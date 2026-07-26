<#
.SYNOPSIS
    Passive, owner-signaled capture around the first official Update action.
.DESCRIPTION
    Captures the complete selected USBPcap root hub with Update.exe initially
    closed. The controller launches the official updater with its package
    directory as the working directory. The owner clicks Update once only
    after READY. The controller then observes a bounded window and contains
    the updater. It never clicks the UI and never sends a project-generated
    USB request.
#>
[CmdletBinding()]
param(
    [string]$UpdaterPath = '',
    [string]$OutPath = '',
    [int]$UpdaterWaitSeconds = 90,
    [int]$PostReadyMaxSeconds = 15
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
            return $false
        }
}
function Get-Vod700 {
    Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
        Where-Object { $_.InstanceId -like '*VID_0483&PID_5265*' } |
        Select-Object -First 1
}

function New-FirstVendorPipeSink {
    param([string]$PipeName, [string]$OutputPath)
    if (-not ('FirstVendorPipeSink' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.IO.Pipes;
using System.Threading;
using System.Threading.Tasks;

public sealed class FirstVendorPipeSink : IDisposable
{
    private readonly NamedPipeServerStream pipe;
    private readonly FileStream output;
    private readonly ManualResetEventSlim connected = new ManualResetEventSlim(false);
    private readonly Task pump;
    private bool disposed;

    public FirstVendorPipeSink(string pipeName, string outputPath)
    {
        pipe = new NamedPipeServerStream(pipeName, PipeDirection.In, 1,
            PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
        output = new FileStream(outputPath, FileMode.Create, FileAccess.Write,
            FileShare.Read, 4096, FileOptions.Asynchronous);
        pump = PumpAsync();
    }

    private async Task PumpAsync()
    {
        try
        {
            await pipe.WaitForConnectionAsync().ConfigureAwait(false);
            connected.Set();
            await pipe.CopyToAsync(output).ConfigureAwait(false);
        }
        catch (IOException) { }
        catch (ObjectDisposedException) { }
        finally { try { output.Flush(); } catch { } }
    }

    public bool WaitForConnection(int milliseconds) { return connected.Wait(milliseconds); }

    public void Dispose()
    {
        if (disposed) return;
        disposed = true;
        try { pipe.Dispose(); } catch { }
        try { pump.Wait(TimeSpan.FromSeconds(5)); } catch { }
        try { output.Flush(true); } catch { }
        try { output.Dispose(); } catch { }
        connected.Dispose();
    }
}
'@
    }
    return [FirstVendorPipeSink]::new($PipeName, $OutputPath)
}

if (-not $UpdaterPath) { $UpdaterPath = Join-Path $repo 'private_samples\updater\Update.exe' }
if (-not $OutPath) { $OutPath = Join-Path $repo 'private_samples\captures\updater_first_vendor.pcap' }
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
$cap = $null
$sink = $null
$updaterProcess = $null
try {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $pipeName = "vod700_first_vendor_$stamp"
    $sink = New-FirstVendorPipeSink -PipeName $pipeName -OutputPath $OutPath
    $captureArgs = '--extcap-interface "{0}" --fifo "{1}" --capture --capture-from-all-devices' -f $interface, "\\.\pipe\$pipeName"
    $cap = Start-Process -FilePath $usbpcapCmd -ArgumentList $captureArgs -PassThru -WindowStyle Hidden
    if (-not $sink.WaitForConnection(5000)) {
        if (-not $cap.HasExited) { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue }
        Fail 'USBPcapCMD did not connect to the named-pipe capture sink.'
    }
    Start-Sleep -Seconds 2
    if ($cap.HasExited) { Fail 'USBPcapCMD exited before updater launch.' }
    Write-Host ("CAPTURE_ACTIVE " + [char]0x2014 + " OFFICIAL UPDATER WILL BE LAUNCHED IN ITS PACKAGE DIRECTORY; STOP BEFORE CLICKING UPDATE")
    Write-Host "USBPcap interface=$interface; dynamically selected address=$usbAddress; complete root hub; injection=disabled"
    $updaterDir = Split-Path -Parent $UpdaterPath
    Write-Host "updater working directory=$updaterDir"
    $updaterProcess = Start-Process -FilePath $UpdaterPath -WorkingDirectory $updaterDir -ArgumentList @() -PassThru -WindowStyle Normal
    Write-Host "updater launch requested with no arguments; pid=$($updaterProcess.Id)"

    $deadline = (Get-Date).AddSeconds($UpdaterWaitSeconds)
    $updaterInfo = $null
    while ((Get-Date) -lt $deadline) {
        $updaterInfo = Get-UpdaterProcess | Select-Object -First 1
        if ($updaterInfo) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $updaterInfo) { Fail 'Update.exe was not detected before timeout.' }
    Write-Host "official updater detected=$($updaterInfo.ExecutablePath)"
    Start-Sleep -Seconds 3
    Write-Host ("READY " + [char]0x2014 + " CLICK UPDATE ONCE NOW")
    Write-Host ("POST_READY_WINDOW " + [char]0x2014 + " observing until the first USB record or $PostReadyMaxSeconds seconds; do not click anything else.")
    $firstRecordDeadline = (Get-Date).AddSeconds($PostReadyMaxSeconds)
    $firstRecordObserved = $false
    while ((Get-Date) -lt $firstRecordDeadline) {
        if ((Test-Path $OutPath) -and ((Get-Item -LiteralPath $OutPath).Length -gt 24)) {
            $firstRecordObserved = $true
            break
        }
        Start-Sleep -Milliseconds 100
    }
    if ($firstRecordObserved) {
        Write-Host ("FIRST_USB_RECORD_OBSERVED " + [char]0x2014 + " containing updater immediately.")
    } else {
        Write-Host ("POST_READY_TIMEOUT " + [char]0x2014 + " no USB record observed; containing updater.")
    }
    try { $updaterProcess.CloseMainWindow() | Out-Null; Start-Sleep -Seconds 3 } catch { }
    if (-not $updaterProcess.HasExited) { try { Stop-Process -Id $updaterProcess.Id -Force -ErrorAction SilentlyContinue } catch { } }
    $sink.Dispose()
    $sink = $null
    try { Wait-Process -Id $cap.Id -Timeout 5 -ErrorAction SilentlyContinue } catch { }
}
finally {
    if ($updaterProcess) {
        try { $updaterProcess.Refresh() } catch { }
        if (-not $updaterProcess.HasExited) {
            try { $updaterProcess.CloseMainWindow() | Out-Null; Start-Sleep -Seconds 2 } catch { }
            if (-not $updaterProcess.HasExited) { try { Stop-Process -Id $updaterProcess.Id -Force -ErrorAction SilentlyContinue } catch { } }
        }
    }
    if ($sink) {
        try { $sink.Dispose() } catch { }
    }
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
