"""Offline SAE J1979 response and DTC decoders.

The formulas here are transport-neutral. They decode already captured,
reassembled OBD-II payloads and never send a request to a vehicle or device.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


class Obd2DecodeError(ValueError):
    """Raised when an OBD-II response cannot be decoded safely."""


@dataclass(frozen=True, slots=True)
class PidValue:
    mode: int
    pid: int
    name: str
    value: object
    unit: str
    raw: bytes


@dataclass(frozen=True, slots=True)
class Dtc:
    code: str
    raw: bytes


def _need(data: bytes, count: int, label: str) -> None:
    if len(data) < count:
        raise Obd2DecodeError(f"PID {label} needs {count} data bytes, got {len(data)}")


def decode_supported_pids(data: bytes, *, base_pid: int = 0x00) -> tuple[int, ...]:
    """Decode a four-byte supported-PID bit map into PID numbers."""

    if len(data) != 4:
        raise Obd2DecodeError("supported-PID bitmap must be exactly four bytes")
    out: list[int] = []
    for index, byte in enumerate(data):
        for bit in range(8):
            if byte & (0x80 >> bit):
                out.append(base_pid + index * 8 + bit + 1)
    return tuple(out)


def _pid_value(pid: int, name: str, value: object, unit: str, raw: bytes) -> PidValue:
    return PidValue(0x01, pid, name, value, unit, bytes(raw))


def decode_mode01_response(payload: bytes) -> PidValue:
    """Decode a reassembled ``41 PID DATA`` response for common Mode 01 PIDs."""

    payload = bytes(payload)
    if len(payload) < 2 or payload[0] != 0x41:
        raise Obd2DecodeError("Mode 01 response must begin with 0x41 and a PID")
    pid = payload[1]
    data = payload[2:]
    if pid == 0x00:
        _need(data, 4, "00")
        return _pid_value(pid, "supported_pids", decode_supported_pids(data[:4]), "pid", data[:4])
    if pid == 0x01:
        _need(data, 4, "01")
        return _pid_value(pid, "monitor_status", int.from_bytes(data[:4], "big"), "bitfield", data[:4])
    formulas: dict[int, tuple[str, str, int, Callable[[int], object]]] = {
        0x04: ("calculated_engine_load", "%", 1, lambda a: a * 100.0 / 255.0),
        0x05: ("engine_coolant_temperature", "°C", 1, lambda a: a - 40),
        0x06: ("short_term_fuel_trim_bank_1", "%", 1, lambda a: a * 100.0 / 128.0 - 100.0),
        0x07: ("long_term_fuel_trim_bank_1", "%", 1, lambda a: a * 100.0 / 128.0 - 100.0),
        0x0B: ("intake_manifold_pressure", "kPa", 1, lambda a: a),
        0x0D: ("vehicle_speed", "km/h", 1, lambda a: a),
        0x0F: ("intake_air_temperature", "°C", 1, lambda a: a - 40),
        0x11: ("throttle_position", "%", 1, lambda a: a * 100.0 / 255.0),
        0x1F: ("runtime_since_engine_start", "s", 2, lambda a: a),
        0x2F: ("fuel_level_input", "%", 1, lambda a: a * 100.0 / 255.0),
        0x33: ("barometric_pressure", "kPa", 1, lambda a: a),
        0x46: ("ambient_air_temperature", "°C", 1, lambda a: a - 40),
    }
    if pid == 0x0C:
        _need(data, 2, "0C")
        return _pid_value(pid, "engine_rpm", int.from_bytes(data[:2], "big") / 4.0, "rpm", data[:2])
    if pid == 0x10:
        _need(data, 2, "10")
        return _pid_value(pid, "mass_air_flow", int.from_bytes(data[:2], "big") / 100.0, "g/s", data[:2])
    if pid == 0x42:
        _need(data, 2, "42")
        return _pid_value(pid, "control_module_voltage", int.from_bytes(data[:2], "big") / 1000.0, "V", data[:2])
    if pid not in formulas:
        raise Obd2DecodeError(f"unsupported Mode 01 PID 0x{pid:02X}")
    name, unit, count, formula = formulas[pid]
    _need(data, count, f"{pid:02X}")
    raw = data[:count]
    integer = int.from_bytes(raw, "big")
    return _pid_value(pid, name, formula(integer), unit, raw)


def _decode_dtc(raw: bytes) -> Dtc:
    if len(raw) != 2:
        raise Obd2DecodeError("a DTC must contain exactly two bytes")
    if raw == b"\x00\x00":
        return Dtc("P0000", raw)
    letters = "PCBU"
    code = f"{letters[(raw[0] >> 6) & 0x03]}{(raw[0] >> 4) & 0x03}{raw[0] & 0x0F:X}{raw[1] >> 4:X}{raw[1] & 0x0F:X}"
    return Dtc(code, raw)


def decode_dtc_response(payload: bytes) -> tuple[Dtc, ...]:
    """Decode a Mode 03 ``43`` response, omitting the all-zero terminator."""

    payload = bytes(payload)
    if not payload or payload[0] != 0x43:
        raise Obd2DecodeError("DTC response must begin with 0x43")
    if len(payload[1:]) % 2:
        raise Obd2DecodeError("DTC response data must contain complete pairs")
    return tuple(dtc for raw in (payload[i : i + 2] for i in range(1, len(payload), 2)) if (dtc := _decode_dtc(raw)).code != "P0000")


def decode_vin_response(payload: bytes) -> str:
    """Decode a reassembled Mode 09 PID 02 VIN response as ASCII."""

    payload = bytes(payload)
    if len(payload) < 2 or payload[:2] != b"I\x02":
        raise Obd2DecodeError("VIN response must begin with service 0x49 and PID 0x02")
    try:
        text = payload[2:].decode("ascii")
    except UnicodeDecodeError as exc:
        raise Obd2DecodeError("VIN response is not ASCII") from exc
    text = text.strip("\x00 \r\n")
    if not text:
        raise Obd2DecodeError("VIN response is empty")
    return text
