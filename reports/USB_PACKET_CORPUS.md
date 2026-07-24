# USB Packet Corpus

Date: 2026-07-24

Source capture:
`private_samples\captures\handshake_20260724_150600.pcapng`

SHA-256:
`4CEC0D3B43DB4BE12F5B8F6BCBC43446E46E4A49F49B66E685AC856748D80D3F`

## Corpus scope

The capture was filtered to bus 1, USBPcap address 4 on `\\.\USBPcap1`. The
native analyzer decoded six records. They are the three descriptor/configuration
pairs injected by USBPcap at capture start, not updater traffic.

The ignored per-record exports are:

- `reports/handshake_20260724_150600_packets.jsonl`
- `reports/handshake_20260724_150600_packets.csv`
- `reports/handshake_20260724_150600_timeline.md`

## Endpoint timelines

### Endpoint 0 control

| t (s) | Pair | Stage | Length | Payload |
|---:|---:|---|---:|---|
| 0.000000 | 1 | descriptor request | 8 | `8006000100001200` |
| 0.000000 | 1 | injected descriptor | 18 | `120100020000004083046552000201020301` |
| 0.000000 | 2 | descriptor request | 8 | `8006000200002e00` |
| 0.000000 | 2 | injected descriptor | 46 | `09022e00010100c0320904000004ffff000007058103100001070501031000010705820240002007050202400020` |
| 0.000000 | 3 | set configuration | 8 | `0009010000000000` |
| 0.000000 | 3 | injected completion | 0 | empty |

### `0x01` interrupt OUT

No records. No 16-byte request frame was captured.

### `0x81` interrupt IN

No records. No device response was captured.

### `0x02` bulk OUT

No records.

### `0x82` bulk IN

No records.

## Corpus interpretation

The descriptor payload verifies VID `0x0483`, PID `0x5265`, and the expected
endpoint descriptors (`0x81`, `0x01`, `0x82`, `0x02`). It does not show the
updater opening the WinUSB interface or performing any vendor transfer.

No submit/completion pair with a nonzero IRP ID exists. No payload is eligible
for replay or read-only-command promotion.
