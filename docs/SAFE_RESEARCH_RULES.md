# Safe Research Rules

These rules are binding for all work in this repository. They exist to protect
the device, the vehicle, and the integrity of the research.

## Hardware handling
- Keep the VOD700 **disconnected from any vehicle** during protocol research.
- Connect the VOD700 to the desktop **by USB only**.
- Do **not** send ECU commands, read/clear DTCs, or write ECU data.
- Do **not** flash, update, recover, or reboot-to-bootloader the VOD700.
- Do **not** erase or modify device storage.

## Official updater
- Do **not** press Update, Upgrade, Recover, Download, Flash, or Firmware
  buttons in the official updater unless the project owner explicitly approves a
  bounded, controlled capture.
- Passive observation (launch → let it detect → close) is the only approved
  interaction for the first capture. See `CAPTURE_HANDSHAKE.md`.

## Driver / OS
- Keep the Microsoft `winusb.inf` driver. Do **not** install Zadig, replace the
  driver, or change the device's driver binding.

## USB traffic
- **No** blind fuzzing.
- **No** replay of unknown packets.
- **No** guessed vendor control transfers.
- **No** bypass of licensing, authentication, signatures, or access controls.

## Promotion of any active request
An active USB request may only be enabled after it is **all** of:
1. **Understood** — every byte accounted for, derived from evidence.
2. **Bounded** — fixed length, known endpoint, known timeout, known max response.
3. **Read-only** — cannot change device state.
4. **Documented** — capture reference + static-analysis reference recorded.
5. **Approved** — the project owner signs off.
6. **Tested first** against a recorded fixture or the mock device.

This is enforced in code by `src/vod700/client/policy.py`. The gate refuses any
command missing any of the above.

## Data hygiene / Git
Never commit:
- official updater binaries or installers
- official firmware or update containers
- proprietary resources
- unredacted PCAP captures
- personal paths, usernames, or device secrets
- private logs
- decompiler project databases
- large binary files

Proprietary material and private captures live **only** in the local, untracked
`private_samples/` directory. See `PRIVATE_SAMPLES.md`.

## Confidence discipline
Never write "the protocol does X" from a single observation. Tag every claim:
`VERIFIED · HIGH · MEDIUM · LOW · UNKNOWN`, and require multiple independent
sources before promoting to VERIFIED.
