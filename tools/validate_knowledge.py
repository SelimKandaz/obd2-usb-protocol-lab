"""Validate the public, machine-readable VOD700 knowledge base.

The validator deliberately checks structure and evidence taxonomy only.  It
does not look inside ``private_samples/`` and does not attempt to validate a
claim against a proprietary capture or updater binary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
EVIDENCE_CLASSIFICATIONS = {
    "PHYSICALLY_VERIFIED",
    "CAPTURE_VERIFIED",
    "DYNAMIC_ANALYSIS_VERIFIED",
    "STATIC_ANALYSIS_SUPPORTED",
    "FIRMWARE_CODE_SUPPORTED",
    "INTERNET_CORRELATED",
    "REPLAY_VERIFIED",
    "INFERRED",
    "UNKNOWN",
}
CONFIDENCES = {"VERIFIED", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}


def _load(name: str) -> dict[str, Any]:
    path = KNOWLEDGE / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name}: cannot parse JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: top-level value must be an object")
    return data


def _walk(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"classification", "evidence_classification"} and child not in EVIDENCE_CLASSIFICATIONS:
                errors.append(f"{child_path}: unknown evidence classification {child!r}")
            if key == "confidence" and child not in CONFIDENCES:
                errors.append(f"{child_path}: unknown confidence {child!r}")
            _walk(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]", errors)


def validate() -> list[str]:
    """Return validation errors; an empty list means the public KB is coherent."""

    errors: list[str] = []
    protocol = _load("protocol_knowledge.json")
    state_machine = _load("updater_state_machine.json")
    memory_map = _load("memory_map.json")
    external_sources = _load("external_sources.json")
    for name, data in (
        ("protocol_knowledge.json", protocol),
        ("updater_state_machine.json", state_machine),
        ("memory_map.json", memory_map),
        ("external_sources.json", external_sources),
    ):
        _walk(data, name, errors)

    if protocol.get("schema_version") != 2:
        errors.append("protocol_knowledge.json: expected schema_version 2")
    commands = protocol.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("protocol_knowledge.json.commands: expected non-empty list")
    else:
        seen_commands: set[str] = set()
        for index, command in enumerate(commands):
            if not isinstance(command, dict):
                errors.append(f"protocol_knowledge.json.commands[{index}]: expected object")
                continue
            value = command.get("command")
            if not isinstance(value, str) or value in seen_commands:
                errors.append(f"protocol_knowledge.json.commands[{index}]: duplicate/missing command")
            else:
                seen_commands.add(value)
            if not command.get("evidence"):
                errors.append(f"protocol_knowledge.json.commands[{index}]: evidence is required")

    states = state_machine.get("states")
    if not isinstance(states, list) or not states:
        errors.append("updater_state_machine.json.states: expected non-empty list")
        state_ids: set[str] = set()
    else:
        state_ids = {item.get("id") for item in states if isinstance(item, dict) and isinstance(item.get("id"), str)}
        if len(state_ids) != len(states):
            errors.append("updater_state_machine.json.states: IDs must be unique strings")
    for index, edge in enumerate(state_machine.get("transitions", [])):
        if not isinstance(edge, dict) or edge.get("from") not in state_ids or edge.get("to") not in state_ids:
            errors.append(f"updater_state_machine.json.transitions[{index}]: endpoints must reference known states")

    regions = memory_map.get("regions")
    if not isinstance(regions, list) or not regions:
        errors.append("memory_map.json.regions: expected non-empty list")
    for index, source in enumerate(external_sources.get("sources", [])):
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith("https://"):
            errors.append(f"external_sources.json.sources[{index}]: HTTPS URL is required")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"KNOWLEDGE_ERROR: {error}", file=sys.stderr)
        return 1
    print("KNOWLEDGE_OK — protocol, state-machine, memory-map, and source records are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
