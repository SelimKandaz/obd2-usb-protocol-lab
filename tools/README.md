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

Planned in-repo helpers: `tools/entropy.py` (sliding-window Shannon entropy for
firmware region classification), `tools/strings_scan.py` (targeted string/const
search over an extracted updater tree).
