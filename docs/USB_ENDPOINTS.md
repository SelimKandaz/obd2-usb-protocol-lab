# USB Endpoints

Interface 0, Alternate Setting 0. Class/SubClass/Protocol = `0xFF/0xFF/0x00`
(vendor-specific). Endpoint count = 4. **VERIFIED** twice: from the Windows
WinUSB pipe enumeration dump, and live via `WinUsb_QueryPipe`
(`vod700 endpoints`).

| Pipe | EP addr | Dir | Transfer   | Max packet | Interval |
|-----:|---------|-----|------------|-----------:|---------:|
| 0    | `0x81`  | IN  | Interrupt  | 16         | 1        |
| 1    | `0x01`  | OUT | Interrupt  | 16         | 1        |
| 2    | `0x82`  | IN  | Bulk       | 64         | 32       |
| 3    | `0x02`  | OUT | Bulk       | 64         | 32       |

## Channel roles from capture evidence

| Channel                 | Observed role                          | Confidence |
|-------------------------|---------------------------------------|------------|
| `0x01` OUT / `0x81` IN  | request / response exchange (interrupt) | VERIFIED |
| `0x02` OUT / `0x82` IN  | bulk data exchange                      | HIGH     |

The channel roles above are observed in the genuine updater captures. The
semantic meaning of individual bulk payloads and the safety of the bulk OUT
path are not inferred from the role alone: the observed bulk OUT is explicitly
dangerous and remains blocked. The `vod700 capture analyze` tool preserves the
raw endpoint timelines for independent review.

## Practical implications for parsing
- Interrupt frames are bounded at **16 bytes** → a single command/response very
  likely fits in one 16-byte frame (fixed-size framing candidate).
- Bulk frames are **64 bytes** → larger messages probably fragment across
  multiple 64-byte packets, terminated by a short packet (standard USB bulk
  convention — see `framing.reassemble_bulk`, tagged LOW confidence).
- The interval of 32 on the bulk endpoints is unusual for bulk (interval is
  normally meaningful only for interrupt/iso); treat the reported value as
  informational, not load-bearing.
