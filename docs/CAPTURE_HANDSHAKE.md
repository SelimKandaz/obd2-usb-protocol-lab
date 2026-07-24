# Capture Workflow — Passive Handshake

Goal of the **first** capture: record only the updater detecting the device and
sitting idle. **No** update-related buttons are pressed.

## Prerequisites

USB capture on Windows needs **USBPcap**. Status on this research host (2026-07-24):

- Wireshark / tshark / dumpcap **4.6.7**: **installed** (via winget). ✅
- USBPcap: **NOT installed** → still blocks USB capture. ⛔
- Npcap: installed (via Nmap) — **but Npcap captures network interfaces only, it
  does NOT capture USB.** It does not help here.

USBPcap is a kernel-mode capture driver that loads at boot, so installing it is an
**owner action (UAC + reboot)**. Install it from an official source — the Wireshark
installer's **USBPcap** component, or the standalone official installer at
`https://desowin.org/usbpcap/` — approve UAC, then **reboot**. No change is made to
the VOD700's WinUSB driver. See `reports/CAPTURE_TOOLING.md`.

After the reboot, `dumpcap -D` should list one or more `USBPcap` interfaces.

## Automated capture (recommended once prerequisites are met)

`scripts\capture_updater_handshake.ps1` orchestrates the whole passive capture
safely: it verifies the device, auto-detects the USBPcap interface(s) and the
current USB address, starts a **time-bounded** capture, launches the updater with
**no arguments**, waits ~18 s for detection, closes it, hashes the pcapng, and runs
the analyzer. It **never** clicks or keys any update control and refuses to run if
USBPcap is missing.

```bash
# validate the environment without capturing anything
powershell -ExecutionPolicy Bypass -File scripts\capture_updater_handshake.ps1 -DryRun

# once USBPcap is installed (post-reboot) and the updater is in private_samples\updater\
powershell -ExecutionPolicy Bypass -File scripts\capture_updater_handshake.ps1 -UpdaterPath "private_samples\updater\Update.exe"
```

The manual procedure below remains valid if you prefer to drive Wireshark by hand.

Verify prerequisites and print the current capture target:

```bash
powershell -ExecutionPolicy Bypass -File scripts\capture_prereqs.ps1
```

## Find the current bus/address (do not hard-code it)

The USB address changes across reconnects. `capture_prereqs.ps1` prints the
device's current `DEVPKEY_Device_Address` (it was `9` at last check) and the
matching Wireshark display filter. Always re-check before a capture.

## Passive capture procedure

1. Ensure the VOD700 is connected to the desktop **only** (not to a vehicle).
2. Start the USB capture:
   - **Wireshark GUI:** pick the `USBPcap<N>` interface corresponding to the root
     hub the VOD700 is on. If unsure which root hub, start capture on each
     `USBPcap` interface, or use USBPcapCMD to list device trees.
   - **CLI (dumpcap):**
     ```bash
     "C:\Program Files\Wireshark\dumpcap.exe" -i USBPcap1 -w private_samples\captures\handshake.pcapng
     ```
3. Launch the official updater.
4. Let it detect the device. **Wait ~10–20 seconds.**
5. Do **not** press Update / Upgrade / Recover / Download / Flash / Firmware.
6. Close the updater.
7. Stop the capture.

Save the file under `private_samples\captures\` (git-ignored).

## Wireshark display filters

Primary (after you know the address):
```
usb.device_address == 9
```
Narrow to this device once descriptors have been exchanged:
```
usb.idVendor == 0x0483 && usb.idProduct == 0x5265
```
Endpoint-specific (validate field names in your Wireshark version first):
```
usb.endpoint_address == 0x01    // interrupt OUT (command candidate)
usb.endpoint_address == 0x81    // interrupt IN  (status candidate)
usb.endpoint_address == 0x02    // bulk OUT      (data candidate)
usb.endpoint_address == 0x82    // bulk IN       (data candidate)
```

**Field-name caveat:** Wireshark versions differ. Some expose
`usb.endpoint_address`, others `usb.endpoint_number`, and USBPcap vs. usbmon
dissectors label fields differently. If a filter yields nothing, open one packet
and read the actual field name from the detail pane. Our analyzer does **not**
depend on Wireshark field names — it parses the USBPcap pseudo-header directly.

## Analyze the capture (no tshark required)

```bash
vod700 capture summary  private_samples\captures\handshake.pcapng
vod700 capture analyze  private_samples\captures\handshake.pcapng --out reports --prefix handshake
```

Outputs:
- `reports\handshake_timeline.md` — human-readable timeline + endpoint groups
- `reports\handshake_packets.jsonl` — one JSON object per transfer
- `reports\handshake_packets.csv` — spreadsheet-friendly

Then look for a trailing checksum on the interrupt command channel:
```bash
vod700 capture checksums private_samples\captures\handshake.pcapng --endpoint 0x01
```

## Differential captures
See [`NEXT_CAPTURES.md`](NEXT_CAPTURES.md) for the A–H capture matrix that
isolates init vs. heartbeat vs. device-info traffic.
