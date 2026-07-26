# USB Packet Corpus

Date: 2026-07-25

## Canonical captures

| Capture | Records | Result |
|---|---:|---|
| `private_samples/captures/baseline_reconnect.pcapng` | 20 | endpoint-0 enumeration only |
| `private_samples/captures/updater_first_vendor.pcapng` | 22 | first updater vendor transaction and bounded follow-on reads |

The first-updater canonical PCAPNG SHA-256 is
`5475B9B6C40413BB97C791C15CF286503626AEC64D90BD831CA3B1D278A8B731`.

## First-updater endpoint corpus

| Endpoint | Live records | Non-empty payloads | Payload lengths |
|---|---:|---:|---|
| endpoint 0 control | 0 | 0 | — |
| `0x01` interrupt OUT | 8 | 4 | 0, 16 |
| `0x81` interrupt IN | 6 | 3 | 0, 16 |
| `0x02` bulk OUT | 0 | 0 | — |
| `0x82` bulk IN | 8 | 4 | 0, 8, 4,096 |

All 22 records belong to bus 1, address 6. USBPcap `info=0` submit and
`info=1` completion records are retained; ordered IRP/phase pairing produces
the transaction timeline in `reports/updater_first_vendor_timeline.md`.

## Exact interrupt frames

```text
OUT 0x01  55aa0b0000000000000000000000000a
 IN 0x81  aa558b0000000200000000000000008c
OUT 0x01  55aa060000fb01001000000000000011
 IN 0x81  aa558600000000000000000000000085
OUT 0x01  55aa060010fb01001000000000000021
 IN 0x81  aa558600000000000000000000000085
OUT 0x01  55aa060020fb01001000000000000031
```

The final `0x06` request has a cancelled completion (`status=0xC0010000`)
because the bounded controller contained the updater. No independent packet
was sent by the lab tooling.
