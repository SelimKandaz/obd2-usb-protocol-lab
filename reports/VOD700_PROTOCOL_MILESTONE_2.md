# VOD700 Protocol — Milestone 2 Status

Milestone: *updater acquisition, passive capture, protocol reconstruction, verified
read-only identification.* Date: 2026-07-24. Host username/paths redacted.

## Outcome in one line
All safe, unblocked work is done (capture tooling installed, device re-verified,
capture orchestrator built, updater located). The evidence-dependent phases are
**BLOCKED** on two owner actions: installing USBPcap (UAC + reboot) and downloading
the sign-in-gated official updater.

## 1. HEAD & commits
- Milestone 1 ended at `ea09992`. Milestone-2 commits add capture tooling reports,
  the capture orchestrator, and doc updates (see `git log`).

## 2. Wireshark / USBPcap versions
- Wireshark / tshark / dumpcap **4.6.7** — installed via winget (official
  `WiresharkFoundation.Wireshark`). VERIFIED LIVE.
- **USBPcap — NOT installed.** `dumpcap -D` shows only network (Npcap) interfaces.
  Requires an owner UAC install + reboot. See `CAPTURE_TOOLING.md`.

## 3. Official updater source & identity
- Device resolved as **ANCEL VOD700** (OEM: Autophix). Official software portal:
  `anceltech.com/download.html` (model **VOD700**); product page
  `anceltech.com/product/detail?id=VOD7005984218324582`. See `UPDATER_ACQUISITION.md`.

## 4. Updater SHA-256 & signature
- **UNKNOWN — not acquired.** The "Upgrade Software" is behind account **sign-in**
  ("Available after sign-in", links to `/login.html`). The assistant cannot create
  accounts or authenticate, so it cannot download the gated file. `hash_updater_files.ps1`
  will produce hash/signature/PE data once the owner provides the binary.

## 5. Updater technology
- **UNKNOWN** (binary not available).

## 6. Static-analysis findings
- **BLOCKED** — no binary. Method + search targets are ready in `UPDATER_STATIC_ANALYSIS.md`.

## 7. Captures completed
- **None.** USB capture is impossible without USBPcap.

## 8. Capture hashes
- N/A (no captures).

## 9–15. Packet counts / timeline / heartbeat / command candidates / framing / checksums / correlations
- **BLOCKED BY INSUFFICIENT EVIDENCE.** No packets have been captured, so no
  protocol claims are made. The analyzer, framing/sequence detectors, and
  multi-frame checksum detector are built and unit-tested, waiting for real input.

## 16. Read-only query verified?
- **No.** No capture + no static analysis ⇒ zero verified request bytes. Nothing was
  promoted in `client/policy.py`; all active verbs remain gated (verified this session).

## 17. Active USB request sent?
- **No.** No bytes were sent to any vendor endpoint. Only standard, read-only
  descriptor/pipe reads were performed (re-confirming the device profile).

## 18. Exact active request/response
- N/A — none performed, none approved.

## 19. Tests & quality checks (this session)
- `pytest` **41 passed**; `ruff` clean; `mypy` clean (22 files); wheel **builds**
  (`vod700-0.1.0-py3-none-any.whl`); live `devices`/`endpoints`/`descriptors` OK.
- New capture orchestrator dry-run correctly **refuses** (USBPcap absent).

## 20. Remaining unknowns
- Everything about the wire protocol: framing, command set, checksum, ACK/NACK,
  heartbeat, device-info/version/serial request bytes, bulk/firmware behavior,
  update-container format. All await capture + updater evidence.

## 21. Required owner actions
1. **Install USBPcap** (official source), approve **UAC**, and **reboot**. Then
   `scripts\capture_updater_handshake.ps1 -DryRun` should report ready.
2. **Download the official VOD700 upgrade software** (sign in at
   `anceltech.com/download.html` → VOD700 → Upgrade Software) into
   `private_samples\updater\`.

## 22. Exact next milestone
Once both are provided:
1. `scripts\hash_updater_files.ps1 -Path private_samples\updater` → inventory + hashes.
2. Static-analyze the updater → `UPDATER_STATIC_ANALYSIS.md` (technology, WinUSB
   call sites, endpoint constants, command tables, checksum code).
3. `scripts\capture_updater_handshake.ps1 -UpdaterPath …` → passive handshake pcapng.
4. `vod700 capture analyze` + differential captures → framing/heartbeat/command
   candidates, cross-checked against the static analysis.
5. Only if two independent sources agree, and with owner approval, promote **one**
   read-only identification command in `client/policy.py`.
