# Protocol Status

Evidence taxonomy and source references live in
[`knowledge/protocol_knowledge.json`](../knowledge/protocol_knowledge.json).
Confidence describes strength; evidence classification describes the kind of
support. A high-confidence byte layout is not automatically safe to transmit.

| Feature | Status | Strongest evidence | Live status |
|---|---|---|---|
| USB descriptor/profile | complete | PHYSICALLY_VERIFIED | standard reads allowed |
| WinUSB pipe map | complete | PHYSICALLY_VERIFIED + STATIC | standard query allowed |
| USBPcap submit/completion correlation | complete | CAPTURE_VERIFIED + parser tests | offline only |
| 16-byte interrupt frame | complete | CAPTURE_VERIFIED + STATIC | builder only for approved `0x0B` |
| SUM8 trailer | complete | CAPTURE_VERIFIED + STATIC | parser/builder verified |
| `0x0B -> 0x8B` | complete | PHYSICALLY_VERIFIED + capture + static | explicit opt-in only |
| `0x06 -> 0x86` address layout | complete bytes; semantic bounded | capture + static tail workers | blocked |
| `0x82` feedback bulk frame | complete captured shape | capture + static | parser only |
| Feedback tail window | mapped | capture + static | blocked |
| Review & Print tail window | mapped static-only | STATIC | blocked |
| `0x03 -> 0x83` | complete captured frame | capture + static | dangerous, blocked |
| `0x04 -> 0x84` ExtFlash stage | exact static candidate only | static worker + artifact size | dangerous, blocked |
| final interrupt `0x02 -> 0x82` | exact static candidate only | static worker control flow | dangerous, blocked |
| `0x01 -> 0x81` page handshake | complete captured frame | capture + static | dangerous, blocked |
| `0x02` update bulk page | complete captured layout | capture + static | dangerous, blocked |
| DM100 first update page matching | complete | capture + static + offline match | offline only |
| Container extraction/decryption | not recovered | structural scans only | no live use |
| MCU/flash/bootloader identification | unknown | related-device research only | no claim |
| Version/identity vendor request | unknown | no exact bytes | blocked |
| ECU/vehicle protocol | out of scope for current session | no vehicle connection | blocked |

## Safety gate

The default client never sends vendor protocol bytes. The only exception is
`vod700 storage-query --approve-live`, which performs one verified `0x0B`
transaction after explicit command-line approval and restores the disabled
policy state afterwards. It should not be used as a routine baseline.

`0x06`, all update commands (`0x01`, `0x03`), bulk OUT, erase/recovery,
firmware, reset, unknown response handling, and all ECU interactions remain
blocked. Offline parsers and memory plans exist to preserve knowledge without
turning capture-derived bytes into active traffic.
