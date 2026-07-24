from __future__ import annotations

from vod700.capture import exporters
from vod700.capture.analyze import analyze_bytes
from vod700.mock.fixtures import build_usbpcap_pcapng, make_usbpcap_record


def _analysis():
    r1 = make_usbpcap_record(endpoint=0x01, payload=b"\xaa\x01\x00")
    r2 = make_usbpcap_record(endpoint=0x81, payload=b"\x55\x01")
    blob = build_usbpcap_pcapng([(0, r1), (1_000_000, r2)])
    return analyze_bytes(blob, capture_id="t")


def test_write_all_creates_three_files(tmp_path):
    paths = exporters.write_all(_analysis(), tmp_path, prefix="h")
    assert paths["jsonl"].exists()
    assert paths["csv"].exists()
    assert paths["markdown"].exists()


def test_jsonl_has_one_line_per_transfer(tmp_path):
    p = exporters.to_jsonl(_analysis(), tmp_path / "x.jsonl")
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert '"payload_hex":"aa0100"' in lines[0]


def test_markdown_and_csv_headers(tmp_path):
    md = exporters.to_markdown(_analysis(), tmp_path / "x.md").read_text(encoding="utf-8")
    assert "Capture timeline" in md and "Endpoint groups" in md
    csv = exporters.to_csv(_analysis(), tmp_path / "x.csv").read_text(encoding="utf-8")
    assert "payload_hex" in csv.splitlines()[0]
