# VOD700 Protocol Lab — Milestone 6

Date: 2026-07-25

## Result

The first genuine vendor-specific USB transaction from the official updater is
now captured and reconstructed. The canonical private fixture is
`private_samples/captures/updater_first_vendor.pcapng`.

## Capture

- Interface: `\\.\USBPcap1`
- Bus/address: `1/6`
- Raw PCAP: 9,290 bytes, SHA-256
  `29212D848F692B685E2C9CA24ADD6CCDE3D8FA99762558550A7D5B1EBFF8CE77`
- Canonical PCAPNG: 9,748 bytes, SHA-256
  `5475B9B6C40413BB97C791C15CF286503626AEC64D90BD831CA3B1D278A8B731`
- Records: 22 live URBs, 0 synthetic
- Endpoint counts: `0x01` 8, `0x81` 6, `0x82` 8, `0x02` 0

## Reconstructed protocol

The first request is a 16-byte `0x0B` interrupt OUT frame:

```text
55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
```

It receives a 16-byte `0x8B` interrupt IN response:

```text
AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C
```

The response value field is `0x02000000` little-endian. The updater then
sends `0x06` requests for `0x01FB0000`, `0x01FB1000`, and `0x01FB2000`, each
with field byte 8 equal to `0x10`, and reads the observed bulk-IN patterns.

All observed 16-byte frames use request magic `55 AA`, response magic `AA 55`,
and trailing SUM8. No bulk OUT or firmware-write transfer was captured.

## Implementation

`vod700.protocol.verified` now provides offline-only builders and parsers for
the evidenced `0x0B` and `0x06` frames, response validation, and exact bulk
pattern classification. Targeted tests cover captured bytes, fields,
checksums, invalid frames, and bulk observations. Live client policy remains
blocked pending explicit owner approval.
