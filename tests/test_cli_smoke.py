from __future__ import annotations

from vod700.cli import main
from vod700.mock.fixtures import build_usbpcap_pcapng, make_usbpcap_record


def test_policy_command_runs(capsys):
    assert main(["policy"]) == 0
    assert "gated" in capsys.readouterr().out.lower()


def test_gated_identify_is_refused(capsys):
    assert main(["identify"]) == 3
    assert "REFUSED" in capsys.readouterr().err


def test_storage_query_requires_explicit_live_approval(capsys):
    assert main(["storage-query"]) == 3
    captured = capsys.readouterr()
    assert "--approve-live" in captured.err


def test_capture_summary(tmp_path, capsys):
    blob = build_usbpcap_pcapng(
        [
            (0, make_usbpcap_record(endpoint=0x01, payload=b"\xaa\x01\x00")),
            (1_000_000, make_usbpcap_record(endpoint=0x81, payload=b"\x55\x01")),
        ]
    )
    path = tmp_path / "cap.pcapng"
    path.write_bytes(blob)
    assert main(["capture", "summary", str(path)]) == 0
    assert "transfers" in capsys.readouterr().out


def test_capture_analyze_writes_reports(tmp_path):
    blob = build_usbpcap_pcapng([(0, make_usbpcap_record(endpoint=0x01, payload=b"\xaa\x01\x00"))])
    path = tmp_path / "cap.pcapng"
    path.write_bytes(blob)
    out = tmp_path / "out"
    assert main(["capture", "analyze", str(path), "--out", str(out), "--prefix", "h"]) == 0
    assert (out / "h_packets.jsonl").exists()
    assert (out / "h_timeline.md").exists()


def test_capture_transactions_is_offline(tmp_path, capsys):
    blob = build_usbpcap_pcapng([(0, make_usbpcap_record(endpoint=0x01, payload=b"\xAA"))])
    path = tmp_path / "cap.pcapng"
    path.write_bytes(blob)
    assert main(["capture", "transactions", str(path)]) == 0
    assert "submit/completion" in capsys.readouterr().out


def test_obd2_decode_is_offline(capsys):
    assert main(["obd2", "decode", "7E8#04410C1AF8000000"]) == 0
    output = capsys.readouterr().out
    assert "engine_rpm" in output
    assert "1726.0" in output


def test_firmware_inspect_is_offline(tmp_path, capsys):
    path = tmp_path / "opaque.bin"
    path.write_bytes(b"\x00" * 32)
    assert main(["firmware", "inspect", str(path)]) == 0
    assert '"size": 32' in capsys.readouterr().out


def test_memory_feedback_plan_never_opens_usb(capsys):
    assert main(["memory", "feedback-plan"]) == 0
    output = capsys.readouterr().out
    assert '"dispatch_enabled": false' in output
    assert "0x01FB0000" in output


def test_memory_review_print_plan_never_opens_usb(capsys):
    assert main(["memory", "review-print-plan"]) == 0
    output = capsys.readouterr().out
    assert "AUTOPHIX" in output
    assert '"dispatch_enabled": false' in output
