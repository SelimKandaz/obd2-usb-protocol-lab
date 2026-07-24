# Read-Only Command Evidence

Date: 2026-07-24

## BLOCKED — insufficient independent evidence

Static analysis found command bytes `0x0B`, `0x06`, and `0x07`, but no passive
capture exists to identify a device-info/model/version request or confirm that
any candidate is read-only on the VOD700.

Therefore there is currently:

- no proposed independently executable request
- no capture response example
- no replay fixture based on real traffic
- no parser promotion
- no policy promotion

`identify` and `version` remain disabled, `UNSAFE`, and `UNKNOWN`. No active
vendor-protocol request was sent.
