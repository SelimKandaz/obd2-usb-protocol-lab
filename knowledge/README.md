# VOD700 Machine-Readable Knowledge Base

The knowledge base is the durable, transport-independent record for future
implementations and ESP32 test fixtures. It contains no proprietary updater,
firmware, raw capture, or raw bulk payload.

| File | Purpose |
|---|---|
| `protocol_knowledge.json` | USB profile, endpoint roles, frame layouts, command catalog, artifact correlation, and implementation boundary |
| `updater_state_machine.json` | Recovered updater states/transitions with trigger, condition, operation, response, failure behavior, evidence, and safety |
| `memory_map.json` | Bounded logical tail-storage windows, unknown regions, and live-read decision |
| `external_sources.json` | Public-source correlation, access date, and limitations |

## Evidence taxonomy

Every important entry uses one of these classifications:

- `PHYSICALLY_VERIFIED`
- `CAPTURE_VERIFIED`
- `DYNAMIC_ANALYSIS_VERIFIED`
- `STATIC_ANALYSIS_SUPPORTED`
- `FIRMWARE_CODE_SUPPORTED`
- `INTERNET_CORRELATED`
- `REPLAY_VERIFIED`
- `INFERRED`
- `UNKNOWN`

Evidence classification is not a confidence rank. A separate `confidence`
field uses `VERIFIED`, `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`, while `safety`
keeps capture-verified but potentially dangerous operations blocked.

## Validate before committing

```powershell
.\.venv\Scripts\python.exe tools\validate_knowledge.py
```

The validator checks JSON syntax, required command evidence, allowed taxonomy,
state-transition references, and public HTTPS source URLs. It does not access
private samples. The full PowerShell verification script runs it automatically.

When adding a discovery:

1. Preserve the raw private evidence only under ignored `private_samples/`.
2. Add the claim and exact source reference here.
3. State the evidence classification, confidence, and safety boundary.
4. Update the related report/doc and add a synthetic regression test.
5. Do not promote a hypothesis merely because a related OEM product looks
   similar.
