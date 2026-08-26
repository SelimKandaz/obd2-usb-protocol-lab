# OBD2 USB Protocol Lab — VOD700 case study

Evidence-driven, **read-only** reverse-engineering tools for USB-connected OBD2
diagnostic devices. The current reference device and detailed case study is
the ANCEL/Autophix VOD700; its evidence remains documented throughout this
repository.

> **Scope of this project is interoperability research and documentation.**
> The immediate goal is *understanding* — descriptors, endpoints, framing,
> handshake, checksums — and eventually an independent **read-only** client
> that can identify the device and read safe metadata. Firmware modification is
> explicitly **out of scope**.

---

## ⚠️ Safety first — read before doing anything

This repository enforces a *passive-first* methodology. The full rules live in
[`docs/SAFE_RESEARCH_RULES.md`](docs/SAFE_RESEARCH_RULES.md). The short version:

- Keep the VOD700 **disconnected from any vehicle**. USB-to-desktop only.
- **No** ECU commands, DTC clears, ECU writes, flashing, or storage changes.
- **No** driver replacement (keep Microsoft `winusb.inf`). No Zadig.
- **No** blind fuzzing, packet replay, or guessed vendor control transfers.
- Every active USB request must be *understood, bounded, read-only, documented,
  approved, and tested against a fixture/mock first.*
- **Never commit** proprietary updater binaries, firmware, or unredacted
  captures. Those live only in the local, untracked `private_samples/`.

Confidence taxonomy used throughout: **VERIFIED · HIGH · MEDIUM · LOW · UNKNOWN**.
Nothing is stated as fact from a single observation.

---

## Verified device facts

Source: local Windows PnP/WinUSB enumeration (`docs/DEVICE_PROFILE.md`,
`docs/USB_ENDPOINTS.md`). These are **VERIFIED** on the research host.

| Property            | Value                                             |
|---------------------|---------------------------------------------------|
| Vendor ID           | `0x0483` (STMicroelectronics)                     |
| Product ID          | `0x5265`                                           |
| bcdUSB              | `2.00`                                             |
| bcdDevice (REV)     | `0x0200`                                            |
| Device class        | `0x00/0x00/0x00` (class deferred to interface)    |
| Interface 0 class   | `0xFF / 0xFF / 0x00` (vendor-specific)            |
| bMaxPacketSize0     | `64`                                               |
| Manufacturer string | `Autophix`                                         |
| Product string      | `Automotive Diagnostic Device`                    |
| Serial string       | `Autophix DM` (fixed; not a unique serial)        |
| Driver              | Microsoft `winusb.inf` (auto via `MS_COMP_WINUSB`)|
| EP `0x81` IN        | Interrupt, 16 B, interval 1                        |
| EP `0x01` OUT       | Interrupt, 16 B, interval 1                        |
| EP `0x82` IN        | Bulk, 64 B, interval 32                            |
| EP `0x02` OUT       | Bulk, 64 B, interval 32                            |

*(Descriptor/string values above were read live from the device via the
read-only WinUSB client — `vod700 descriptors`. Windows shows the serial as
`Autophix_DM` in instance IDs because spaces are not allowed there.)*

**Capture-verified channel roles:** `0x01/0x81` interrupt carries the updater's
request/response exchange; `0x02/0x82` carries bulk data. Individual bulk
payload meanings and the bulk OUT safety boundary remain separate questions.

VID `0x0483` is registered to STMicroelectronics, but it does **not** identify
the VOD700 MCU. The actual MCU, flash layout, and bootloader remain unknown
until supported by board or firmware evidence.

---

## Repository layout

The package also contains `src/vod700/obd2/`, an offline-only CAN/ISO-TP and
SAE J1979 decoder. It is intentionally not connected to the VOD700 USB or a
vehicle.

The machine-readable protocol record is maintained in
[`knowledge/protocol_knowledge.json`](knowledge/protocol_knowledge.json), with
the authoring rules in [`knowledge/README.md`](knowledge/README.md).

```
vod700-protocol-lab/
├─ src/vod700/            # Python package (zero runtime dependencies)
│  ├─ protocol/           # models, checksums, framing, parser
│  ├─ capture/            # native pcapng + USBPcap decoder + exporters
│  ├─ firmware/           # opaque-artifact and release-ZIP analysis only
│  ├─ memory/             # disabled, capture-derived storage plans
│  ├─ client/             # read-only WinUSB client (ctypes) + safety policy
│  └─ mock/               # replay device + synthetic fixture builders
├─ scripts/               # read-only PowerShell discovery tools
├─ docs/                  # device profile, endpoints, capture & safety docs
├─ reports/              # environment + static-analysis + status reports
├─ fixtures/synthetic/    # small, TEXT, non-proprietary test fixtures
├─ captures/              # (empty in git) redacted/synthetic captures only
├─ research/              # working notes + confidence-tagged log
├─ tools/                 # pointers to safe static-analysis tools (no binaries)
├─ tests/                 # pytest suite (no hardware, no firmware writes)
└─ private_samples/       # LOCAL ONLY, git-ignored: updater/firmware/captures
```

## Quickstart

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
vod700 --help
```

Read-only device commands (safe; standard USB requests only):

```bash
vod700 devices          # enumerate VOD700 WinUSB interfaces
vod700 descriptors      # device/config/string descriptors (read-only)
vod700 endpoints        # confirm the endpoint map from the live device
```

Capture analysis (works offline; no tshark required):

```bash
vod700 capture analyze private_samples/captures/handshake.pcapng
vod700 capture transactions private_samples/captures/handshake.pcapng
```

Offline artifact/storage analysis (no device access):

```bash
vod700 firmware inspect private_samples/updater/bin/DM100/McuCode.bin --deep
vod700 memory feedback-plan
```

Offline OBD-II/ISO-TP decoding (no device or vehicle access):

```bash
vod700 obd2 decode "7E8#04410C1AF8000000"
```

Active/query commands (`listen`, `identify`, `version`) are **gated**: they
refuse to run until the underlying request is verified from capture evidence
and enabled in `src/vod700/client/policy.py`.

The verified capacity query is available only as an explicit opt-in:

```bash
vod700 storage-query --approve-live
```

It sends one 16-byte `0x0B` request and validates the 16-byte `0x8B` response;
the default command set sends no vendor-protocol bytes.

## Status

See [`docs/PROTOCOL_STATUS.md`](docs/PROTOCOL_STATUS.md) and
[`reports/VOD700_REVERSE_ENGINEERING_STATUS.md`](reports/VOD700_REVERSE_ENGINEERING_STATUS.md).

The current consolidated status is
[`reports/VOD700_REVERSE_ENGINEERING_STATUS.md`](reports/VOD700_REVERSE_ENGINEERING_STATUS.md).
The private canonical capture proves the `0x0B`/`0x8B` and `0x06`/`0x86`
interrupt exchanges, additive checksums, and bounded bulk-IN frames. A
separate official-updater capture proves the dangerous `0x03`, `0x01`, and
`0x02` update path; it is parser-only and never dispatchable. The full recovered
worker graph is in `reports/UPDATER_STATE_MACHINE.md`.

The independent client now has evidence-backed offline parsers, capture
transaction correlation, opaque-artifact tools, disabled storage plans, and a
policy-gated transport state machine. The dangerous `0x06`/bulk paths remain
unimplemented for dispatch. `storage-query` is disabled by default and
requires explicit approval on every invocation. A separate offline OBD-II
codec is available for captured CAN/ISO-TP data; it is not connected to the
VOD700 USB transport.

## Legal & ethical

Independent interoperability research on a device the operator owns. No bypass of
licensing, authentication, signatures, or access controls; no redistribution of
proprietary firmware or software. See `docs/SAFE_RESEARCH_RULES.md`.

For the repository publication boundary and the local-only artifact policy, see
[`PUBLIC_RELEASE_NOTES.md`](PUBLIC_RELEASE_NOTES.md).
