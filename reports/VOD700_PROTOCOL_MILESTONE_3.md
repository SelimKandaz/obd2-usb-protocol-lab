# VOD700 Protocol - Milestone 3

Date: 2026-07-24

## Outcome

Milestone 3 completed the updater static analysis and one owner-approved,
bounded passive updater run. The run produced a valid 560-byte PCAPNG but no
updater-generated USB traffic. Only the synthetic descriptors injected by
USBPcap at capture start were present.

No independent vendor request was sent, no updater control was clicked, no
firmware image was used, and no driver was installed or replaced.

## Repository and runtime gate

- Starting HEAD: `186de78718f69005cd2fa8047c3cc04d0e1bf55d`
- Initial branch/worktree: `main`, clean
- VOD700: present, PnP `Status=Started`, CIM `Status=OK`, `WINUSB`
- Updater: official `Update.exe`, launched with no arguments
- Passive interval: 18 seconds
- UI activity: none
- Updater shutdown: `CloseMainWindow` succeeded

## Dynamic USB mapping

Windows reported `DEVPKEY_Device_Address=9` at
`Port_#0009.Hub_#0001`. USBPcap's extcap device tree independently mapped the
single WinUSB target to device address 4 on `\\.\USBPcap1`. The orchestrator now
discovers this mapping dynamically instead of using the Windows hub-port value
as a USBPcap address.

## Capture artifact

- Path:
  `private_samples\captures\handshake_20260724_150600.pcapng`
- SHA-256:
  `4CEC0D3B43DB4BE12F5B8F6BCBC43446E46E4A49F49B66E685AC856748D80D3F`
- Size: 560 bytes
- Native analyzer records: 6 synthetic records
- Corrected logical live updater transfers: 0

Endpoint counts:

| Endpoint | Records | Live updater transfers |
|---|---:|---:|
| endpoint 0 control | 6 | 0 |
| `0x01` interrupt OUT | 0 | 0 |
| `0x81` interrupt IN | 0 | 0 |
| `0x02` bulk OUT | 0 | 0 |
| `0x82` bulk IN | 0 | 0 |

All six records share IRP ID zero and a single capture-start timestamp. They
correlate into injected device-descriptor, configuration-descriptor, and
set-configuration pairs. They are not updater submit/completion URBs.

## Static/dynamic correlation

Static analysis remains strong for:

- WinUSB open/read/write paths
- dynamic endpoint discovery
- 16-byte interrupt OUT and IN transfers
- request prefix `55 AA`
- additive request checksum
- possible command bytes `0x0B`, `0x06`, `0x07`, `0x03`, and `0x0A`

The capture dynamically confirms only the standard descriptors and four
endpoint declarations. It does not correlate a vendor command, response,
heartbeat, checksum instance, or bulk transfer. `0x0B` and `0x06` did not
appear.

## Safety decision

No safe read-only request candidate meets the required independent static and
passive-capture threshold. The client policy is unchanged. The project stops
before the first independent active vendor request.
