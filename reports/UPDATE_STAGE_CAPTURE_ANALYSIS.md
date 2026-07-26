# Official Updater Update-Stage Capture

Date: 2026-07-25

This is a separate private capture from the preliminary transaction fixture.
It was produced by the official updater and is retained only for analysis;
the binary capture and firmware payload are not committed to git.

## Capture identity

- Raw PCAP: `private_samples/captures/updater_update_stage.pcap`
- Size: 4,708 bytes
- SHA-256: `F20FC6DA3D5C819F319F57B13A6544B6BD865EFB40ABDFCAFEDF8DC4A108DB6A`
- Canonical PCAPNG: `private_samples/captures/updater_update_stage.pcapng`
- PCAPNG SHA-256: `9D5853435EAD142CBED7439E6A980FA402935A2427B92CED6D2D7D704BADCC0A`
- Records: 12 live URBs, bus 1 / address 6

## Timeline

```text
0x01 OUT  55 aa 03 00 47 00 00 00 00 00 00 00 00 00 00 49
0x81 IN   aa 55 83 00 00 00 00 00 00 00 00 00 00 00 00 82
0x01 OUT  55 aa 01 10 00 00 00 00 00 00 00 00 00 00 00 10
0x81 IN   aa 55 81 00 00 00 00 00 00 00 00 00 00 00 00 80
0x02 OUT  4104-byte bulk block, prefix 55 aa 55 aa
```

The 4,104-byte bulk block is the dangerous update path. Its trailing
big-endian 32-bit total is `0x0007FCC2`, equal to the additive sum of the
preceding 4,100 bytes. The payload itself is intentionally not reproduced or
committed. No further update-stage operation was allowed after containment.

## Interpretation

The `0x03` and `0x01` interrupt frames and their `0x83`/`0x81` responses are
live evidence of a later updater state. The `0x02` transfer confirms the
static bulk-write builder at `0x00411330`; it is not read-only and must never be
implemented as an active command. The preliminary `0x0B`/`0x06` capture remains
the canonical read-oriented evidence, separate from this update-stage trace.

## Safety result

The project sent no packet. The official updater generated the observed bulk
OUT. `Update.exe` and USBPcapCMD are no longer running, and the device remains
present as `Status=OK`. No subsequent capture or update action is authorized.

## 2026-07-26 artifact correlation

The update-stage frame is now correlated with the local official package using
the offline-only `vod700 firmware match-bulk` tool. Its 4,096-byte data section
matches byte-for-byte the first page of `bin\DM100\McuCode.bin`:

- DM100 artifact SHA-256:
  `D36A9A4ECD084CB787096089DCBB4FF71104D25BBAA07F69D60CA3B9AFEB4C78`
- Matching page SHA-256:
  `D0D028CE79946A7DB54E4B0D7A424085AC15CE4273007FC9D007F5B781CA313B`
- Page equality: `true`; transport SUM32BE: valid
- `0x03` page count `0x0047` equals `ceil(287552 / 4096) = 71`

This proves the captured host worker transports the opaque DM100 page without
a host-side transform for this page. It does not establish the inner container
format or authorize a repeat of the update transfer.
