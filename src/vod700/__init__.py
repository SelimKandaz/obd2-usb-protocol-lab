"""VOD700 Protocol Lab — read-only, evidence-driven USB protocol research tools.

Nothing in this package writes to the device beyond standard, read-only USB
descriptor requests. Any command that would send bytes to a vendor endpoint is
gated behind :mod:`vod700.client.policy` and disabled until verified.
"""
from __future__ import annotations

__version__ = "0.1.0"

# Device identity — VERIFIED from local Windows WinUSB/PnP enumeration.
VENDOR_ID = 0x0483  # STMicroelectronics
PRODUCT_ID = 0x5265
DEVICE_REV = 0x0200

# Device interface GUIDs registered by the WinUSB binding (from PnP dump).
INTERFACE_GUIDS = (
    "{f70242c7-fb25-443b-9e7e-a4260f373982}",
    "{dee824ef-729b-4a0e-9c14-b7117d33a817}",
)

__all__ = ["__version__", "VENDOR_ID", "PRODUCT_ID", "DEVICE_REV", "INTERFACE_GUIDS"]
