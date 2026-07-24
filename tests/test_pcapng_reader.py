from __future__ import annotations

from vod700.capture.analyze import analyze_bytes
from vod700.capture.pcapng import iter_packets
from vod700.capture.usbpcap import LINKTYPE_USBPCAP
from vod700.mock.fixtures import build_usbpcap_pcapng, make_usbpcap_record
from vod700.protocol.models import Direction, TransferType


def _blob() -> bytes:
    r1 = make_usbpcap_record(endpoint=0x01, payload=b"\xaa\x01\x00", transfer_type=TransferType.INTERRUPT)
    r2 = make_usbpcap_record(endpoint=0x81, payload=b"\x55\x01", transfer_type=TransferType.INTERRUPT)
    return build_usbpcap_pcapng([(1_000_000, r1), (2_000_000, r2)])


def test_pcapng_roundtrip_linktype_count_and_timestamp():
    pkts = list(iter_packets(_blob()))
    assert len(pkts) == 2
    assert all(p.linktype == LINKTYPE_USBPCAP for p in pkts)
    assert abs(pkts[0].timestamp - 0.001) < 1e-9  # 1_000_000 ns


def test_analyze_bytes_groups_devices_directions():
    analysis = analyze_bytes(_blob(), capture_id="synthetic")
    assert len(analysis.transfers) == 2
    assert analysis.devices[0].address == 9
    dirs = {t.endpoint: t.direction for t in analysis.transfers}
    assert dirs[0x01] is Direction.OUT
    assert dirs[0x81] is Direction.IN
    labels = " ".join(g.label for g in analysis.groups)
    assert "0x01" in labels and "0x81" in labels


def test_non_usbpcap_capture_warns():
    # A classic pcap with an Ethernet linktype (1) yields no USB transfers.
    import struct

    global_header = struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    rec = struct.pack("<IIII", 0, 0, 4, 4) + b"\xde\xad\xbe\xef"
    analysis = analyze_bytes(global_header + rec, capture_id="eth")
    assert analysis.transfers == []
    assert any("USBPcap" in w for w in analysis.warnings)
