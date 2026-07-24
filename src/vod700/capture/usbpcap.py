"""Decode the USBPcap pseudo-header (LINKTYPE_USBPCAP = 249).

Layout of ``USBPCAP_BUFFER_PACKET_HEADER`` (little-endian, packed). We locate the
payload using ``headerLen`` rather than a hard-coded size so control transfers
(which carry an extra stage byte) decode correctly.

    off  size  field
      0   u16  headerLen         total length of this pseudo-header
      2   u64  irpId
     10   u32  status            USBD_STATUS
     14   u16  function          URB function
     16   u8   info              bit0 = PDO->FDO (data came FROM the device)
     17   u16  bus
     19   u16  device            USB device address
     21   u8   endpoint          bit7 = direction (1 = IN) for non-control
     22   u8   transfer          0=iso 1=int 2=ctrl 3=bulk
     23   u32  dataLength        payload byte count
    (control adds a 1-byte stage field before the payload; covered by headerLen)
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from ..protocol.models import Direction, TransferType

LINKTYPE_USBPCAP = 249

# USBPcap transfer-type codes
_ISO, _INT, _CTRL, _BULK = 0, 1, 2, 3
_TRANSFER_MAP = {
    _ISO: TransferType.ISOCHRONOUS,
    _INT: TransferType.INTERRUPT,
    _CTRL: TransferType.CONTROL,
    _BULK: TransferType.BULK,
}

_INFO_PDO_TO_FDO = 0x01  # data flows device -> host (an IN completion)
_BASE_HEADER = 27  # minimum pseudo-header size (non-control)


@dataclass
class UsbpcapRecord:
    header_len: int
    irp_id: int
    status: int
    function: int
    info: int
    bus: int
    device: int
    endpoint: int
    transfer_code: int
    data_length: int
    payload: bytes

    @property
    def transfer_type(self) -> TransferType:
        return _TRANSFER_MAP.get(self.transfer_code, TransferType.CONTROL)

    @property
    def direction(self) -> Direction:
        # For non-control endpoints, the endpoint's high bit is authoritative.
        # For control transfers, fall back to the info bit (stage-dependent).
        if self.transfer_code == _CTRL:
            return Direction.IN if (self.info & _INFO_PDO_TO_FDO) else Direction.OUT
        return Direction.IN if (self.endpoint & 0x80) else Direction.OUT


def decode_usbpcap(raw: bytes) -> UsbpcapRecord:
    if len(raw) < _BASE_HEADER:
        raise ValueError(f"USBPcap record too short: {len(raw)} bytes")
    header_len = struct.unpack_from("<H", raw, 0)[0]
    if header_len < _BASE_HEADER or header_len > len(raw):
        raise ValueError(f"implausible USBPcap headerLen={header_len} (buffer {len(raw)})")
    irp_id = struct.unpack_from("<Q", raw, 2)[0]
    status = struct.unpack_from("<I", raw, 10)[0]
    function = struct.unpack_from("<H", raw, 14)[0]
    info = raw[16]
    bus = struct.unpack_from("<H", raw, 17)[0]
    device = struct.unpack_from("<H", raw, 19)[0]
    endpoint = raw[21]
    transfer_code = raw[22]
    data_length = struct.unpack_from("<I", raw, 23)[0]
    payload = raw[header_len : header_len + data_length]
    return UsbpcapRecord(
        header_len=header_len,
        irp_id=irp_id,
        status=status,
        function=function,
        info=info,
        bus=bus,
        device=device,
        endpoint=endpoint,
        transfer_code=transfer_code,
        data_length=data_length,
        payload=payload,
    )
