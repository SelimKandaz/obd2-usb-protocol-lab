# fixtures/synthetic/

**Synthetic** = fabricated for testing. Nothing here is captured from the real
device, so nothing proprietary is embedded.

The canonical synthetic fixtures are built in code by
`src/vod700/mock/fixtures.py`:

- `make_usbpcap_record(...)` — one USBPcap pseudo-header + payload.
- `build_usbpcap_pcapng([(ts_ns, record), ...])` — a valid little-endian pcapng
  (linktype 249) the native reader can round-trip.
- `synthetic_interrupt_transfers()` — a small fabricated interrupt exchange whose
  frames carry a known XOR8 trailing byte (so checksum-detector tests have a
  known-good answer).

Building fixtures in code (rather than committing binary blobs) keeps the repo
text-only and makes the fixtures self-documenting. When a **redacted** real
handshake fixture is eventually approved for commit, it will be added here with a
note describing exactly what was redacted.
