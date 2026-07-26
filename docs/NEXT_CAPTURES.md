# Next Captures

The first updater transaction is now canonicalized at
`private_samples/captures/updater_first_vendor.pcapng`; do not repeat it.

The next evidence target is the boundary after the observed preliminary
`0x06`/bulk-IN reads. Any future capture must be separately approved and must
stop before `0x02` bulk OUT or firmware transfer. The existing controller now
contains the updater on the first USB record, so it is suitable only for a
newly scoped scenario after changing its capture label and output path.

Before any live command execution:

1. Validate the new parser/builders against the private replay fixture.
2. Review the exact request, response, timeout, maximum length, and risk.
3. Obtain explicit owner approval for one command.
4. Exercise the command against the mock/replay device first.

The `0x0B`/`0x8B` query has now been validated once on the physical device and
must not be repeated as a baseline. `0x06`, bulk OUT, firmware, erase, driver
replacement, vehicle connection, and replay of update-stage traffic remain
unauthorized. Any future capture must target a distinct unknown command or
state and requires a separate explicit approval.

For a future bounded passive capture, the controller launches `Update.exe`
itself with `private_samples/updater` as the working directory. Do not launch
a second copy manually; this avoids the `C:\Windows\System32\bin\McuCode.bin`
working-directory failure.
