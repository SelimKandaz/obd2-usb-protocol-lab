# VOD700 Protocol Lab — Milestone 7

Date: 2026-07-25

## Result

One owner-approved live transmission of the exact passive/static `0x0B`
storage query was performed through the policy-gated WinUSB adapter. The
request was sent once and the client stopped on the first unexpected response.
No retry or second vendor request followed.

## Live request

```text
Endpoint: 0x01 Interrupt OUT
55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
```

The request bytes and SUM8 are independently supported by the canonical
updater capture and static `Update.exe` analysis.

## Live result

The device returned a 16-byte `0x81` Interrupt IN frame whose command byte was
`0x05`. The previous transaction diagnostic did not retain the raw frame after
the parser rejected that command, so the response payload cannot be claimed
byte-for-byte. The result is therefore an **UNKNOWN state/response**, not a
verified NACK and not a successful storage query.

## Containment and post-check

- Policy was restored to disabled after the one approved call.
- No updater or USBPcap process remained.
- PnP status remained `OK`.
- Both WinUSB interface paths were inspected with standard descriptors and pipe
  queries only; both exposed the same expected endpoints.
- No bulk endpoint was written and no update operation was started by the lab.

## Implementation change

`vod700.client.transaction` now includes the raw response hex in parse and
unexpected-command errors. This is diagnostic-only and does not enable a live
command. The shipped policy remains blocked, and the exact next live request
requires a new explicit owner approval.

## Validation

The full test, lint, type, compile, and wheel checks are rerun for this
milestone. See the final commit and `reports/ACTIVE_STORAGE_QUERY_ATTEMPT.md`
for the evidence boundary.
