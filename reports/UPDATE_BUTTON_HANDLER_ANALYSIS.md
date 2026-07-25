# Update Button Handler Analysis

Date: 2026-07-24

## Status: BLOCKED / STATIC MAP NOT YET RECONSTRUCTED

The existing static report verifies WinUSB imports, endpoint selectors, the
16-byte interrupt helper, and dangerous bulk-write code. It does not yet prove
the MFC dialog resource ID, message-map entry, or exact Update-button handler
through cross-references.

No button was clicked, no handler was executed, and no UI command was invoked.
The following static facts are safe to carry forward:

- x86 native MFC executable
- interrupt helper at `0x00410010`
- WinUSB write wrapper at `0x00409AB0`
- dangerous bulk-write path at `0x00411330`
- no imported `WinUsb_ControlTransfer` or `DeviceIoControl`

The exact control ID, handler address, caller chain, worker-thread start, and
first reachable write remain UNKNOWN until resource/message-map cross-references
are completed. Nearby strings alone must not be used to identify the handler.
