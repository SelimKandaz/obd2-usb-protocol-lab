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

No live `0x0B` or `0x06` request is authorized by this document. No firmware,
erase, bulk OUT, driver replacement, vehicle connection, or replay of the
captured request is authorized.
