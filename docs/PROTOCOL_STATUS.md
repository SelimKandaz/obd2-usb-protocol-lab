# Protocol Status

| Feature | Status | Evidence | Confidence | Safe to query |
|---|---|---|---|---|
| USB enumeration | done | 20 live endpoint-0 records; addresses 5 -> 6 | VERIFIED LIVE | yes |
| USBPcap root-hub mapping | done | genuine captures on `\\.\USBPcap1` | VERIFIED LIVE | n/a |
| Endpoint discovery | done | descriptors declare `0x81`, `0x01`, `0x82`, `0x02` | VERIFIED LIVE | yes |
| First updater transaction | done | 22 live records, address 6, no synthetic records | VERIFIED LIVE | n/a |
| 16-byte interrupt request framing | done | four live OUT frames plus static builder agreement | VERIFIED HIGH | approval required |
| 16-byte interrupt response framing | done | three live IN responses plus static helper agreement | VERIFIED HIGH | approval required |
| Request checksum | done | SUM8 matches all four live OUT frames and static routine | VERIFIED HIGH | n/a |
| Response checksum | done | SUM8 matches all three live 16-byte IN responses | VERIFIED HIGH | n/a |
| `0x0B` request bytes | done | exact live request and static `0x0040E670` match | VERIFIED HIGH | approval required |
| `0x0B` response/value | done | `0x8B`, value `0x02000000`, static decode and one physical exchange agree | VERIFIED LIVE | explicit approval required |
| `0x06` request bytes/fields | done | three live addresses and static builder match | VERIFIED HIGH | approval required |
| `0x06` response/value | partial | `0x86`, zero value, three live responses | HIGH bytes; MEDIUM meaning | approval required |
| Owner-approved live `0x0B` validation | done | exact `0x0B` OUT → `0x8B` IN on physical VOD700; one earlier run returned `0x05` | VERIFIED LIVE; `0x05` semantics UNKNOWN | explicit approval required |
| Bulk-IN preliminary read | partial | repeated 4,096-byte and 8-byte patterns on `0x82` | HIGH pattern; UNKNOWN meaning | approval required |
| Bulk-OUT firmware write | observed in separate update-stage trace | one official-updater `0x02` submit, 4,104 bytes; no lab-generated write | VERIFIED dangerous | no |
| Heartbeat / polling | partial | repeated `0x86` and bulk-IN payloads within update path | MEDIUM | no |
| Firmware version query | blocked | no distinct command identified | UNKNOWN | no |
| Response status/NACK semantics | partial | only successful `0x8B`/`0x86` responses observed | MEDIUM | no |

## Safety gate

`identify`, `version`, and `0x06` remain disabled for live transport. The
evidence-backed `0x0B` entry is classified `READ_ONLY` and remains disabled by
default; `vod700 storage-query --approve-live` is the only explicit opt-in
dispatch path. It was validated against the physical device and returned the
canonical `0x8B` response. The earlier `0x05` observation remains unknown and
is not treated as a successful response.
