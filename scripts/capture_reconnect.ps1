<#
.SYNOPSIS
    Bounded passive USBPcap baseline for a VOD700 disconnect/reconnect.
.DESCRIPTION
    Captures the complete dynamically selected VOD700 root hub with USBPcap
    descriptor injection disabled. The script waits for the owner to unplug
    the USB-only device, observes it disappear and return as Started, then
    captures five additional seconds. It never launches the updater and never
    sends a vendor-protocol request.
#>
[CmdletBinding()]
param(
    [string]$OutPath = '',
    [int]$DisconnectWaitSeconds = 60,
    [int]$ReconnectWaitSeconds = 60,
    [int]$PostReconnectSeconds = 5,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$usbpcapCmd = 'C:\Program Files\USBPcap\USBPcapCMD.exe'
$editcap = 'C:\Program Files\Wireshark\editcap.exe'

function Fail($message) { Write-Error $message; exit 1 }

function Get-Vod700 {
    Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
        Where-Object { $_.InstanceId -like '*VID_0483&PID_5265*' } |
        Select-Object -First 1
}

function Test-Vod700Started {
    $device = Get-Vod700
    if (-not $device) { return $false }
    return $device.Status -eq 'OK'
}

function New-UsbPcapPipeSink {
    param([string]$PipeName, [string]$OutputPath)
    if (-not ('ReconnectPipeSink' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.IO.Pipes;
using System.Threading;
using System.Threading.Tasks;

public sealed class ReconnectPipeSink : IDisposable
{
    private readonly NamedPipeServerStream pipe;
    private readonly FileStream output;
    private readonly ManualResetEventSlim connected = new ManualResetEventSlim(false);
    private readonly Task pump;
    private bool disposed;

    public ReconnectPipeSink(string pipeName, string outputPath)
    {
        pipe = new NamedPipeServerStream(pipeName, PipeDirection.In, 1,
            PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
        output = new FileStream(outputPath, FileMode.CreateNew, FileAccess.Write,
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
    return [ReconnectPipeSink]::new($PipeName, $OutputPath)
}

if (-not (Test-Path $usbpcapCmd)) { Fail "USBPcapCMD not found: $usbpcapCmd" }
if (-not (Test-Path $editcap)) { Fail "editcap not found: $editcap" }
$device = Get-Vod700
if (-not $device) { Fail 'VOD700 is not present. Connect it by USB only.' }
if (-not (Test-Vod700Started)) { Fail 'VOD700 is not in Started/OK state.' }

$pnpLocation = (Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName 'DEVPKEY_Device_LocationInfo' -ErrorAction SilentlyContinue).Data
$pnpAddress = (Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName 'DEVPKEY_Device_Address' -ErrorAction SilentlyContinue).Data
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

Write-Host "VOD700 Started; PnP location=$pnpLocation; PnP address=$pnpAddress"
Write-Host "USBPcap interface=$interface; current USBPcap address=$usbAddress"
Write-Host "Capture mode=complete root hub; descriptor injection=disabled"

if (-not $OutPath) { $OutPath = Join-Path $repo 'private_samples\captures\baseline_reconnect.pcapng' }
$outDir = Split-Path -Parent $OutPath
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$rawPath = Join-Path $outDir "baseline_reconnect_$stamp.pcap"
$pipeName = "vod700_reconnect_$stamp"

if ($DryRun) {
    Write-Host "PLAN: capture=$OutPath; raw=$rawPath; disconnect wait=${DisconnectWaitSeconds}s; reconnect wait=${ReconnectWaitSeconds}s; post=${PostReconnectSeconds}s"
    exit 0
}

$elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $elevated) { Fail 'Reconnect capture requires an elevated PowerShell session. No capture started.' }

$sink = New-UsbPcapPipeSink -PipeName $pipeName -OutputPath $rawPath
$captureArgs = '--extcap-interface "{0}" --fifo "{1}" --capture --capture-from-all-devices' -f $interface, "\\.\pipe\$pipeName"
$cap = Start-Process -FilePath $usbpcapCmd -ArgumentList $captureArgs -PassThru -WindowStyle Hidden
if (-not $sink.WaitForConnection(5000)) {
    $sink.Dispose()
    if (-not $cap.HasExited) { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue }
    Fail 'USBPcapCMD did not connect to the capture sink.'
}
Write-Host 'CAPTURE_ACTIVE: disconnect the VOD700 USB cable now. The script will detect reconnect automatically.'

$gone = $false
$goneDeadline = (Get-Date).AddSeconds($DisconnectWaitSeconds)
while ((Get-Date) -lt $goneDeadline) {
    if (-not (Get-Vod700)) { $gone = $true; break }
    Start-Sleep -Milliseconds 250
}
if (-not $gone) {
    $sink.Dispose(); if (-not $cap.HasExited) { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue }
    Fail 'VOD700 did not disappear during the disconnect window; baseline not accepted.'
}
Write-Host 'DISCONNECT_OBSERVED: waiting for Windows Status=Started after reconnect.'

$back = $false
$backDeadline = (Get-Date).AddSeconds($ReconnectWaitSeconds)
while ((Get-Date) -lt $backDeadline) {
    if (Test-Vod700Started) { $back = $true; break }
    Start-Sleep -Milliseconds 250
}
if (-not $back) {
    $sink.Dispose(); if (-not $cap.HasExited) { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue }
    Fail 'VOD700 did not return to Status=Started during the reconnect window.'
}
Write-Host "RECONNECT_STARTED: waiting $PostReconnectSeconds seconds for enumeration to settle."
Start-Sleep -Seconds $PostReconnectSeconds

$sink.Dispose()
try { Wait-Process -Id $cap.Id -Timeout 5 -ErrorAction SilentlyContinue } catch { }
$cap.Refresh()
if (-not $cap.HasExited) {
    Write-Warning 'USBPcapCMD did not exit after pipe close; force-stopping the verified capture PID.'
    Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue
}
& $editcap $rawPath $OutPath
if ($LASTEXITCODE -ne 0) { Fail "editcap failed converting $rawPath" }
if (-not (Test-Path $OutPath) -or (Get-Item $OutPath).Length -le 24) { Fail "Reconnect capture is missing or header-only: $OutPath" }
$item = Get-Item $OutPath
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutPath).Hash
Write-Host "CAPTURE_OK: $OutPath size=$($item.Length) sha256=$hash"
Write-Host 'No updater was launched and no vendor-protocol request was sent.'
