# Updater First Vendor Transaction Analysis

Date: 2026-07-25

## Capture identity

- Raw USBPcap PCAP: `private_samples/captures/updater_first_vendor.pcap`
- Raw size: 9,290 bytes
- Raw SHA-256: `29212D848F692B685E2C9CA24ADD6CCDE3D8FA99762558550A7D5B1EBFF8CE77`
- Canonical PCAPNG: `private_samples/captures/updater_first_vendor.pcapng`
- Canonical size: 9,748 bytes
- Canonical SHA-256: `5475B9B6C40413BB97C791C15CF286503626AEC64D90BD831CA3B1D278A8B731`
- USBPcap interface: `\\.\USBPcap1`
- VOD700 USB address: `6`
- Bus: `1`
- Capture duration: 0.082173 seconds
- Records: 22, all genuine live URBs; no synthetic descriptor records

The reconnect baseline was not repeated. The capture contains only the
dynamically assigned VOD700 address and no endpoint-0 enumeration records.

## Endpoint counts

| Endpoint | Direction | Type | Records | Non-empty payloads |
|---|---|---|---:|---:|
| `0x01` | OUT | interrupt | 8 | 4 x 16 bytes |
| `0x81` | IN | interrupt | 6 | 3 x 16 bytes |
| `0x02` | OUT | bulk | 0 | 0 |
| `0x82` | IN | bulk | 8 | 4 x 4,096 bytes; 4 x 8 bytes |

USBPcap `info=0` submits and `info=1` completions were paired by IRP ID,
address, endpoint, and phase. The first request/response pair is:

| Time | Endpoint | Phase | Bytes |
|---:|---|---|---|
| 0.000000 s | `0x01` OUT | submit | `55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A` |
| 0.0012 s | `0x01` OUT | completion | status 0, zero completion payload |
| 0.0015 s | `0x81` IN | submit | zero-length read request |
| 0.0202 s | `0x81` IN | completion | `AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C` |

## Reconstructed sequence

1. `0x0B` interrupt OUT request, 16 bytes.
2. `0x8B` interrupt IN response, 16 bytes, value `0x02000000` little-endian.
3. `0x06` interrupt OUT request for address `0x01FB0000`, field byte 8 `0x10`.
4. `0x86` interrupt IN response, 16 bytes, value `0`.
5. Two bulk-IN reads on `0x82`: 4,096 bytes followed by 8 bytes.
6. The same `0x06` request/response plus bulk-IN pattern repeats at addresses
   `0x01FB1000` and `0x01FB2000`; the final request is cancelled when the
   bounded controller contains the updater.

## Integrity and framing

All four non-empty interrupt OUT frames and all three non-empty interrupt IN
responses satisfy the same trailing additive checksum:

`frame[15] = sum(frame[0:15]) & 0xFF`

The request magic is `55 AA`; the response magic is `AA 55`; response command
is request command plus `0x80`. The 4,096-byte bulk-IN payloads begin with
`AA 55 AA 55` and are otherwise `0xFF` fill in this capture. The 8-byte
follow-up payload is exactly `FF FF FF FF 00 0F F1 FE`. Their semantic meaning
is not promoted beyond the captured pattern.

## Static correlation

The first live request exactly matches the static builder at `0x0040E670`:
command `0x0B`, all data bytes zero, additive checksum `0x0A`. The live `0x06`
requests match the static address-bearing builder and its `0x10` field. The
static helper at `0x00410010` predicts the observed `0x01` OUT -> `0x81` IN
interrupt exchange, followed by the bulk-IN path. This is independent static
and dynamic agreement at HIGH confidence for bytes, endpoints, and framing.

No `0x02` bulk OUT occurred. No firmware write was captured. The capture
therefore stops before any bulk-OUT update stage.
