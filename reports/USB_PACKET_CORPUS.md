# USB Packet Corpus

Date: 2026-07-24

## Baseline reconnect corpus

Canonical capture:
`private_samples\captures\baseline_reconnect.pcapng`

The corpus contains 20 live USBPcap records, all endpoint-0 control traffic:

| Sequence | Address | Relative time | Content |
|---:|---:|---:|---|
| 1 | 5 | 0.000000-0.016003 | device/configuration descriptors, language ID, set configuration |
| 2 | 6 | 81.121916-81.137621 | same descriptor/configuration sequence after reconnect |

The device descriptor payload includes VID `0483` and PID `5265`. The
configuration descriptor includes interrupt `0x81`/`0x01` and bulk `0x82`/`0x02`.

## Submit/completion interpretation

USBPcap `info=0` records are submits and `info=1` records are completions. The
capture has nonzero IRP IDs, but the driver reuses an IRP value across portions
of an enumeration sequence; pairing is therefore performed by ordered phase,
address, and adjacent control transaction, not IRP ID alone.

## Endpoint corpus counts

| Endpoint | Live records | Synthetic records | Payload lengths |
|---|---:|---:|---|
| endpoint 0 control | 20 | 0 | 0, 2, 8, 9, 18, 46 |
| `0x01` interrupt OUT | 0 | 0 | - |
| `0x81` interrupt IN | 0 | 0 | - |
| `0x02` bulk OUT | 0 | 0 | - |
| `0x82` bulk IN | 0 | 0 | - |

No SET_ADDRESS request is present. No exact 16-byte vendor frame is present. No
checksum test is applicable to this corpus, and no payload is eligible for
replay.
