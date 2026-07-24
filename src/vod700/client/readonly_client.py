"""High-level read-only device operations used by the CLI.

Safe operations (enumeration, descriptor reads, pipe queries) run for real.
Active operations (``listen``, ``identify``, ``version``) are gated and raise a
clear, actionable error until they are backed by verified evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .. import INTERFACE_GUIDS
from . import winusb
from .descriptors import parse_configuration, parse_device_descriptor
from .policy import assert_dispatchable


class NotVerifiedError(RuntimeError):
    """Raised when an active request is requested before it is verified/enabled."""


@dataclass
class DeviceProbe:
    paths: list[str] = field(default_factory=list)
    device_descriptor: dict | None = None
    configuration: dict | None = None
    strings: dict[str, str] = field(default_factory=dict)
    pipes: list[dict] = field(default_factory=list)
    opened_path: str | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "paths": self.paths,
            "opened_path": self.opened_path,
            "device_descriptor": self.device_descriptor,
            "configuration": self.configuration,
            "strings": self.strings,
            "pipes": self.pipes,
            "errors": self.errors,
        }


def list_device_paths(guids: tuple[str, ...] = INTERFACE_GUIDS) -> list[str]:
    return winusb.enumerate_device_paths(guids)


def probe(guids: tuple[str, ...] = INTERFACE_GUIDS) -> DeviceProbe:
    """Enumerate + open the device and read standard descriptors (read-only)."""
    result = DeviceProbe()
    result.paths = winusb.enumerate_device_paths(guids)
    if not result.paths:
        result.errors.append("No matching WinUSB device-interface paths found.")
        return result

    last_err: str | None = None
    for path in result.paths:
        try:
            with winusb.WinUsbDevice(path) as dev:
                result.opened_path = path
                dev_desc = parse_device_descriptor(dev.device_descriptor())
                result.device_descriptor = dev_desc.to_dict()
                try:
                    result.configuration = parse_configuration(dev.configuration_descriptor()).to_dict()
                except Exception as exc:  # noqa: BLE001 - keep going, record it
                    result.errors.append(f"configuration descriptor: {exc}")
                for label, idx in (
                    ("manufacturer", dev_desc.iManufacturer),
                    ("product", dev_desc.iProduct),
                    ("serial", dev_desc.iSerialNumber),
                ):
                    try:
                        if idx:
                            result.strings[label] = dev.string(idx)
                    except Exception as exc:  # noqa: BLE001
                        result.errors.append(f"string[{label}]: {exc}")
                try:
                    result.pipes = [p.to_dict() for p in dev.pipes(0)]
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"pipes: {exc}")
                return result
        except winusb.WinUsbError as exc:
            last_err = str(exc)
            continue
    if last_err:
        result.errors.append(f"Could not open any interface path: {last_err}")
    return result


# --------------------------------------------------------------------------
# Gated active operations. These intentionally refuse until verified.
# --------------------------------------------------------------------------
def listen(*_args: object, **_kwargs: object) -> None:
    raise NotVerifiedError(
        "listen() reads the interrupt IN endpoint (0x81). The read-only client "
        "ships without a WinUsb_ReadPipe binding on purpose. Enable it only after "
        "the device's spontaneous/interrupt behavior is characterized from a "
        "passive capture and reviewed. See docs/READ_ONLY_CLIENT.md."
    )


def identify(*_args: object, **_kwargs: object) -> None:
    assert_dispatchable("identify")  # raises PolicyError: no verified request bytes yet


def version(*_args: object, **_kwargs: object) -> None:
    assert_dispatchable("version")  # raises PolicyError: no verified request bytes yet
