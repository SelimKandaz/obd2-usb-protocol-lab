# Read-Only Command Evidence

Date: 2026-07-24

## Decision: BLOCKED

The genuine reconnect capture validates only standard USB enumeration. It has no
traffic on the VOD700 interrupt or bulk endpoints. The earlier updater-idle
capture likewise has no live vendor traffic.

| Candidate | Static evidence | Live passive evidence | Classification |
|---|---|---|---|
| `0x0B` | capacity/size candidate; additive-checksum frame template | absent | UNKNOWN / blocked |
| `0x06` | address-bearing block-read candidate followed by bulk IN | absent | UNKNOWN / blocked |
| identify/version | no unique request identified | absent | UNKNOWN / blocked |

The standard-control metadata value `0x000B` in enumeration records is not the
vendor opcode `0x0B`. No request, response, endpoint, timeout, maximum response
length, or read-only risk assessment is sufficiently evidenced for transmission.

The client policy remains unchanged. No vendor request has been sent.
