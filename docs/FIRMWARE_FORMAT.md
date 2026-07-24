# Firmware / Update Container Format

Status: **BLOCKED** — no updater or firmware sample is present on the research
host. This document defines the *approach* so analysis can start the moment a
sample is placed in `private_samples/firmware/`.

## Hard rules
- **Static analysis only.** A firmware/update file is never sent to the device.
- **Do not** attempt to defeat encryption, signatures, or access controls.
- **Do not** commit or publish proprietary firmware contents.

## What to determine (static)
- container header / magic bytes
- file/format version
- target device identifiers (expect `VID_0483` / `PID_5265` / `Autophix` / model)
- region / language fields
- payload length(s) and section table
- compression indicators (zlib `78 9C`, gzip `1F 8B`, LZMA, etc.)
- encryption indicators (high uniform entropy, absence of ASCII strings)
- checksums / signatures / certificates / manifests
- firmware version string(s)
- bootloader vs. application separation

## Method
1. `scripts\hash_updater_files.ps1 -Path private_samples\firmware` → inventory +
   SHA-256 + PE arch + signatures for any bundled tools.
2. Entropy scan (planned `tools/entropy.py`): sliding-window Shannon entropy to
   flag compressed/encrypted regions vs. plaintext headers.
3. Magic/signature scan and `strings` over the container (never executed).
4. Header diff across multiple official versions if more than one is available.
5. Record findings in `reports/FIRMWARE_CONTAINER_ANALYSIS.md` with confidence
   tags and **no** raw proprietary bytes (offsets/lengths/entropy only).

## STM32 context (STRONG INFERENCE)
VID `0x0483` implies an STM32 MCU. Vendors commonly ship either a raw/patched
application image or a vendor-wrapped container over the top. If the device ever
exposes ST's DFU interface (a different PID, typically `0xDF11`) that is a
separate mode and **out of scope** for this read-only project.
