"""Capture ingestion: native pcapng/pcap reading and USBPcap decoding.

Deliberately dependency-free. We parse pcapng/classic-pcap and the USBPcap
pseudo-header in pure Python so a capture can be analyzed on any machine without
tshark, pyshark, or scapy installed. (tshark is still fine to *produce* the
capture — see docs/CAPTURE_HANDSHAKE.md.)
"""
from __future__ import annotations

from .analyze import CaptureAnalysis, analyze, analyze_bytes
from .pcapng import RawPacket, read_packets
from .transactions import (
    FeedbackReadTransaction,
    UrbTransaction,
    correlate_feedback_reads,
    correlate_urb_transactions,
)
from .usbpcap import LINKTYPE_USBPCAP, UsbpcapRecord, decode_usbpcap

__all__ = [
    "RawPacket",
    "read_packets",
    "LINKTYPE_USBPCAP",
    "UsbpcapRecord",
    "decode_usbpcap",
    "CaptureAnalysis",
    "analyze",
    "analyze_bytes",
    "UrbTransaction",
    "FeedbackReadTransaction",
    "correlate_urb_transactions",
    "correlate_feedback_reads",
]
