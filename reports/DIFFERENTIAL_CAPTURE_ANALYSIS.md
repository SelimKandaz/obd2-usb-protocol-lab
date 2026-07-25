# Differential Capture Analysis

Date: 2026-07-24

## Baseline reconnect capture: VERIFIED LIVE

The supplied complete-root-hub capture contains two standard enumeration
sequences:

| Phase | Relative time | USB address | Records | Result |
|---|---:|---:|---:|---|
| before disconnect | 0.000000-0.016003 s | 5 | 10 | live endpoint-0 enumeration |
| after reconnect | 81.121916-81.137621 s | 6 | 10 | live endpoint-0 enumeration |

The 81.120376-second gap and address transition 5 -> 6 are consistent with the
device being disconnected and reconnected. The records have nonzero IRP IDs and
are therefore distinct from the six zero-IRP synthetic records in the earlier
idle capture. SET_ADDRESS is not present in the recorded window.

## Endpoint differential

| Channel | Baseline reconnect | Updater-idle capture | Interpretation |
|---|---:|---:|---|
| endpoint 0 control | 20 live | 6 synthetic | enumeration only; captures differ in source |
| `0x01` interrupt OUT | 0 | 0 | no vendor request |
| `0x81` interrupt IN | 0 | 0 | no vendor response |
| `0x02` bulk OUT | 0 | 0 | no bulk write |
| `0x82` bulk IN | 0 | 0 | no bulk read |

No updater-open reconnect capture has been performed. Therefore no claim can be
made about whether `Update.exe` opens WinUSB after reconnect.
