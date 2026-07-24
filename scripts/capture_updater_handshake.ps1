<#
.SYNOPSIS
    Safe, bounded passive USB capture of the official updater DETECTING the VOD700.
.DESCRIPTION
    Orchestrates a *passive* handshake capture and refuses to do anything unsafe:

      * It launches the official updater EXE with NO arguments and closes it.
      * It NEVER clicks/keys Update/Upgrade/Download/Recover/Flash controls.
      * It NEVER passes update-related command-line switches.
      * Capture is time-bounded (dumpcap self-stops; direct USBPcapCMD is stopped
        immediately after the bounded updater-idle interval).

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
    [Alias('CaptureDuration')]
    [int]$DurationSeconds = 18,
    [string[]]$CaptureInterface,
    [string]$OutDir,
    [switch]$SkipAnalyze,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$dumpcap = 'C:\Program Files\Wireshark\dumpcap.exe'
$editcap = 'C:\Program Files\Wireshark\editcap.exe'
$usbpcapCmd = 'C:\Program Files\USBPcap\USBPcapCMD.exe'

function Fail($msg) { Write-Error $msg; exit 1 }

function New-UsbPcapPipeSink {
    param(
        [string]$PipeName,
        [string]$OutputPath
    )

    if (-not ('UsbPcapPipeSink' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.IO.Pipes;
using System.Threading;
using System.Threading.Tasks;

public sealed class UsbPcapPipeSink : IDisposable
{
    private readonly NamedPipeServerStream pipe;
    private readonly FileStream output;
    private readonly ManualResetEventSlim connected = new ManualResetEventSlim(false);
    private readonly Task pump;
    private bool disposed;

    public UsbPcapPipeSink(string pipeName, string outputPath)
    {
        pipe = new NamedPipeServerStream(
            pipeName,
            PipeDirection.In,
            1,
            PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous);
        output = new FileStream(
            outputPath,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.Read,
            4096,
            FileOptions.Asynchronous);
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
        catch (IOException)
        {
            // Expected when the bounded reader closes the pipe.
        }
        catch (ObjectDisposedException)
        {
            // Expected during bounded shutdown.
        }
        finally
        {
            try { output.Flush(); } catch { }
        }
    }

    public bool WaitForConnection(int milliseconds)
    {
        return connected.Wait(milliseconds);
    }

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

    return [UsbPcapPipeSink]::new($PipeName, $OutputPath)
}

# --- 1. VOD700 present? --------------------------------------------------
$dev = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.InstanceId -like '*VID_0483&PID_5265*' }
if (-not $dev) { Fail "VOD700 (VID_0483&PID_5265) is not connected. Connect it by USB (NOT to a vehicle) and retry." }
$pnpAddress = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName 'DEVPKEY_Device_Address' -ErrorAction SilentlyContinue).Data
$pnpLocation = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName 'DEVPKEY_Device_LocationInfo' -ErrorAction SilentlyContinue).Data
Write-Host "VOD700 present. PnP hub port/address property: $pnpAddress ($pnpLocation)"

# --- 2. Capture tooling present? -----------------------------------------
if (-not (Test-Path $dumpcap)) { Fail "dumpcap not found at $dumpcap. Install Wireshark." }
if (-not (Test-Path $editcap)) { Fail "editcap not found at $editcap. Install Wireshark." }
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
    if (-not $CaptureInterface) {
        $extcapInterfaces = & $usbpcapCmd --extcap-interfaces 2>&1 | ForEach-Object {
            if ("$_" -match '^interface \{value=(.+?)\}') { $Matches[1] }
        }
        $winUsbTargets = foreach ($interface in $extcapInterfaces) {
            & $usbpcapCmd --extcap-interface $interface --extcap-config 2>&1 | ForEach-Object {
                if ("$_" -match '^value \{arg=99\}\{value=(\d+)\}\{display=\[\d+\] WinUsb Device\}') {
                    [PSCustomObject]@{ Interface = $interface; Address = [int]$Matches[1] }
                }
            }
        }
        if (@($winUsbTargets).Count -eq 1) {
            $CaptureInterface = @($winUsbTargets)[0].Interface
        } elseif (@($winUsbTargets).Count -gt 1) {
            Fail "Multiple USBPcap WinUSB targets were found; refusing to guess the VOD700 root hub."
        }
    }
}
if (-not $CaptureInterface -or $CaptureInterface.Count -eq 0) {
    Fail "No USBPcap capture interface found via 'dumpcap -D'. Confirm USBPcap installed and the machine rebooted."
}
Write-Host "USBPcap interface(s): $($CaptureInterface -join ', ')"
$useDirectUsbPcap = $CaptureInterface.Count -eq 1 -and
    $CaptureInterface[0] -match '^\\\\\.\\USBPcap\d+$'
$captureAddress = $pnpAddress
if ($useDirectUsbPcap) {
    $targetRows = & $usbpcapCmd --extcap-interface $CaptureInterface[0] --extcap-config 2>&1 |
        ForEach-Object {
            if ("$_" -match '^value \{arg=99\}\{value=(\d+)\}\{display=\[\d+\] WinUsb Device\}') {
                [int]$Matches[1]
            }
        }
    if (@($targetRows).Count -ne 1) {
        Fail "Expected exactly one WinUSB target on $($CaptureInterface[0]); found $(@($targetRows).Count)."
    }
    $captureAddress = @($targetRows)[0]
    Write-Host "Capture backend: USBPcapCMD extcap -> bounded named-pipe sink"
    Write-Host "USBPcap device address: $captureAddress"
} else {
    Write-Host "Capture backend: dumpcap"
}

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
$extension = 'pcapng'
$capturePath = Join-Path $OutDir "handshake_$stamp.$extension"

# --- 6. Elevation note ---------------------------------------------------
$elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $elevated) { Write-Warning "Not elevated. USBPcap capture usually requires Administrator; if capture is empty, re-run elevated." }
if ($useDirectUsbPcap -and -not $DryRun -and -not $elevated) {
    Fail "Direct USBPcapCMD capture requires an elevated PowerShell session. No updater was launched."
}

# --- 7. Plan / DryRun ----------------------------------------------------
Write-Host "--------------------------------------------------------------"
Write-Host "PLAN (passive, bounded, no update-UI actions):"
Write-Host "  capture -> $capturePath"
Write-Host "  interfaces -> $($CaptureInterface -join ', ')"
Write-Host "  USBPcap address -> $captureAddress"
Write-Host "  backend -> $(if ($useDirectUsbPcap) {'USBPcapCMD extcap -> bounded named-pipe sink'} else {'dumpcap'})"
Write-Host "  duration -> $DurationSeconds s (bounded by orchestrator)"
Write-Host "  updater  -> $(if ($DryRun) {'(dry run: not launched)'} else {$UpdaterPath}) [launched with NO arguments]"
Write-Host "  close strategy -> CloseMainWindow; force-stop only if still open after 3 s"
Write-Host "--------------------------------------------------------------"
if ($DryRun) { Write-Host "DryRun complete. Environment is ready: USBPcap present, device present."; exit 0 }

# --- 8. Start capture (self-stopping) ------------------------------------
Write-Host "Starting capture..."
if ($useDirectUsbPcap) {
    $pipeName = "vod700_usbpcap_$stamp"
    $rawCapturePath = Join-Path $OutDir "handshake_$stamp.pcap"
    $captureSink = New-UsbPcapPipeSink -PipeName $pipeName -OutputPath $rawCapturePath
    $directArgs = '--extcap-interface "{0}" --fifo "{1}" --capture --devices {2} --inject-descriptors' -f
        $CaptureInterface[0], "\\.\pipe\$pipeName", $captureAddress
    $cap = Start-Process -FilePath $usbpcapCmd -ArgumentList $directArgs -PassThru -WindowStyle Hidden
    if (-not $captureSink.WaitForConnection(5000)) {
        $captureSink.Dispose()
        if (-not $cap.HasExited) { try { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue } catch {} }
        Fail "USBPcapCMD did not connect to the bounded capture sink. No updater was launched."
    }
} else {
    $iArgs = @(); foreach ($i in $CaptureInterface) { $iArgs += @('-i', $i) }
    $dumpArgs = $iArgs + @('-w', $capturePath, '-a', "duration:$($DurationSeconds + 4)")
    $cap = Start-Process -FilePath $dumpcap -ArgumentList $dumpArgs -PassThru -WindowStyle Hidden
}
Start-Sleep -Seconds 2  # let the capture attach
if ($cap.HasExited) {
    Fail "Capture process exited before the updater launch. No updater was launched."
}

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
if ($useDirectUsbPcap) {
    Start-Sleep -Seconds 1
    $captureSink.Dispose()
    try { Wait-Process -Id $cap.Id -Timeout 5 -ErrorAction SilentlyContinue } catch {}
    $cap.Refresh()
    if (-not $cap.HasExited) {
        Write-Warning "USBPcapCMD did not exit after the named pipe closed; using force-stop fallback."
        try { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    & $editcap $rawCapturePath $capturePath
    if ($LASTEXITCODE -ne 0) {
        Fail "editcap could not convert the bounded raw stream to PCAPNG: $rawCapturePath"
    }
} else {
    try { Wait-Process -Id $cap.Id -Timeout 15 -ErrorAction SilentlyContinue } catch {}
    if (-not $cap.HasExited) { try { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue } catch {} }
}
Start-Sleep -Seconds 1

# --- 13. Verify + hash ---------------------------------------------------
if (-not (Test-Path $capturePath) -or (Get-Item $capturePath).Length -le 24) {
    Fail "Capture file is missing or contains only a file header: $capturePath. (The wrong root hub may have been selected.)"
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
    $addrArg = @(); if ($captureAddress) { $addrArg = @('--address', "$captureAddress") }
    & $py -m vod700 capture analyze $capturePath --out (Join-Path $repo 'reports') --prefix "handshake_$stamp" @addrArg
}
Write-Host "Done. Raw capture stays under private_samples\ (git-ignored)."
