"""Minimal, read-only WinUSB access via ctypes.

Exposes exactly the calls needed to *observe* the device:
  * enumerate device-interface paths (SetupAPI)
  * open + WinUsb_Initialize
  * WinUsb_GetDescriptor (device / configuration / string)  -- standard reads
  * WinUsb_QueryInterfaceSettings / WinUsb_QueryPipe        -- endpoint map

There is deliberately **no** WinUsb_WritePipe and **no** WinUsb_ReadPipe binding
in this module. Sending or soliciting vendor traffic is a separate, gated step
(see :mod:`vod700.client.policy`). Importing this module never fails: if WinUSB
is unavailable, ``WINUSB_AVAILABLE`` is ``False`` and calls raise cleanly.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass

from .descriptors import parse_string_descriptor

WINUSB_AVAILABLE = False
_IMPORT_ERROR = ""

try:  # pragma: no cover - platform dependent
    from ctypes import POINTER, byref, c_ubyte, c_ushort, c_void_p, create_string_buffer, wintypes

    _setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _winusb = ctypes.WinDLL("winusb", use_last_error=True)
    WINUSB_AVAILABLE = True
except Exception as exc:  # pragma: no cover
    _IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


class WinUsbError(RuntimeError):
    pass


# Descriptor type constants
DT_DEVICE, DT_CONFIG, DT_STRING = 0x01, 0x02, 0x03
_DEFAULT_LANGID = 0x0409


if WINUSB_AVAILABLE:  # pragma: no cover - requires Windows + device
    _DIGCF_PRESENT = 0x02
    _DIGCF_DEVICEINTERFACE = 0x10
    _GENERIC_READ = 0x80000000
    _GENERIC_WRITE = 0x40000000
    _FILE_SHARE_RW = 0x03
    _OPEN_EXISTING = 3
    _FILE_FLAG_OVERLAPPED = 0x40000000
    _INVALID_HANDLE = ctypes.c_void_p(-1).value

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

        @classmethod
        def from_string(cls, s: str) -> GUID:
            s = s.strip("{}")
            parts = s.split("-")
            g = cls()
            g.Data1 = int(parts[0], 16)
            g.Data2 = int(parts[1], 16)
            g.Data3 = int(parts[2], 16)
            tail = bytes.fromhex(parts[3] + parts[4])
            for i in range(8):
                g.Data4[i] = tail[i]
            return g

    class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("InterfaceClassGuid", GUID),
            ("Flags", wintypes.DWORD),
            ("Reserved", ctypes.c_size_t),
        ]

    class USB_INTERFACE_DESCRIPTOR(ctypes.Structure):
        _fields_ = [
            ("bLength", c_ubyte),
            ("bDescriptorType", c_ubyte),
            ("bInterfaceNumber", c_ubyte),
            ("bAlternateSetting", c_ubyte),
            ("bNumEndpoints", c_ubyte),
            ("bInterfaceClass", c_ubyte),
            ("bInterfaceSubClass", c_ubyte),
            ("bInterfaceProtocol", c_ubyte),
            ("iInterface", c_ubyte),
        ]

    class WINUSB_PIPE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PipeType", ctypes.c_int),
            ("PipeId", c_ubyte),
            ("MaximumPacketSize", c_ushort),
            ("Interval", c_ubyte),
        ]

    _setupapi.SetupDiGetClassDevsW.argtypes = [
        POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD
    ]
    _setupapi.SetupDiGetClassDevsW.restype = wintypes.HANDLE
    _setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
        wintypes.HANDLE, c_void_p, POINTER(GUID), wintypes.DWORD, POINTER(SP_DEVICE_INTERFACE_DATA)
    ]
    _setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
    _setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
        wintypes.HANDLE, POINTER(SP_DEVICE_INTERFACE_DATA), c_void_p,
        wintypes.DWORD, POINTER(wintypes.DWORD), c_void_p
    ]
    _setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL
    _setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]
    _setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

    _kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
    ]
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    _winusb.WinUsb_Initialize.argtypes = [wintypes.HANDLE, POINTER(c_void_p)]
    _winusb.WinUsb_Initialize.restype = wintypes.BOOL
    _winusb.WinUsb_Free.argtypes = [c_void_p]
    _winusb.WinUsb_Free.restype = wintypes.BOOL
    _winusb.WinUsb_GetDescriptor.argtypes = [
        c_void_p, c_ubyte, c_ubyte, c_ushort, c_void_p, wintypes.ULONG, POINTER(wintypes.ULONG)
    ]
    _winusb.WinUsb_GetDescriptor.restype = wintypes.BOOL
    _winusb.WinUsb_QueryInterfaceSettings.argtypes = [
        c_void_p, c_ubyte, POINTER(USB_INTERFACE_DESCRIPTOR)
    ]
    _winusb.WinUsb_QueryInterfaceSettings.restype = wintypes.BOOL
    _winusb.WinUsb_QueryPipe.argtypes = [
        c_void_p, c_ubyte, c_ubyte, POINTER(WINUSB_PIPE_INFORMATION)
    ]
    _winusb.WinUsb_QueryPipe.restype = wintypes.BOOL

    _PIPE_TYPES = {0: "CONTROL", 1: "ISOCHRONOUS", 2: "BULK", 3: "INTERRUPT"}


def _require() -> None:
    if not WINUSB_AVAILABLE:
        raise WinUsbError(f"WinUSB is not available on this platform ({_IMPORT_ERROR})")


def enumerate_device_paths(guids: tuple[str, ...]) -> list[str]:
    """Return device-interface paths for the given interface class GUIDs."""
    _require()
    paths: list[str] = []
    for guid_str in guids:  # pragma: no cover - requires device
        guid = GUID.from_string(guid_str)
        hdev = _setupapi.SetupDiGetClassDevsW(
            byref(guid), None, None, _DIGCF_PRESENT | _DIGCF_DEVICEINTERFACE
        )
        if hdev == _INVALID_HANDLE or hdev is None:
            continue
        try:
            index = 0
            while True:
                iface = SP_DEVICE_INTERFACE_DATA()
                iface.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)
                if not _setupapi.SetupDiEnumDeviceInterfaces(
                    hdev, None, byref(guid), index, byref(iface)
                ):
                    break
                index += 1
                required = wintypes.DWORD(0)
                _setupapi.SetupDiGetDeviceInterfaceDetailW(
                    hdev, byref(iface), None, 0, byref(required), None
                )
                if required.value == 0:
                    continue
                buf = create_string_buffer(required.value)
                cb = 8 if ctypes.sizeof(c_void_p) == 8 else 6
                ctypes.cast(buf, POINTER(wintypes.DWORD))[0] = cb
                if _setupapi.SetupDiGetDeviceInterfaceDetailW(
                    hdev, byref(iface), buf, required, byref(required), None
                ):
                    path = ctypes.wstring_at(ctypes.addressof(buf) + ctypes.sizeof(wintypes.DWORD))
                    if path and path not in paths:
                        paths.append(path)
        finally:
            _setupapi.SetupDiDestroyDeviceInfoList(hdev)
    return paths


@dataclass
class PipeInfo:
    pipe_id: int
    pipe_type: str
    max_packet_size: int
    interval: int

    def to_dict(self) -> dict[str, object]:
        return {
            "pipe_id": f"0x{self.pipe_id:02X}",
            "direction": "IN" if self.pipe_id & 0x80 else "OUT",
            "pipe_type": self.pipe_type,
            "max_packet_size": self.max_packet_size,
            "interval": self.interval,
        }


class WinUsbDevice:
    """Read-only WinUSB handle. Use as a context manager."""

    def __init__(self, path: str) -> None:
        _require()
        self.path = path
        self._file: int | None = None
        self._handle = c_void_p()

    def __enter__(self) -> WinUsbDevice:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def open(self) -> None:  # pragma: no cover - requires device
        self._file = _kernel32.CreateFileW(
            self.path,
            _GENERIC_READ | _GENERIC_WRITE,
            _FILE_SHARE_RW,
            None,
            _OPEN_EXISTING,
            _FILE_FLAG_OVERLAPPED,
            None,
        )
        if self._file == _INVALID_HANDLE or not self._file:
            raise WinUsbError(f"CreateFileW failed: {ctypes.WinError(ctypes.get_last_error())}")
        if not _winusb.WinUsb_Initialize(self._file, byref(self._handle)):
            err = ctypes.WinError(ctypes.get_last_error())
            _kernel32.CloseHandle(self._file)
            self._file = None
            raise WinUsbError(f"WinUsb_Initialize failed: {err}")

    def close(self) -> None:  # pragma: no cover - requires device
        if self._handle:
            _winusb.WinUsb_Free(self._handle)
            self._handle = c_void_p()
        if self._file:
            _kernel32.CloseHandle(self._file)
            self._file = None

    def get_descriptor(self, dtype: int, index: int = 0, langid: int = 0, length: int = 256) -> bytes:  # pragma: no cover
        buf = create_string_buffer(length)
        transferred = wintypes.ULONG(0)
        ok = _winusb.WinUsb_GetDescriptor(
            self._handle, dtype, index, langid, buf, length, byref(transferred)
        )
        if not ok:
            raise WinUsbError(
                f"WinUsb_GetDescriptor(type={dtype}, index={index}) failed: "
                f"{ctypes.WinError(ctypes.get_last_error())}"
            )
        return buf.raw[: transferred.value]

    def device_descriptor(self) -> bytes:  # pragma: no cover
        return self.get_descriptor(DT_DEVICE, 0, 0, 18)

    def configuration_descriptor(self) -> bytes:  # pragma: no cover
        head = self.get_descriptor(DT_CONFIG, 0, 0, 9)
        total = int.from_bytes(head[2:4], "little") if len(head) >= 4 else 9
        return self.get_descriptor(DT_CONFIG, 0, 0, max(total, 9))

    def string(self, index: int, langid: int = _DEFAULT_LANGID) -> str:  # pragma: no cover
        if index == 0:
            return ""
        raw = self.get_descriptor(DT_STRING, index, langid, 255)
        return parse_string_descriptor(raw)

    def pipes(self, alt: int = 0) -> list[PipeInfo]:  # pragma: no cover
        iface = USB_INTERFACE_DESCRIPTOR()
        if not _winusb.WinUsb_QueryInterfaceSettings(self._handle, alt, byref(iface)):
            raise WinUsbError("WinUsb_QueryInterfaceSettings failed")
        out: list[PipeInfo] = []
        for i in range(iface.bNumEndpoints):
            info = WINUSB_PIPE_INFORMATION()
            if _winusb.WinUsb_QueryPipe(self._handle, alt, i, byref(info)):
                out.append(
                    PipeInfo(
                        pipe_id=info.PipeId,
                        pipe_type=_PIPE_TYPES.get(info.PipeType, "UNKNOWN"),
                        max_packet_size=info.MaximumPacketSize,
                        interval=info.Interval,
                    )
                )
        return out
