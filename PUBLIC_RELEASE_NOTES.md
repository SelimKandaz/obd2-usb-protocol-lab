# VOD700 Protocol Lab — release scope

This repository contains the reproducible, evidence-driven tooling and
documentation for passive USB protocol research on an ANCEL/Autophix VOD700.
It is intentionally safe to inspect and build offline.

## Included

- Dependency-free Python parsers, USBPcap/pcapng analysis, and replay helpers.
- Evidence taxonomy, protocol knowledge, state-machine records, and ESP32
  portability notes.
- Synthetic fixtures and tests that do not contain vendor firmware bytes.
- Read-only device discovery and descriptor inspection code.

## Never included

- Official updater executables, DLLs, driver installers, firmware/update
  containers, raw captures, or private support files.
- Credentials, personal machine paths, device-specific logs, or unredacted
  packet data. These remain in the local, git-ignored `private_samples/` vault.

## Safety boundary

Vendor update and addressed-storage paths are parser-only or disabled by the
policy gate. The default CLI sends no vendor-protocol bytes. The single
capacity-query path is disabled by default and requires explicit local approval;
no firmware write, erase, reset, or update operation is implemented.

The reports deliberately label capture facts, static conclusions, hypotheses,
and unknowns separately. This is a research snapshot, not a claim that the
complete VOD700 protocol or MCU firmware has been recovered.

Before making this repository public, review the current diff and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_project.ps1
git ls-files | Select-String -Pattern '\.(exe|dll|sys|bin|hex|dfu|img|pcap|pcapng|zip)$'
```

The second command must return no paths.
