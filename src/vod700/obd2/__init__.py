"""Transport-neutral OBD-II/ISO-TP codecs.

This package deliberately stops at parsing and constructing CAN/ISO-TP frames
in memory. It does not open a USB pipe, connect to a vehicle, or transmit an
ECU request. The VOD700 USB vendor protocol and an OBD-II transport are
separate layers; no evidence currently justifies coupling them.
"""

from .frames import CanFrame, parse_can_line
from .isotp import (
    FlowControl,
    IsoTpError,
    IsoTpReassembler,
    encode_isotp,
    encode_single_frame,
)
from .pids import (
    Dtc,
    PidValue,
    decode_dtc_response,
    decode_mode01_response,
    decode_supported_pids,
    decode_vin_response,
)

__all__ = [
    "CanFrame",
    "Dtc",
    "FlowControl",
    "IsoTpError",
    "IsoTpReassembler",
    "PidValue",
    "decode_dtc_response",
    "decode_mode01_response",
    "decode_supported_pids",
    "decode_vin_response",
    "encode_isotp",
    "encode_single_frame",
    "parse_can_line",
]
