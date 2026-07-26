# Internet and Related-Hardware Correlation

Date accessed: 2026-07-26

Machine-readable source record: [`knowledge/external_sources.json`](../knowledge/external_sources.json).
No proprietary updater, firmware image, capture, or binary hash was uploaded to
a public analysis service during this research.

## Useful public correlations

| Source | What it supports | What it does not support |
|---|---|---|
| [Official ANCEL VOD700 product page](https://www.ancel.com/products/ancel-vod700) | VOD700 publicly advertises a Feedback Function. That aligns with the updater's `Feedback.bin` worker. | USB commands, tail addresses, feedback file format, or MCU identity. |
| [Official VOD700 product/download page](https://www.anceltech.com/product/detail?id=VOD7005984218324582) | Public VOD700 upgrade software and manual are offered. | Hash/provenance of the local package, protocol behavior. |
| [Related ANCEL AD410 teardown](https://www.allaboutcircuits.com/news/teardown-tuesday-vehicle-code-reader-check-engine-light-OBDII-scan-tool/) | A related AD410 board used a GD32F103, serial flash, and CAN hardware; the local updater contains AD410/DM100 OEM-ANCEL build references. | That the VOD700 is an AD410 board, has the same MCU/flash, or uses its protocol. |
| [GigaDevice GD32F103 page](https://www.gigadevice.com/product/mcu/main-stream-mcus/gd32f10x-series/gd32f103) | USB FS and CAN 2.0B capabilities are compatible with the related-board hypothesis. | Any VOD700 component identification. |
| [ST USB library manual](https://www.st.com/resource/en/user_manual/cd00289278-stm32f105xx-stm32f107xx-stm32f2xx-and-stm32f4xx-usb-on-the-go-host-and-device-library-stmicroelectronics.pdf) | Stock ST USB/DFU context for VID `0x0483`. | A match to VOD700, which exposes a vendor-specific WinUSB interface/PID `0x5265`, not a demonstrated stock DFU endpoint. |
| [libusb Windows USB status definition](https://android.googlesource.com/platform/external/libusb/+/refs/heads/pie-arc/libusb/os/windows_usbdk.c) | `0xC0010000` is `USBD_STATUS_CANCELED`, matching contained capture IRPs. | The reason a particular VOD700 operation was cancelled. |

## Result of targeted searches

Searches combined `VOD700`, `Update.exe`, `DM100UpdateCustom_OEM_ANCEL`,
`McuCode.bin`, `Autophix`, and `0483:5265`. This pass found no authoritative
public VOD700 protocol specification, public updater source, PCB teardown,
firmware-container specification, matching Linux driver, or confirmed OEM
clone with the same USB PID.

The static updater build path `DM100UpdateCustom_OEM_ANCEL` and `AD410 Update
Tool` metadata make a shared OEM lineage a **useful hypothesis**, not a hardware
identity conclusion. The 32 MiB updater capacity is not evidence that a
related AD410 teardown's flash arrangement applies to VOD700.

## Working architecture hypothesis

**INFERRED, not verified:** the VOD700 is likely an embedded diagnostic-tool
platform with a USB-capable microcontroller, nonvolatile application/database
storage, and automotive-bus hardware. That is compatible with the product role
and related-hardware literature, but there is no VOD700 board inspection,
decoded firmware, or component marking to promote the hypothesis.

The highest-value evidence to resolve this is a non-invasive board-marking
inspection or a safely acquired, independently validated read-only storage
artifact—not a guessed USB command or firmware update.
