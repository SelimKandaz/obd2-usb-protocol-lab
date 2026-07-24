# Next Passive Captures

The first accepted scenario - device already connected, then updater launched
with no arguments - produced no updater-generated USB traffic during 18 seconds.
Only USBPcap's injected descriptors were present.

No additional capture is authorized by the completed milestone. If the owner
later requests more passive work, the smallest useful next scenarios are:

| Priority | Scenario | Purpose |
|---:|---|---|
| 1 | Start updater, then connect the USB-only device | test whether detection is connect-event driven |
| 2 | Keep updater open and idle for 30 seconds | look for delayed heartbeat/polling |
| 3 | Open a clearly read-only device-information view without update controls | isolate identity/version query |

Every scenario must remain capture-only:

- device disconnected from any vehicle
- updater unmodified and launched with no arguments
- no Update, Upgrade, Download, Recover, Flash, Erase, Write, or Firmware action
- no firmware image opened or used
- no driver replacement
- no replay or independent packet

Use the dynamically discovered USBPcap address, not the Windows
`DEVPKEY_Device_Address` hub-port value. Require at least two stable passive
request/response observations plus matching static evidence before considering
an active read-only proposal.
