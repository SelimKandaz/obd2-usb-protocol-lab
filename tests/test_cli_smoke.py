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
