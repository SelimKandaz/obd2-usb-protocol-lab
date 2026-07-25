# VOD700 Protocol - Milestone 4

Date: 2026-07-24

## Outcome

The USB capture path is now VERIFIED LIVE through a supplied disconnect/reconnect
capture made with `Update.exe` closed. The VOD700 was observed at USB address 5,
then at address 6 after reconnect, with 20 real endpoint-0 descriptor/configuration
records. SET_ADDRESS is not present in the recorded window.

No vendor traffic was observed. The updater-open reconnect scenario, runtime
process observation, and exact MFC Update-button handler reconstruction remain
unimplemented. No Update button was clicked and no independent request was sent.

## Capture artifacts

- Source: `C:\USBPcapCaptures\VOD700_reconnect_20260724_202512.pcap`
- Source size/hash: 1,134 bytes / `344604CCD58B8BF27AC10F85980C58AF2372AF488770B27CE4C0A9DA8B17536E`
- Canonical: `private_samples\captures\baseline_reconnect.pcapng`
- Canonical size/hash: 1,556 bytes / `3484911891084476D74E8D3553D15F13BE5676E09EED241388E7E5AEC4182878`
- USBPcap interface: `\\.\USBPcap1`
- Device addresses: 5 -> 6
- Capture duration: 81.137621 seconds

## Evidence classification

- VERIFIED LIVE: USBPcap root-hub capture, standard enumeration, address change
- VERIFIED STATICALLY: WinUSB paths, endpoint selectors, 16-byte frame builder,
  additive request checksum, command candidates
- UNKNOWN: updater open after reconnect, heartbeat, vendor command semantics,
  response checksum, Update-button MFC handler
- BLOCKED: active read-only request promotion

## Stop point

The next capture may launch `Update.exe` idle and repeat disconnect/reconnect,
but it must remain passive and stop before any button-triggered write. Any
debugger pre-send plan is prepared only as documentation and has not been run.
