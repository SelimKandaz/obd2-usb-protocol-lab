from __future__ import annotations

import json
from pathlib import Path


def test_protocol_knowledge_base_has_safe_boundaries():
    path = Path(__file__).parents[1] / "knowledge" / "protocol_knowledge.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["device"]["vid"] == "0x0483"
    assert data["device"]["pid"] == "0x5265"
    commands = {entry["command"]: entry for entry in data["commands"]}
    assert commands["0x0B"]["confidence"] == "PHYSICAL_VERIFIED"
    assert commands["0x0B"]["safety"] == "READ_ONLY_OPT_IN"
    assert commands["0x06"]["safety"] == "BLOCKED"
    assert "0x02 bulk OUT firmware writes" in data["esp32_reproduction_boundary"]["do_not_implement_from_this_file"]
    candidates = {entry["command"]: entry for entry in data["static_command_candidates"]}
    assert candidates["0x03"]["request_bytes"] == "UNKNOWN"
    assert all(entry["safety"] == "BLOCKED" for entry in candidates.values())
