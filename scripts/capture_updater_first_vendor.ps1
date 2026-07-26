<#
.SYNOPSIS
    Passive, owner-signaled capture around the first official Update action.
.DESCRIPTION
    Captures the complete selected USBPcap root hub with Update.exe initially
    closed. The owner opens the official updater, then creates the click signal
    only after the controller prints READY. The script never clicks the UI and
    never sends a project-generated USB request.
#>
[CmdletBinding()]
param(
    [string]$UpdaterPath = '',
    [string]$OutPath = '',
    [string]$SignalPath = '',
    [int]$UpdaterWaitSeconds = 90,
    [int]$ClickWaitSeconds = 30,
    [int]$PostClickSeconds = 2
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$usbpcapCmd = 'C:\Program Files\USBPcap\USBPcapCMD.exe'

function Fail($message) { Write-Error $message; exit 1 }
function Get-UpdaterProcess {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            if ($_.Name -ine 'Update.exe') { return $false }
            if ($_.ExecutablePath -and (([IO.Path]::GetFullPath($_.ExecutablePath)) -ieq ([IO.Path]::GetFullPath($UpdaterPath)))) { return $true }
            $_.CommandLine -and ($_.CommandLine -like ('*' + [IO.Path]::GetFileName($UpdaterPath) + '*'))
        }
}
function Get-Vod700 {
    Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
        Where-Object { $_.InstanceId -like '*VID_0483&PID_5265*' } |
        Select-Object -First 1
}

if (-not $UpdaterPath) { $UpdaterPath = Join-Path $repo 'private_samples\updater\Update.exe' }
if (-not $OutPath) { $OutPath = Join-Path $repo 'private_samples\captures\updater_first_vendor.pcap' }
if (-not $SignalPath) { $SignalPath = Join-Path $repo 'private_samples\captures\first_vendor_click.signal' }
if (-not (Test-Path $usbpcapCmd)) { Fail "USBPcapCMD not found: $usbpcapCmd" }
if (-not (Test-Path $UpdaterPath)) { Fail "Updater not found: $UpdaterPath" }
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Fail 'Administrator elevation is required. Re-run this exact script from an elevated PowerShell.'
}
Write-Host ("ELEVATION_OK " + [char]0x2014 + " Administrator token confirmed.")
if (Get-UpdaterProcess) { Fail 'Update.exe is already running; close it before capture.' }
$device = Get-Vod700
if (-not $device -or $device.Status -ne 'OK') { Fail 'VOD700 is not present in Status=Started/OK.' }

$interfaces = & $usbpcapCmd --extcap-interfaces 2>&1 | ForEach-Object {
    if ("$_" -match '^interface \{value=(.+?)\}') { $Matches[1] }
}
$targets = foreach ($interface in $interfaces) {
    & $usbpcapCmd --extcap-interface $interface --extcap-config 2>&1 | ForEach-Object {
        if ("$_" -match '^value \{arg=99\}\{value=(\d+)\}\{display=\[\d+\] WinUsb Device\}') {
            [PSCustomObject]@{ Interface = $interface; Address = [int]$Matches[1] }
        }
    }
}
if (@($targets).Count -ne 1) { Fail "Expected one USBPcap WinUSB target; found $(@($targets).Count)." }
$interface = @($targets)[0].Interface
$usbAddress = @($targets)[0].Address

$outDir = Split-Path -Parent $OutPath
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Remove-Item -LiteralPath $SignalPath -Force -ErrorAction SilentlyContinue
$cap = $null
try {
    # USBPcapCMD rejects 4096 as the lower-bound buffer value. Use its
    # documented default-sized kernel buffer and a full USB snapshot length.
    $captureArgs = '-d "{0}" -A -o "{1}" -s 65535 -b 1048576' -f $interface, $OutPath
    $cap = Start-Process -FilePath $usbpcapCmd -ArgumentList $captureArgs -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if ($cap.HasExited) { Fail 'USBPcapCMD exited before updater launch.' }
    Write-Host ("CAPTURE_ACTIVE " + [char]0x2014 + " OPEN THE OFFICIAL UPDATER AND STOP BEFORE CLICKING UPDATE")
    Write-Host "USBPcap interface=$interface; dynamically selected address=$usbAddress; complete root hub; injection=disabled"
    Write-Host "click signal path=$SignalPath"

    $deadline = (Get-Date).AddSeconds($UpdaterWaitSeconds)
    $updater = $null
    while ((Get-Date) -lt $deadline) {
        $updater = Get-UpdaterProcess | Select-Object -First 1
        if ($updater) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $updater) { Fail 'Update.exe was not detected before timeout.' }
    Start-Sleep -Seconds 3
    Write-Host ("READY " + [char]0x2014 + " CLICK UPDATE ONCE NOW")

    $clickDeadline = (Get-Date).AddSeconds($ClickWaitSeconds)
    while ((Get-Date) -lt $clickDeadline -and -not (Test-Path $SignalPath)) {
        Start-Sleep -Milliseconds 100
    }
    if (-not (Test-Path $SignalPath)) { Fail 'Owner click signal was not received; no button action was performed.' }
    Remove-Item -LiteralPath $SignalPath -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds $PostClickSeconds
    Write-Host ("CLICK_SIGNAL_RECEIVED " + [char]0x2014 + " containing updater and stopping capture.")
    try { Stop-Process -Id $updater.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
}
finally {
    if ($cap) {
        try { Wait-Process -Id $cap.Id -Timeout 3 -ErrorAction SilentlyContinue } catch { }
        $cap.Refresh()
        if (-not $cap.HasExited) { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue }
    }
}

if (-not (Test-Path $OutPath)) { Fail "Capture file was not created: $OutPath" }
$item = Get-Item -LiteralPath $OutPath
if ($item.Length -le 24) { Fail "Capture is header-only or empty: $OutPath" }
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutPath).Hash
Write-Host ("CAPTURE_OK " + [char]0x2014 + " path=$OutPath size=$($item.Length) sha256=$hash")
Write-Host 'No independent vendor request was sent by this controller.'
