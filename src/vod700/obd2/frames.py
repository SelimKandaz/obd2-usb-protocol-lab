"""Small, strict CAN frame value objects used by the offline OBD-II codecs."""
from __future__ import annotations

from dataclasses import dataclass


class CanFrameError(ValueError):
    """Raised when a CAN frame is malformed or outside the supported range."""


@dataclass(frozen=True, slots=True)
class CanFrame:
    """One classical CAN data frame.

    The class intentionally models only data frames (0--8 data bytes). Remote
    frames, CAN-FD, and bus timing are transport concerns and are rejected
    rather than silently approximated.
    """

    arbitration_id: int
    data: bytes
    extended: bool = False

    def __post_init__(self) -> None:
        data = bytes(self.data)
        object.__setattr__(self, "data", data)
        maximum = 0x1FFFFFFF if self.extended else 0x7FF
        if not 0 <= self.arbitration_id <= maximum:
            kind = "29-bit" if self.extended else "11-bit"
            raise CanFrameError(f"CAN id must fit {kind} range")
        if len(data) > 8:
            raise CanFrameError("classical CAN data must be at most 8 bytes")

    @property
    def dlc(self) -> int:
        return len(self.data)

    def to_socketcan(self) -> str:
        """Return a canonical ``ID#DATA`` representation for logs/fixtures."""
        identifier = f"{self.arbitration_id:X}"
        return f"{identifier}#{self.data.hex().upper()}"


def parse_can_line(line: str, *, extended: bool | None = None) -> CanFrame:
    """Parse a SocketCAN-style ``ID#DATA`` line.

    Whitespace is ignored. An empty data part is accepted for a zero-length
    frame. The optional ``extended`` argument forces the identifier width;
    otherwise 29-bit IDs select extended mode automatically.
    """

    text = line.strip()
    if "#" not in text:
        raise CanFrameError("CAN line must use ID#DATA form")
    id_text, data_text = text.split("#", 1)
    if not id_text or any(ch not in "0123456789abcdefABCDEF" for ch in id_text):
        raise CanFrameError("CAN identifier must be hexadecimal")
    if len(data_text) % 2 or any(ch not in "0123456789abcdefABCDEF" for ch in data_text):
        raise CanFrameError("CAN data must contain an even number of hex digits")
    arbitration_id = int(id_text, 16)
    use_extended = extended if extended is not None else arbitration_id > 0x7FF
    return CanFrame(arbitration_id, bytes.fromhex(data_text), use_extended)
