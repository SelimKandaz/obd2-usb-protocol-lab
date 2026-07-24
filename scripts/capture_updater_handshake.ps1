<#
.SYNOPSIS
    Safe, bounded passive USB capture of the official updater DETECTING the VOD700.
.DESCRIPTION
    Orchestrates a *passive* handshake capture and refuses to do anything unsafe:

      * It launches the official updater EXE with NO arguments and closes it.
      * It NEVER clicks/keys Update/Upgrade/Download/Recover/Flash controls.
      * It NEVER passes update-related command-line switches.
      * Capture is time-bounded (dumpcap self-stops via -a duration).

    The script REFUSES to run if USBPcap is not installed, if the VOD700 is not
    present, or if the updater path is missing. Use -DryRun to validate the
    environment and print the plan without capturing or launching anything.

    Raw capture is written under private_samples\captures\ (git-ignored). Safe
    derived reports go to reports\ (the *_packets.* / *_timeline.md outputs are
    also git-ignored because they can reflect private capture contents).
.PARAMETER UpdaterPath
    Path to the official updater executable (inside private_samples\updater\...).
.PARAMETER DurationSeconds
    How long to capture while the updater is open and idle (default 18).
.PARAMETER DryRun
    Validate environment + print the plan; do not capture or launch anything.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\capture_updater_handshake.ps1 -DryRun
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\capture_updater_handshake.ps1 -UpdaterPath "private_samples\updater\Update.exe"
#>
[CmdletBinding()]
param(
    [string]$UpdaterPath,
    [int]$DurationSeconds = 18,
    [string[]]$CaptureInterface,
    [string]$OutDir,
    [switch]$SkipAnalyze,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$dumpcap = 'C:\Program Files\Wireshark\dumpcap.exe'
$usbpcapCmd = 'C:\Program Files\USBPcap\USBPcapCMD.exe'

function Fail($msg) { Write-Error $msg; exit 1 }

# --- 1. VOD700 present? --------------------------------------------------
$dev = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.InstanceId -like '*VID_0483&PID_5265*' }
if (-not $dev) { Fail "VOD700 (VID_0483&PID_5265) is not connected. Connect it by USB (NOT to a vehicle) and retry." }
$address = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName 'DEVPKEY_Device_Address' -ErrorAction SilentlyContinue).Data
Write-Host "VOD700 present. Current USB address: $address"

# --- 2. Capture tooling present? -----------------------------------------
if (-not (Test-Path $dumpcap)) { Fail "dumpcap not found at $dumpcap. Install Wireshark." }
if (-not (Test-Path $usbpcapCmd)) {
    Fail @"
USBPcap is not installed, so USB capture is impossible.
Install it (official source: https://desowin.org/usbpcap/ or the Wireshark installer's USBPcap component),
approve the UAC prompt, and REBOOT (the USBPcap driver loads at boot). Then re-run this script.
Npcap (already present) captures network interfaces only, not USB.
"@
}

# --- 3. Determine USBPcap capture interfaces -----------------------------
if (-not $CaptureInterface -or $CaptureInterface.Count -eq 0) {
    $CaptureInterface = (& $dumpcap -D 2>&1 | Select-String -Pattern 'USBPcap' | ForEach-Object {
        ($_ -split '\s+', 2)[1] -replace '^\d+\.\s*', '' -replace '\s+\(.*$', ''
    }) | Where-Object { $_ }
    # Fallback: dumpcap sometimes lists as "\\.\USBPcapN"
    if (-not $CaptureInterface) {
        $CaptureInterface = (& $dumpcap -D 2>&1 | Select-String -Pattern 'USBPcap' | ForEach-Object { ($_ -replace '^\d+\.\s*','' -replace '\s.*$','') })
    }
}
if (-not $CaptureInterface -or $CaptureInterface.Count -eq 0) {
    Fail "No USBPcap capture interface found via 'dumpcap -D'. Confirm USBPcap installed and the machine rebooted."
}
Write-Host "USBPcap interface(s): $($CaptureInterface -join ', ')"

# --- 4. Updater path -----------------------------------------------------
if (-not $DryRun) {
    if (-not $UpdaterPath) { Fail "Provide -UpdaterPath to the official updater EXE (in private_samples\updater\)." }
    if (-not (Test-Path $UpdaterPath)) { Fail "Updater not found: $UpdaterPath" }
    if ([IO.Path]::GetExtension($UpdaterPath).ToLower() -ne '.exe') { Fail "UpdaterPath must be an .exe: $UpdaterPath" }
}

# --- 5. Paths ------------------------------------------------------------
if (-not $OutDir) { $OutDir = Join-Path $repo 'private_samples\captures' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$capturePath = Join-Path $OutDir "handshake_$stamp.pcapng"

# --- 6. Elevation note ---------------------------------------------------
$elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $elevated) { Write-Warning "Not elevated. USBPcap capture usually requires Administrator; if capture is empty, re-run elevated." }

# --- 7. Plan / DryRun ----------------------------------------------------
Write-Host "--------------------------------------------------------------"
Write-Host "PLAN (passive, bounded, no update-UI actions):"
Write-Host "  capture -> $capturePath"
Write-Host "  interfaces -> $($CaptureInterface -join ', ')"
Write-Host "  duration -> $DurationSeconds s (dumpcap self-stops)"
Write-Host "  updater  -> $(if ($DryRun) {'(dry run: not launched)'} else {$UpdaterPath}) [launched with NO arguments]"
Write-Host "--------------------------------------------------------------"
if ($DryRun) { Write-Host "DryRun complete. Environment is ready: USBPcap present, device present."; exit 0 }

# --- 8. Start capture (self-stopping) ------------------------------------
$iArgs = @(); foreach ($i in $CaptureInterface) { $iArgs += @('-i', $i) }
$dumpArgs = $iArgs + @('-w', $capturePath, '-a', "duration:$($DurationSeconds + 4)")
Write-Host "Starting capture..."
$cap = Start-Process -FilePath $dumpcap -ArgumentList $dumpArgs -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2  # let the capture attach

# --- 9. Launch updater (NO arguments; never any update switch) -----------
Write-Host "Launching updater (passive; it should only DETECT the device)..."
$upd = Start-Process -FilePath $UpdaterPath -PassThru
Write-Host "Updater PID $($upd.Id). Waiting $DurationSeconds s for device detection. DO NOT click any update control."

# --- 10. Bounded idle ----------------------------------------------------
Start-Sleep -Seconds $DurationSeconds

# --- 11. Close updater gracefully ----------------------------------------
Write-Host "Closing updater..."
try { $upd.CloseMainWindow() | Out-Null; Start-Sleep -Seconds 3 } catch {}
if (-not $upd.HasExited) { try { Stop-Process -Id $upd.Id -Force -ErrorAction SilentlyContinue } catch {} }

# --- 12. Wait for capture to finish & flush ------------------------------
try { Wait-Process -Id $cap.Id -Timeout 15 -ErrorAction SilentlyContinue } catch {}
if (-not $cap.HasExited) { try { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue } catch {} }
Start-Sleep -Seconds 1

# --- 13. Verify + hash ---------------------------------------------------
if (-not (Test-Path $capturePath) -or (Get-Item $capturePath).Length -eq 0) {
    Fail "Capture file is missing or empty: $capturePath. (USBPcap may need elevation, or the wrong root hub was captured.)"
}
$size = (Get-Item $capturePath).Length
$hash = (Get-FileHash -Algorithm SHA256 -Path $capturePath).Hash
Write-Host "Capture OK: $capturePath ($size bytes)"
Write-Host "SHA-256: $hash"

# --- 14. Analyze ---------------------------------------------------------
if (-not $SkipAnalyze) {
    $py = Join-Path $repo '.venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { $py = 'python' }
    Write-Host "Analyzing capture..."
    $addrArg = @(); if ($address) { $addrArg = @('--address', "$address") }
    & $py -m vod700 capture analyze $capturePath --out (Join-Path $repo 'reports') --prefix "handshake_$stamp" @addrArg
}
Write-Host "Done. Raw capture stays under private_samples\ (git-ignored)."
