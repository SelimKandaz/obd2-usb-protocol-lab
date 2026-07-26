# ESP32 Portability Reference

This document is a transport-independent specification aid, not an ESP32
firmware implementation. It includes only protocol elements supported by the
knowledge base and excludes every update/erase/write operation.

Machine-readable source: [`knowledge/protocol_knowledge.json`](../knowledge/protocol_knowledge.json).

## USB profile to reproduce in a fixture

| Role | Endpoint | Type | Observed maximum packet |
|---|---|---|---:|
| host request | `0x01` | interrupt OUT | 16 |
| device response | `0x81` | interrupt IN | 16 |
| host update data | `0x02` | bulk OUT | 64 endpoint packet; dangerous protocol path |
| device data | `0x82` | bulk IN | 64 endpoint packet |

Endpoint addresses are USB transport details. The 16-byte frame parser and
checksum should remain independent of TinyUSB/ESP-IDF plumbing.

## Confirmed 16-byte frame layout

```c
/* Wire layout, no compiler packing assumptions required. */
enum { VOD700_INTERRUPT_FRAME_LEN = 16 };

static inline uint8_t vod700_sum8(const uint8_t frame[16]) {
    uint8_t sum = 0;
    for (unsigned i = 0; i < 15; ++i) sum = (uint8_t)(sum + frame[i]);
    return sum;
}

/* Request: [0]=0x55, [1]=0xAA, [2]=command, [15]=SUM8.
 * Response: [0]=0xAA, [1]=0x55, [2]=response command, [15]=SUM8.
 */
```

Verified fixture vector:

```text
request : 55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
response: AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C
```

For a compatible **offline test fixture only**, the response payload bytes 3–6
are little-endian `0x02000000`. Do not use the fixture as a claim that all
hardware responding to those bytes has identical storage.

## Parser-only bulk shapes

```text
Feedback-like bulk IN:
  AA 55 AA 55 | 4096 data bytes | SUM32BE(first 4100 bytes)

Dangerous update bulk OUT:
  55 AA 55 AA | 4096 artifact bytes | SUM32BE(first 4100 bytes)
```

Only the first shape is represented by an offline parser. The second has an
inspector, not a builder or sender.

## Portable state guidance

```text
parse interrupt request/response -> validate magic + SUM8
  -> accept only an explicitly modeled fixture command
  -> bound length and timeout at the transport edge
  -> preserve raw bytes and record source/evidence
  -> never infer a state-changing operation from a matching command byte
```

## Explicitly excluded from ESP32 implementation

- Live `0x06` addressed reads
- `0x01`/`0x02`/`0x03`/`0x04` update-stage commands, bulk OUT, erase, reset,
  recovery
- Firmware container decoding or writing
- CAN, ISO-TP, K-Line, LIN, and vehicle interaction
- MCU/flash assumptions based on related hardware

Before implementing any excluded item, extend the knowledge base with a
capture/static/physical evidence chain and add synthetic parser vectors first.
