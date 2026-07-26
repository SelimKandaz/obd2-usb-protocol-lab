# Read-Only Command Evidence

Date: 2026-07-25

## Evidence status

The first updater transaction is now verified passively. No command has been
enabled or sent by the client.

| Candidate | Static evidence | Live passive evidence | Confidence | Safe to transmit |
|---|---|---|---|---|
| `0x0B` storage/capacity query candidate | exact builder and response decode | exact 16-byte request and `0x8B` response | HIGH bytes; MEDIUM meaning | approval required |
| `0x06` block-read candidate | address/length builder and bulk-IN path | three exact requests, responses, and bulk-IN pairs | HIGH bytes; MEDIUM meaning | approval required |
| `0x07` | non-PID branch only | absent | LOW | no |
| `identify`/`version` | no distinct request established | absent | UNKNOWN | no |

## First candidate details

- Endpoint: `0x01` interrupt OUT
- Request: `55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A`
- Length: 16 bytes
- Checksum: additive SUM8 over bytes 0–14, `0x0A`
- Response endpoint: `0x81` interrupt IN
- Response: `AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C`
- Response length: 16 bytes
- Response checksum: `0x8C`, independently validated
- Response value field: bytes 3–6 little-endian = `0x02000000`
- Observed response latency: approximately 18.8 ms
- Static references: `0x0040E670`, `0x00410010`, checksum builder `0x0040EC70`
- Passive capture reference: `updater_first_vendor.pcapng`, records 0–3
- Maximum response length observed: 16 bytes

## Risk assessment

The request is read-oriented in the observed updater path, but it precedes
address-bearing reads and the update state machine. Its semantic purpose is
not independently proven to be harmless. A separate update-stage capture also
shows that the official updater can progress to a dangerous `0x02` bulk OUT
after preliminary interrupt exchanges. Therefore the client policy remains
blocked. Explicit owner approval is required before any active execution.
