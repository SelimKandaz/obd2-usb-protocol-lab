# VOD700 Protocol Knowledge Base

`protocol_knowledge.json` is the compact, machine-readable record of the
current protocol evidence. It is intended to be usable when implementing a
compatible ESP32-side simulator or test fixture without rediscovering the
USB framing.

Every entry carries a confidence/safety boundary. `PHYSICAL_VERIFIED` means an
isolated exchange was observed on the owned VOD700; `CAPTURE_VERIFIED` means a
genuine USBPcap record; `STATIC_CORRELATED` means updater code independently
matches the bytes. A semantic interpretation is never promoted merely because
the byte layout is known.

The knowledge base contains no proprietary firmware, updater binary, or raw
capture. Private capture names are references to local ignored fixtures only.
When adding a discovery, update both this JSON and the narrative reports, add a
regression test, and state whether an ESP32 implementation may safely use it.
