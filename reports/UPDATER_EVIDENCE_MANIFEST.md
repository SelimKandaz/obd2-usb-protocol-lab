# Updater Evidence Manifest

Date: 2026-07-24

Scope: read-only inventory of the local, git-ignored official updater package.
No binary content is reproduced here.

## VERIFIED STATICALLY

- Original archive: `private_samples/updater/original/6a448a83cddfb.zip`
- Archive SHA-256:
  `0F23628CF36C57541D51458A1871D3E4EEEDF87BB73690661414540530BBC25C`
- Archive entries: 41
- Archive file members: 27 (the other 14 entries are directories)
- Path-traversal or absolute-path entries: 0
- Duplicate ZIP entry names: 0
- Nested archives: 0
- ZIP extensions: one EXE, four BIN, six INF, six CAT, six DLL, one BAT,
  three TXT, and directory entries.
- Entry timestamps span 2026-06-24 10:48:18 through 10:49:14.

The regenerated recursive inventory contains 82 files and 24 unique SHA-256
values. There are 23 hash groups with duplicates, covering 81 file instances.
This is explained by three equivalent extracted layouts plus WDF coinstaller
reuse across DM100, DM100HC, and DM300. The original ZIP is the only
single-instance hash. No duplicate evidence was deleted.

## 2026-07-26 archive verification

`vod700 firmware verify-archive` performs standard ZIP CRC validation and
compares each safe archive file member with the existing extracted root without
extracting or modifying anything. For the canonical archive, all 27 file
members passed CRC validation and byte-match the root working tree. The private
result is `private_samples/analysis/release_archive_verification.json`.

## Canonical hashes

| Logical artifact | SHA-256 | Copies | Status |
|---|---|---:|---|
| `Update.exe` | `F705FB6C6276FA52F75DD88269408D5CF061048F5EEB5451212EB1986D862C4D` | 3 | VERIFIED STATICALLY |
| `ExtFlashDat.bin` | `1A2B538D499125871436383A78FD6FE0158183970473A43088DB0C2D2CFC993B` | 3 | VERIFIED STATICALLY |
| DM100 `McuCode.bin` | `D36A9A4ECD084CB787096089DCBB4FF71104D25BBAA07F69D60CA3B9AFEB4C78` | 3 | VERIFIED STATICALLY |
| DM300 `McuCode.bin` | `5FC2749FE3E4E8294645412D82513E480BE2C5E2D6A4DD6A21ED66D52CF98F4B` | 3 | VERIFIED STATICALLY |
| DM300 `Erase.bin` | `1E560520B78CAD7D12143E2FDADAA3FFFD8203AB9A3DE8BA18E67C48E6006FC6` | 3 | VERIFIED STATICALLY |

The complete per-path inventory remains private in
`private_samples/updater_inventory.json`. `private_samples/` is covered by the
repository ignore rule, and no private evidence appears in git status.
