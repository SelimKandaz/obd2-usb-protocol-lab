# Device Profile — ANCEL / Autophix VOD700

All values below are **VERIFIED** on the research host unless tagged otherwise.
Sources: Windows PnP enumeration (`pnputil`, `Get-PnpDevice`) and a live,
read-only WinUSB descriptor read (`vod700 descriptors`, `vod700 endpoints`).

## Identity (USB device descriptor — live read)

| Field              | Value                          | Confidence |
|--------------------|--------------------------------|------------|
| idVendor           | `0x0483` (STMicroelectronics)  | VERIFIED   |
| idProduct          | `0x5265`                       | VERIFIED   |
| bcdUSB             | `2.00`                         | VERIFIED   |
| bcdDevice          | `2.00` (REV_0200)              | VERIFIED   |
| bDeviceClass       | `0x00` (per-interface classes) | VERIFIED   |
| bDeviceSubClass    | `0x00`                         | VERIFIED   |
| bDeviceProtocol    | `0x00`                         | VERIFIED   |
| bMaxPacketSize0    | `64`                           | VERIFIED   |
| bNumConfigurations | `1`                            | VERIFIED   |
| iManufacturer (1)  | `Autophix`                     | VERIFIED   |
| iProduct (2)       | `Automotive Diagnostic Device` | VERIFIED   |
| iSerialNumber (3)  | `Autophix DM`                  | VERIFIED   |

Notes:
- The serial string is a **fixed label**, identical across units of this model
  (not a per-unit serial). Windows renders it `Autophix_DM` in the instance ID
  because instance IDs cannot contain spaces.
- VID `0x0483` is STMicroelectronics → the device is almost certainly an
  **STM32**-class MCU (STRONG INFERENCE). This does not by itself imply any
  particular application protocol.

## Windows binding

| Property           | Value                                         | Confidence |
|--------------------|-----------------------------------------------|------------|
| Instance ID        | `USB\VID_0483&PID_5265\AUTOPHIX_DM`           | VERIFIED   |
| Device description  | `Automotive Diagnostic Device`               | VERIFIED   |
| Service / driver   | `WINUSB` / `winusb.inf` (Microsoft)           | VERIFIED   |
| Driver version     | `10.0.26100.8875`                             | VERIFIED   |
| Compatible ID      | `USB\MS_COMP_WINUSB`                           | VERIFIED   |
| Config string      | `winusb.inf:USB\MS_COMP_WINUSB,WINUSB.NT`     | VERIFIED   |

The device requests WinUSB automatically via Microsoft OS descriptors
(`MS_COMP_WINUSB`); no third-party driver is involved. This is why a custom
read-only client can talk to it without replacing anything.

## Device-interface GUIDs

| GUID                                     | Meaning                              |
|------------------------------------------|--------------------------------------|
| `{f70242c7-fb25-443b-9e7e-a4260f373982}` | vendor interface GUID #1 (app-facing)|
| `{dee824ef-729b-4a0e-9c14-b7117d33a817}` | vendor interface GUID #2             |
| `{a5dcbf10-6530-11d2-901f-00c04fb951ed}` | generic `GUID_DEVINTERFACE_USB_DEVICE` |

Both vendor GUIDs resolve to the same underlying device/endpoints. The official
updater presumably opens one of the vendor GUIDs (to be confirmed by static
analysis of the updater).

## Endpoints
See [`USB_ENDPOINTS.md`](USB_ENDPOINTS.md).

## Redaction
Machine-specific identifiers (BIOS device path, USB topology siblings, physical
location, host username) are intentionally **omitted** from this committed
document. They add nothing to the protocol and identify the research host.
