<#
.SYNOPSIS
    Show the VOD700 interface/endpoint map (read-only).
.DESCRIPTION
    Preferred path: invoke the Python read-only client, which queries the live
    device via WinUsb_QueryPipe (standard, read-only). If Python/package are not
    available, prints the endpoint map recorded during initial enumeration
    (VERIFIED on the research host — see docs/USB_ENDPOINTS.md).
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\get_vod700_endpoints.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }

if ($python) {
    Write-Output "Querying live device via Python read-only client (WinUsb_QueryPipe)..."
    & $python.Source -m vod700 endpoints
    if ($LASTEXITCODE -eq 0) { return }
    Write-Warning "Live query unavailable (exit $LASTEXITCODE). Showing recorded map instead."
}

@"
Recorded endpoint map (VERIFIED on research host; see docs/USB_ENDPOINTS.md)
Interface 0, Alternate Setting 0, Class/Sub/Proto = 0xFF/0xFF/0x00, 4 endpoints

  0x81  IN   Interrupt  maxpkt=16  interval=1
  0x01  OUT  Interrupt  maxpkt=16  interval=1
  0x82  IN   Bulk       maxpkt=64  interval=32
  0x02  OUT  Bulk       maxpkt=64  interval=32

Working hypothesis (UNVERIFIED): 0x01/0x81 = command/status/ACK,
                                 0x02/0x82 = data/file/firmware transfer.
"@ | Write-Output
