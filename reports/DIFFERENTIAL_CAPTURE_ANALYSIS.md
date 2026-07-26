# Differential Capture Analysis

Date: 2026-07-25

## Baseline versus updater action

| Channel | Reconnect baseline | First updater capture | Conclusion |
|---|---:|---:|---|
| endpoint 0 control | 20 live | 0 | known enumeration excluded |
| `0x01` interrupt OUT | 0 | 8 records / 4 frames | updater command channel |
| `0x81` interrupt IN | 0 | 6 records / 3 responses | updater response channel |
| `0x02` bulk OUT | 0 | 0 | no firmware write observed |
| `0x82` bulk IN | 0 | 8 records / 4 data pairs | preliminary read path |

The updater capture is address 6 only and contains no reconnect enumeration.
This is a clean differential against the canonical address-transition baseline.

## Transaction progression

The first request is `0x0B`, followed by response `0x8B` carrying the
little-endian value `0x02000000`. It is followed by `0x06` requests at
`0x01FB0000`, `0x01FB1000`, and `0x01FB2000`. Each completed `0x06` response is
`0x86` with value zero, followed by a 4,096-byte and an 8-byte bulk-IN read.

The third `0x06` completion is cancelled by containment; this is an expected
capture boundary, not a device NACK.

## Separate update-stage differential

The later private update-stage capture is intentionally separate from the
preliminary fixture. It contains 12 live records: four interrupt OUT/IN frame
pairs and one 4,104-byte `0x02` bulk OUT submit. The bulk block begins
`55 AA 55 AA` and its trailing big-endian SUM32 is `0x0007FCC2`. This confirms
the static dangerous bulk-write builder at `0x00411330`; it does not promote
any active command and is not part of the read-only evidence set.

## Static/dynamic result

Static function `0x0040E670` and helper `0x00410010` independently predict the
live `0x0B` frame, 16-byte interrupt exchange, `0x06` address layout, and
bulk-IN follow-on. This raises the byte-level command/framing confidence to
HIGH. The semantic meaning of the 0x0B value and bulk payload remains MEDIUM.
