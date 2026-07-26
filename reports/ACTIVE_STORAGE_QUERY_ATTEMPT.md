# Owner-Approved Active Storage Query Attempt

Date: 2026-07-25

## Scope and approval

The owner explicitly approved one live transmission of the exact
evidence-backed storage query. This was the first active vendor-protocol
request sent by the lab. No replay, update-stage command, bulk write, or
second request was sent.

## Pre-send checks

- Repository HEAD: `36d71f9a8cf4e5b170462c01330871a0dca50e2c`
- Worktree: clean before the attempt
- Device: `USB\VID_0483&PID_5265\AUTOPHIX_DM`, PnP `Status=OK`
- Updater and `USBPcapCMD`: not running
- WinUSB interface paths: two paths enumerated; both exposed the same single
  vendor interface and endpoint map
- Selected path:
  `\\?\usb#vid_0483&pid_5265#autophix_dm#{f70242c7-fb25-443b-9e7e-a4260f373982}`

## Request sent

Endpoint `0x01` Interrupt OUT, 16 bytes:

```text
55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
```

The trailing `0A` is the verified SUM8 checksum. The policy entry was
temporarily enabled in-process for this single owner-approved attempt and was
restored to `enabled=false` and `ACTIVE_QUERY` immediately afterward. The
repository policy remains non-dispatchable.

## Observed result

WinUSB returned a 16-byte interrupt-IN response on endpoint `0x81`, but the
response command byte was `0x05`, not the passive-capture `0x8B` storage-query
response. The pre-diagnostic implementation discarded the raw frame while
raising the validation error, so the complete response bytes are **not
available** from this attempt. No retransmission was made.

This is an observation of an unknown/state response, not evidence that `0x05`
is a NACK or that the request is safe in every device state. Its semantics are
UNKNOWN. The capture-backed successful `0x8B` response remains the only
verified storage-query response.

## Read-only post-check

After the attempt, the device still reported PnP `Status=OK`; no updater or
USBPcapCMD process remained. Both enumerated WinUSB interface paths were then
opened only for standard descriptors and pipe queries. Each reported the same
configuration: vendor interface `0xFF`, interrupt `0x01`/`0x81` (16-byte
packets), and bulk `0x02`/`0x82` (64-byte packets). No vendor transfer was made
during this post-check.

## Decision

The active query is **not promoted**. The unexpected `0x05` response means the
live state-machine result is unresolved, and the exact response must be
captured before any classification. The client remains blocked by policy.

`transaction.py` now preserves raw response bytes in future diagnostics, but
this change does not send traffic. Any further live request requires a new,
explicit owner approval and must be preceded by a plan to retain the raw
response before parsing.
