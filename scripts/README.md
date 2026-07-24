# scripts/ — read-only Windows discovery

All scripts are **read-only**: they enumerate and report. None opens a device
handle for I/O, changes settings, or installs anything. Run from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\<name>.ps1
```

| Script                      | Purpose                                                        |
|-----------------------------|----------------------------------------------------------------|
| `get_vod700_device.ps1`     | PnP device node: status, driver, IDs, USB address (VID_0483/PID_5265). |
| `get_vod700_interfaces.ps1` | WinUSB device-interface symbolic links (from the registry).    |
| `get_vod700_endpoints.ps1`  | Endpoint map — live via the Python client, else the recorded map. |
| `capture_prereqs.ps1`       | Check Wireshark/USBPcap/Npcap; print current bus/address + filters. |
| `hash_updater_files.ps1`    | Phase 2 inventory: size, SHA-256, PE arch, signature (point at `private_samples\updater`). |

Notes:
- `hash_updater_files.ps1` requires `-Path`; nothing is executed, only hashed and
  read. Use `-OutJson` to save an inventory.
- `capture_prereqs.ps1` reminds you that Npcap ≠ USB capture; USBPcap is required.
