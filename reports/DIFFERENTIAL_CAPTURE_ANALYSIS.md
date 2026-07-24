# Differential Capture Analysis

Date: 2026-07-24

## Available traces

The accepted bounded run is
`handshake_20260724_150600.pcapng`. A preliminary capture plumbing attempt,
`handshake_20260724_145429.pcap`, was not accepted as a bounded result because
its writer did not shut down normally.

Both decode to the same six synthetic descriptor/configuration records in the
same order. This repetition confirms the records come from USBPcap descriptor
injection. It is not independent evidence of updater behavior.

## Differential result

| Channel | Preliminary plumbing trace | Accepted 18-second trace | Difference attributable to updater |
|---|---:|---:|---:|
| endpoint 0 synthetic records | 6 | 6 | 0 |
| `0x01` interrupt OUT | 0 | 0 | 0 |
| `0x81` interrupt IN | 0 | 0 | 0 |
| `0x02` bulk OUT | 0 | 0 | 0 |
| `0x82` bulk IN | 0 | 0 | 0 |

No request/response, heartbeat, or bulk-transfer differential exists. A second
passive scenario would be required to determine whether automatic detection is
triggered only by a connect event or a non-update UI action. No such scenario
was run in this milestone.
