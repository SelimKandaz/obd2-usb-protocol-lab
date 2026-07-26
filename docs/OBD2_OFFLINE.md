# Offline OBD-II / ISO-TP Support

The repository includes a transport-neutral OBD-II codec under
`src/vod700/obd2/`. It is deliberately separate from the VOD700 WinUSB
protocol: the captures prove the updater's USB framing, but they do not prove
that the VOD700 vendor endpoints are a CAN/OBD-II bridge.

## Supported offline operations

- strict classical-CAN `ID#DATA` parsing (11-bit and 29-bit IDs)
- ISO-TP single-frame and first/consecutive-frame reassembly
- ISO-TP fixture fragmentation and flow-control metadata parsing
- common SAE J1979 Mode 01 PID formulas (coolant, RPM, speed, MAF, throttle,
  temperatures, pressure, fuel level, runtime, and voltage)
- supported-PID bitmaps
- Mode 03 diagnostic trouble-code decoding
- Mode 09 PID 02 VIN decoding
- CLI decoding of captured frames without opening WinUSB:

```powershell
vod700 obd2 decode "7E8#04410C1AF8000000"
```

The example decodes an engine-RPM response. Multi-frame payloads can be passed
as multiple quoted `ID#DATA` arguments and are reassembled in order.

## Explicit boundary

This module has no CAN socket, serial adapter, WinUSB write, ECU request
builder, DTC-clear operation, or vehicle workflow. It cannot and does not send
diagnostic traffic. Adding a live OBD-II transport would require independent
evidence for the VOD700's vehicle-side bridge and a separate safety review.
