"""Pure-Python parsing of standard USB descriptors (read-only, testable).

These functions operate on raw descriptor bytes obtained from the driver via
standard GET_DESCRIPTOR requests. No device interaction happens here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

DT_DEVICE = 0x01
DT_CONFIG = 0x02
DT_STRING = 0x03
DT_INTERFACE = 0x04
DT_ENDPOINT = 0x05

_TRANSFER_TYPES = {0: "CONTROL", 1: "ISOCHRONOUS", 2: "BULK", 3: "INTERRUPT"}


def bcd(value: int) -> str:
    return f"{(value >> 8) & 0xFF:x}.{value & 0xFF:02x}"


@dataclass
class DeviceDescriptor:
    bcdUSB: int
    bDeviceClass: int
    bDeviceSubClass: int
    bDeviceProtocol: int
    bMaxPacketSize0: int
    idVendor: int
    idProduct: int
    bcdDevice: int
    iManufacturer: int
    iProduct: int
    iSerialNumber: int
    bNumConfigurations: int
    raw: bytes = b""

    def to_dict(self) -> dict[str, object]:
        return {
            "bcdUSB": bcd(self.bcdUSB),
            "bDeviceClass": f"0x{self.bDeviceClass:02X}",
            "bDeviceSubClass": f"0x{self.bDeviceSubClass:02X}",
            "bDeviceProtocol": f"0x{self.bDeviceProtocol:02X}",
            "bMaxPacketSize0": self.bMaxPacketSize0,
            "idVendor": f"0x{self.idVendor:04X}",
            "idProduct": f"0x{self.idProduct:04X}",
            "bcdDevice": bcd(self.bcdDevice),
            "iManufacturer": self.iManufacturer,
            "iProduct": self.iProduct,
            "iSerialNumber": self.iSerialNumber,
            "bNumConfigurations": self.bNumConfigurations,
        }


@dataclass
class EndpointDescriptor:
    bEndpointAddress: int
    bmAttributes: int
    wMaxPacketSize: int
    bInterval: int

    @property
    def direction(self) -> str:
        return "IN" if self.bEndpointAddress & 0x80 else "OUT"

    @property
    def transfer_type(self) -> str:
        return _TRANSFER_TYPES.get(self.bmAttributes & 0x03, "UNKNOWN")

    def to_dict(self) -> dict[str, object]:
        return {
            "bEndpointAddress": f"0x{self.bEndpointAddress:02X}",
            "direction": self.direction,
            "transfer_type": self.transfer_type,
            "wMaxPacketSize": self.wMaxPacketSize,
            "bInterval": self.bInterval,
        }


@dataclass
class InterfaceDescriptor:
    bInterfaceNumber: int
    bAlternateSetting: int
    bNumEndpoints: int
    bInterfaceClass: int
    bInterfaceSubClass: int
    bInterfaceProtocol: int
    endpoints: list[EndpointDescriptor] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "bInterfaceNumber": self.bInterfaceNumber,
            "bAlternateSetting": self.bAlternateSetting,
            "bNumEndpoints": self.bNumEndpoints,
            "bInterfaceClass": f"0x{self.bInterfaceClass:02X}",
            "bInterfaceSubClass": f"0x{self.bInterfaceSubClass:02X}",
            "bInterfaceProtocol": f"0x{self.bInterfaceProtocol:02X}",
            "endpoints": [e.to_dict() for e in self.endpoints],
        }


@dataclass
class ConfigurationDescriptor:
    wTotalLength: int
    bNumInterfaces: int
    bConfigurationValue: int
    bmAttributes: int
    bMaxPower: int
    interfaces: list[InterfaceDescriptor] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "wTotalLength": self.wTotalLength,
            "bNumInterfaces": self.bNumInterfaces,
            "bConfigurationValue": self.bConfigurationValue,
            "bmAttributes": f"0x{self.bmAttributes:02X}",
            "bMaxPower_mA": self.bMaxPower * 2,
            "interfaces": [i.to_dict() for i in self.interfaces],
        }


def parse_device_descriptor(data: bytes) -> DeviceDescriptor:
    if len(data) < 18:
        raise ValueError(f"device descriptor too short: {len(data)} bytes")
    return DeviceDescriptor(
        bcdUSB=int.from_bytes(data[2:4], "little"),
        bDeviceClass=data[4],
        bDeviceSubClass=data[5],
        bDeviceProtocol=data[6],
        bMaxPacketSize0=data[7],
        idVendor=int.from_bytes(data[8:10], "little"),
        idProduct=int.from_bytes(data[10:12], "little"),
        bcdDevice=int.from_bytes(data[12:14], "little"),
        iManufacturer=data[14],
        iProduct=data[15],
        iSerialNumber=data[16],
        bNumConfigurations=data[17],
        raw=bytes(data[:18]),
    )


def parse_configuration(data: bytes) -> ConfigurationDescriptor:
    if len(data) < 9 or data[1] != DT_CONFIG:
        raise ValueError("not a configuration descriptor")
    config = ConfigurationDescriptor(
        wTotalLength=int.from_bytes(data[2:4], "little"),
        bNumInterfaces=data[4],
        bConfigurationValue=data[5],
        bmAttributes=data[7],
        bMaxPower=data[8],
    )
    offset = data[0]  # bLength of the config header
    current: InterfaceDescriptor | None = None
    while offset + 2 <= len(data):
        blen = data[offset]
        if blen == 0:
            break
        btype = data[offset + 1]
        chunk = data[offset : offset + blen]
        if btype == DT_INTERFACE and len(chunk) >= 9:
            current = InterfaceDescriptor(
                bInterfaceNumber=chunk[2],
                bAlternateSetting=chunk[3],
                bNumEndpoints=chunk[4],
                bInterfaceClass=chunk[5],
                bInterfaceSubClass=chunk[6],
                bInterfaceProtocol=chunk[7],
            )
            config.interfaces.append(current)
        elif btype == DT_ENDPOINT and len(chunk) >= 7 and current is not None:
            current.endpoints.append(
                EndpointDescriptor(
                    bEndpointAddress=chunk[2],
                    bmAttributes=chunk[3],
                    wMaxPacketSize=int.from_bytes(chunk[4:6], "little"),
                    bInterval=chunk[6],
                )
            )
        offset += blen
    return config


def parse_string_descriptor(data: bytes) -> str:
    if len(data) < 2 or data[1] != DT_STRING:
        return ""
    return data[2 : data[0]].decode("utf-16-le", errors="replace")
