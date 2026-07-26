# tools/

Pointers to **safe, read-only** static-analysis tools. **No binaries are
committed here** — install them yourself.

| Purpose                 | Tool(s)                                  |
|-------------------------|------------------------------------------|
| USB capture             | Wireshark (+ **USBPcap** component), dumpcap |
| Capture parsing         | this repo's `vod700 capture` (no tshark needed) |
| PE inspection           | `dumpbin`, PE-bear, Detect It Easy (DIE)  |
| .NET decompilation      | ILSpy, dnSpyEx                            |
| Native decompilation    | Ghidra                                    |
| Strings / signatures    | Sysinternals `strings`, `sigcheck`, `binwalk` |
| Archives                | 7-Zip                                     |
| Hashing / signatures    | `scripts\hash_updater_files.ps1` (in-repo) |

## Rules
- Static analysis only. Never execute updater/firmware binaries as part of RE.
- Do not patch or modify official binaries.
- Do not commit decompiler project databases (`.idb`, `.i64`, `.bndb`, `.gpr`,
  `.rep`) — they are git-ignored.

## Reproducible offline helpers

`tools/analyze_updater.py` is a static-only PE report generator. It uses the
project analysis venv's `pefile` and `capstone` packages, which are deliberately
not runtime dependencies of `vod700`. In addition to imports, direct calls,
and selected strings, it conservatively records x86 MFC `WM_COMMAND` map-shaped
records whose handler pointers land in `.text`. Those records are structural
evidence, not vendor symbol recovery.

```powershell
.\.venv\Scripts\python.exe tools\analyze_updater.py `
  --input private_samples\updater\Update.exe `
  --out private_samples\analysis\updater_static_v4.json
```

The output can include targeted vendor strings, so keep it under the ignored
`private_samples\analysis\` directory. It never executes or modifies the
target. For container structure, use the dependency-free package CLI:

```powershell
vod700 firmware inspect private_samples\updater\bin\DM100\McuCode.bin --deep `
  --out private_samples\analysis\dm100_mcucode_inventory.json
vod700 firmware compare private_samples\updater\bin\DM100\McuCode.bin `
  private_samples\updater\bin\DM300\McuCode.bin `
  --out private_samples\analysis\dm100_dm300_compare.json

# Compare an observed 0x02 bulk page with a local artifact without printing
# the page or constructing a write packet.
vod700 firmware match-bulk private_samples\captures\updater_update_stage.pcapng `
  private_samples\updater\bin\DM100\McuCode.bin --bus 1 --address 6 `
  --out private_samples\analysis\update_stage_dm100_match.json

# Verify the original local release ZIP against its extracted working tree.
# This reads and hashes members but does not extract, execute, or modify them.
vod700 firmware verify-archive private_samples\updater\original\release.zip `
  private_samples\updater `
  --out private_samples\analysis\release_archive_verification.json

# Validate public machine-readable claims without inspecting private samples.
.\.venv\Scripts\python.exe tools\validate_knowledge.py
```
