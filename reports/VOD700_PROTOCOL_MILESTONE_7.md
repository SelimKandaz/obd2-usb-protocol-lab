# VOD700 Protocol Lab — Milestone 7

Date: 2026-07-25

## Result

The first owner-approved diagnostic run returned an unclassified `0x05`
response. After the diagnostic path was corrected to retain raw response bytes,
one additional owner-authorized run of the exact passive/static `0x0B` query
completed successfully with the expected `0x8B` response. No retry loop,
update-stage command, bulk write, or firmware operation was used.

## Live request

```text
Endpoint: 0x01 Interrupt OUT
55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
```

The request bytes and SUM8 are independently supported by the canonical
updater capture and static `Update.exe` analysis.

## Live result

The successful physical exchange was:

```text
OUT 0x01  55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
IN  0x81  AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C
```

The response command, checksum, exact length, and little-endian value
`0x02000000` all match the canonical passive capture. The first `0x05`
observation remains documented as an unresolved state-dependent response, but
it is not the result of the final validated run.

## Containment and post-check

- Policy was restored to disabled after the one approved call.
- No updater or USBPcap process remained.
- PnP status remained `OK`.
- Both WinUSB interface paths were inspected with standard descriptors and pipe
  queries only; both exposed the same expected endpoints.
- No bulk endpoint was written and no update operation was started by the lab.

## Implementation change

`vod700.client.transaction` now includes the raw response hex in parse and
unexpected-command errors. The `storage-query` policy entry is now classified
`READ_ONLY`, but remains disabled by default. The CLI exposes it only through
the explicit `vod700 storage-query --approve-live` path, which restores the
disabled state after one transaction.

## Validation

The full test, lint, type, compile, and wheel checks are rerun for this
milestone. See the final commit and `reports/ACTIVE_STORAGE_QUERY_ATTEMPT.md`
for the evidence boundary.
