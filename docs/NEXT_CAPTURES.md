# Next Captures

The canonical reconnect, preliminary updater transaction, and contained
update-stage capture already exist. Do not repeat them as baselines.

## Highest-value future physical evidence

1. **Passive Feedback workflow capture, no update action.** Use the updater's
   `Feedback` control (dialog ID 1005, statically mapped to worker
   `0x0040DB30`); run a bounded root-hub capture and contain the updater before
   any `0x02` bulk OUT. This can prove the complete 32-page storage-export path
   and its normal termination.
2. **Passive Review & Print workflow capture, no update action.** Capture the
   separate 30-page range at `capacity-0x30000`. It can validate the
   `AUTOPHIX` signature and clarify the opaque post-signature fields.
3. **Non-invasive board-marking inspection.** A clear photo of the main IC and
   flash marking would be much stronger MCU/flash evidence than VID or an OEM
   lineage hypothesis.

## Mandatory safety boundary

- Do not click Update/Upgrade/Download/Recover/Flash/Erase/Write/Firmware.
- Do not replay `0x01`, `0x02`, `0x03`, `0x04`, `0x06`, bulk OUT, or any
  unverified command.
- Do not use `Erase.bin`, `McuCode.bin`, or `ExtFlashDat.bin` in a live flow.
- Keep the device disconnected from a vehicle.
- Do not replace the WinUSB driver or patch the official updater.

`0x0B` is already physically validated and must not be re-run merely as a
baseline. The only possible future active `0x06` experiment requires the
three evidence gates recorded in `knowledge/memory_map.json` plus explicit
owner approval; it is not currently authorized.

For a bounded passive updater capture, launch only the controller-managed
`Update.exe` instance with `private_samples\updater` as its working directory.
Do not start a second copy manually; doing so can recreate the
`C:\Windows\System32\bin\McuCode.bin` working-directory failure.
