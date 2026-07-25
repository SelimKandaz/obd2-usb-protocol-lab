# Protocol Hypothesis

Date: 2026-07-24

## VERIFIED LIVE

- USBPcap captures genuine VOD700 standard enumeration on `\\.\USBPcap1`.
- The device address changes from 5 to 6 across reconnect.
- The descriptor declares interrupt `0x81`/`0x01` and bulk `0x82`/`0x02`.
- The reconnect capture contains no records on those vendor-data endpoints.

## VERIFIED STATICALLY

- Updater requests/responses are fixed-width 16-byte interrupt transfers.
- Request bytes 0 and 1 are `55 AA`.
- Request byte 15 is an additive sum8 over bytes 0 through 14.
- Static candidates include `0x0B` and `0x06`.

## UNKNOWN / BLOCKED

- updater-open behavior after reconnect
- vendor command or response bytes
- heartbeat cadence
- response checksum and ACK/NACK layout
- Update-button MFC handler identity
- whether any candidate is safe to send

Standard endpoint-0 enumeration is transport evidence and must not be promoted
to vendor protocol evidence. No active request satisfies the two-source rule.
