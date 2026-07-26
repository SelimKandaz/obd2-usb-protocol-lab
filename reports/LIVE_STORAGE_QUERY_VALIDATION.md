# Live Storage Query Validation

Date: 2026-07-25

## Physical validation

After the first diagnostic attempt returned an unclassified `0x05`, one new
owner-authorized run used the exact same evidence-backed request and the
updated raw-response diagnostics. The request completed successfully.

- Device: `USB\VID_0483&PID_5265\AUTOPHIX_DM`
- PnP status before/after: `OK`
- Selected WinUSB path:
  `\\?\usb#vid_0483&pid_5265#autophix_dm#{f70242c7-fb25-443b-9e7e-a4260f373982}`
- Interface paths discovered: 2 (both expose the same endpoint map)
- Endpoint: `0x01` Interrupt OUT → `0x81` Interrupt IN
- Request length: 16 bytes
- Response length: 16 bytes

## Exact exchange

Request:

```text
55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A
```

Response:

```text
AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C
```

Both trailing bytes validate with the captured SUM8 algorithm. The response
value bytes `03..06` decode little-endian as `0x02000000` (33,554,432).

## Containment

- No updater was launched.
- No bulk endpoint was used.
- No update, erase, firmware, or recovery operation was invoked.
- The in-process policy override was restored to `enabled=false` immediately
  after the exchange.
- No live PCAP was created for this direct validation run; the passive
  canonical fixture remains the transport-independent packet evidence.

## Classification

The `0x0B` request/`0x8B` response is now confirmed by three independent
layers: official-updater capture, static updater analysis, and one successful
physical VOD700 exchange. The byte-level command and response are VERIFIED
LIVE. The value is strongly consistent with a capacity/size query; update-stage
side effects were not observed from this isolated request.

The command remains opt-in in the client: a caller must pass an explicit live
approval flag. The default policy does not dispatch vendor traffic.
