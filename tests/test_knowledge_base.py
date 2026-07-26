from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_protocol_knowledge_base_has_safe_boundaries():
    path = Path(__file__).parents[1] / "knowledge" / "protocol_knowledge.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["device"]["vid"] == "0x0483"
    assert data["device"]["pid"] == "0x5265"
    commands = {entry["command"]: entry for entry in data["commands"]}
    assert commands["0x0B"]["confidence"] == "VERIFIED"
    assert commands["0x0B"]["safety"] == "READ_ONLY_OPT_IN"
    assert commands["0x06"]["safety"] == "BLOCKED_PENDING_EXPLICIT_LIVE_APPROVAL"
    assert "0x02 bulk OUT firmware writes" in data["esp32_reproduction_boundary"]["do_not_implement_from_this_file"]
    assert commands["0x03"]["safety"] == "DANGEROUS_BLOCKED"
    assert commands["0x01"]["safety"] == "DANGEROUS_BLOCKED"
    routes = {entry["control"]: entry for entry in data["updater_ui_routes"]}
    assert routes["Update"]["worker_callback"] == "0x00410310"
    assert routes["Update"]["safety"] == "DANGEROUS_BLOCKED"
    assert routes["Feedback"]["worker_callback"] == "0x0040DB30"
    blocked = {entry["id"]: entry for entry in data["unknown_or_blocked"]}
    assert blocked["update_stage_0x04"]["request_hex_static"] == "55aa041d360000000000000000000056"
    assert blocked["final_update_command_0x02"]["safety"] == "DANGEROUS_BLOCKED"


def test_machine_readable_knowledge_base_validator():
    root = Path(__file__).parents[1]
    completed = subprocess.run(
        [sys.executable, str(root / "tools" / "validate_knowledge.py")],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "KNOWLEDGE_OK" in completed.stdout
