# USBPcap Reconnect Validation

Date: 2026-07-24

## Verdict: VERIFIED LIVE

The supplied capture proves that `USBPcap1` is observing genuine VOD700 USB
traffic. It was recorded with USBPcapCMD on the complete root hub and without
descriptor injection.

Source capture:

- Path: `C:\USBPcapCaptures\VOD700_reconnect_20260724_202512.pcap`
- Size: 1,134 bytes
- SHA-256: `344604CCD58B8BF27AC10F85980C58AF2372AF488770B27CE4C0A9DA8B17536E`
- Format: classic pcap, 20 packets, 81.137621 seconds

Canonical private copy:

- Path: `private_samples\captures\baseline_reconnect.pcapng`
- Size: 1,556 bytes
- SHA-256: `3484911891084476D74E8D3553D15F13BE5676E09EED241388E7E5AEC4182878`

## Evidence

- All 20 records are USBPcap link type 249.
- All records have nonzero IRP IDs; none are synthetic injected records.
- Two live descriptor/configuration enumeration sequences are visible.
- No SET_ADDRESS request is present in this capture; address assignment occurred
  outside the recorded window or was not emitted by this USBPcap path.
- Device address changes from `5` to `6` after an 81.120376-second gap,
  consistent with disconnect/reconnect address reassignment.
- Both sequences contain device and configuration descriptors matching VID
  `0x0483`, PID `0x5265`, and the four expected endpoints.
- Submit/completion direction is represented by USBPcap's information bit and
  appears as ordered pairs; IRP ID alone is not used as a unique transaction
  key because the capture reuses an IRP value across the enumeration sequence.

## Endpoint result

| Endpoint | Records | Interpretation |
|---|---:|---|
| endpoint 0 control | 20 | live standard enumeration only |
| `0x01` interrupt OUT | 0 | no vendor request |
| `0x81` interrupt IN | 0 | no vendor response |
| `0x02` bulk OUT | 0 | no bulk write |
| `0x82` bulk IN | 0 | no bulk read |

This validates the capture backend and root-hub mapping. It does not establish
an updater handshake or authorize an active request.
