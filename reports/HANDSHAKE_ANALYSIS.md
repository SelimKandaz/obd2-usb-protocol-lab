# Handshake Analysis (Phases 6–7)

**Status: BLOCKED — no USB capture exists yet** (USBPcap not installed).

This report is generated/updated from capture data. Once
`private_samples/captures/handshake.pcapng` exists:

```bash
vod700 capture analyze private_samples\captures\handshake.pcapng --out reports --prefix handshake
vod700 capture checksums private_samples\captures\handshake.pcapng --endpoint 0x01
```

That produces `reports/handshake_timeline.md`, `handshake_packets.jsonl`, and
`handshake_packets.csv`, which this analysis then interprets.

## To fill in from evidence
- Initialization sequence (first OUT/IN on the interrupt channel).
- Fixed header / magic bytes (`framing.common_prefix` across many frames).
- Command byte and any sub-command byte.
- Sequence-number field (`framing.incrementing_offsets`).
- Payload-length field.
- Status / response code.
- Checksum algorithm — **only** if it reproduces across multiple captures
  (`checksums.analyze_trailing`, `min_frames >= 2`).
- Heartbeat cadence (from `repeated_payloads` + timestamps).
- Bulk fragmentation behavior (short-packet termination?).
- ACK/NACK and error responses.

## Confidence ledger (to be completed)
| Claim | Evidence (capture#frame) | Confidence |
|-------|--------------------------|------------|
| _tbd_ | _tbd_                    | UNKNOWN    |

Every parsed field must preserve raw bytes; unexplained bytes remain visible.
