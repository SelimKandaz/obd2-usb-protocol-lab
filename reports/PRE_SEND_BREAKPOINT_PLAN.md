# Pre-Send Breakpoint Plan

Date: 2026-07-24

## Status: PREPARED, NOT EXECUTED

This is a containment plan only. It has not been attached to `Update.exe`, the
Update button has not been clicked, and no vendor payload has been transmitted.

## Target

- Tool: x32dbg or another trusted x86 user-mode debugger
- Module: official `Update.exe`, SHA-256
  `F705FB6C6276FA52F75DD88269408D5CF061048F5EEB5451212EB1986D862C4D`
- Architecture: PE32 x86, image base `0x00400000`
- Process state: launch suspended; do not resume through a button-handler path

## Breakpoints before any possible device write

1. `WinUsb_WritePipe` imported API (symbol/API breakpoint)
2. static write wrapper `Update.exe+0x00009AB0` (`0x00409AB0` at the preferred
   image base)
3. interrupt transaction helper `Update.exe+0x00010010`
4. bulk-write builder/call path `Update.exe+0x00011330`

Static analysis found no `WinUsb_ControlTransfer` or `DeviceIoControl` import.
Any additional `WriteFile` breakpoint must be limited to the updater process
and reviewed to distinguish firmware-file output from device I/O.

## Inspection and termination

At the first `WinUsb_WritePipe` breakpoint, inspect the x86 calling convention:
the API arguments are the WinUSB interface handle, pipe ID, buffer pointer,
buffer length, transferred-length pointer, and overlapped pointer. Do not step
over the call. Dump the buffer and length, record the selected pipe, then
terminate the suspended process. Do not detach/resume it.

The exact MFC handlers are now recovered for `Update` (control ID 1) and
`Feedback` (control ID 1005), but that coverage is still not proof that a
request is safe. Custom wrapper callers, the Review & Print UI edge, and all
dangerous stage semantics remain incomplete. This plan must not be executed
without explicit owner approval.
