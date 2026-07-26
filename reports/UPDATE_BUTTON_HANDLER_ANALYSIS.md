# Update Button Handler Analysis

Date: 2026-07-25

## Status: FIRST LIVE TRANSACTION VERIFIED; EXACT MFC MESSAGE-MAP SYMBOL STILL UNKNOWN

The official updater UI capture and the later isolated physical validation are
documented separately. The following static findings are retained as the
independent code-side evidence.

## Dialog resource

PE resource dialog 102 is titled `Device upgrades` and contains:

| Control | ID | Class | Caption |
|---|---:|---|---|
| Update button | 1 | button (ATOM 128) | `Update` |
| Exit button | 2 | button (ATOM 128) | `Exit` |
| Progress bar | 1000 | `msctls_progress32` | — |
| Welcome/status text | 1001 | static | `Welcome to ANCEL's vehicle diagnostic tool !` |
| Feedback | 1005 | static | `Feedback` |

This identifies the user-visible control but does not by itself identify its
message-map handler or prove that the handler reaches the first USB write.

## Static request candidate

The command-builder function at `0x0040E670` initializes a 16-byte frame,
sets byte 2 to `0x0B`, clears bytes 3 through 14, and invokes the checksum
builder at `0x0040EC70`. The resulting exact candidate is:

```
55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
```

The final byte is consistent with the additive checksum over bytes 0 through
14 (`0x55 + 0xAA + 0x0B = 0x10A`, low byte `0x0A`). This was initially static
evidence only; the canonical updater capture and one physical validation later
observed the same request/response bytes.

The helper at `0x00410010` writes 16 bytes through pipe selector 1
(`0x01` interrupt OUT) and reads 16 bytes through selector 0 (`0x81`
interrupt IN). For command `0x0B`, the response discriminator is expected to
be byte 2 `0x8B`; the caller decodes response bytes 3–6 as a little-endian
value. These facts correlate with the canonical updater capture; the physical
client validation is performed through the independent policy-gated adapter
rather than by modifying or replaying the updater.

## Live correlation

The canonical first-updater capture independently observed the exact static
`0x0B` frame on `0x01` and its `0x8B` response on `0x81`, followed by the
static `0x06`/bulk-IN path. This proves that the captured worker path is
reachable from the owner-approved Update action. The exact symbolic MFC
message-map entry remains unresolved, but it is no longer necessary to infer
the first transfer bytes.

## Remaining proof

The exact MFC message-map entry and complete call chain from dialog control ID
1 remain UNKNOWN. The first live submit/completion pair is verified in
`reports/HANDSHAKE_ANALYSIS.md`; the bounded passive capture controller is
`scripts/capture_updater_first_vendor.ps1`.

The exact symbolic MFC message-map entry remains UNKNOWN, but it is not needed
for the first independent client transaction. The client promotes only the
`0x0B` query as an explicit opt-in after capture, static, replay, and physical
evidence; `0x06` and every update-stage path remain blocked.
