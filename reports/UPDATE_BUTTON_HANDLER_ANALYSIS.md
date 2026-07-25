# Update Button Handler Analysis

Date: 2026-07-25

## Status: STATIC EVIDENCE IMPROVED; LIVE HANDLER/CAPTURE PENDING

No updater UI was clicked and no project-generated USB request was sent. The
following findings are read-only analysis of the official `Update.exe`.

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
14 (`0x55 + 0xAA + 0x0B = 0x10A`, low byte `0x0A`). This is static evidence
only; it has not been observed on USB and must not be transmitted.

The helper at `0x00410010` writes 16 bytes through pipe selector 1
(`0x01` interrupt OUT) and reads 16 bytes through selector 0 (`0x81`
interrupt IN). For command `0x0B`, the response discriminator is expected to
be byte 2 `0x8B`; the caller decodes response bytes 3–6 as a little-endian
value. These facts remain uncorrelated with a live Update-button capture.

## Remaining proof

The exact MFC message-map entry, call chain from dialog control ID 1, and the
first live submit/completion pair remain UNKNOWN. The bounded passive capture
controller is `scripts/capture_updater_first_vendor.ps1`; it waits for the
owner to open the official updater, then waits for an explicit owner click
signal, and contains the updater immediately afterward.

Until a live capture independently matches the static candidate (or another
static/runtime pair reaches HIGH confidence), no read-only command is enabled
in the client policy.
