# private_samples/ — Local Vault (never committed)

`private_samples/` is **git-ignored in its entirety**. It is where all
proprietary and private material lives so it never reaches version control.

```
private_samples/
├─ updater/     # official VOD700 updater install or extracted files
├─ firmware/    # firmware / update containers
└─ captures/    # raw pcapng/pcap captures (may contain other-device traffic)
```

## What goes here
- Official updater installer / extracted binaries / DLLs / configs
- Firmware and update containers
- Raw USB captures (before redaction)
- Any file carrying host-identifying or proprietary data

## What must NOT be committed from here
Everything. If you need to share a finding, extract only:
- hashes, offsets, lengths, entropy values, field layouts
- small, **redacted**, **synthetic** fixtures with no proprietary bytes

## How the tools use it
- `scripts\hash_updater_files.ps1 -Path private_samples\updater` → inventory
- `vod700 capture analyze private_samples\captures\handshake.pcapng`

The directory is created locally and is expected to be empty in a fresh clone.
