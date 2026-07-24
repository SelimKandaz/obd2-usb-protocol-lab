<#
.SYNOPSIS
    List the WinUSB device-interface symbolic links exposed by the VOD700.
.DESCRIPTION
    Read-only. Reads the registry DeviceClasses store for the known interface
    class GUIDs (registered by the device's MS OS descriptor) plus the generic
    USB device-interface GUID. No device handle is opened.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\get_vod700_interfaces.ps1
#>
[CmdletBinding()]
param(
    [string]$Match = 'VID_0483&PID_5265'
)

$ErrorActionPreference = 'Stop'

# Interface class GUIDs seen on this device (from the PnP dump) + generic USB.
$guids = @(
    '{f70242c7-fb25-443b-9e7e-a4260f373982}',  # vendor interface GUID #1
    '{dee824ef-729b-4a0e-9c14-b7117d33a817}',  # vendor interface GUID #2
    '{a5dcbf10-6530-11d2-901f-00c04fb951ed}'   # GUID_DEVINTERFACE_USB_DEVICE
)

$base = 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceClasses'
$found = 0

foreach ($guid in $guids) {
    $key = Join-Path $base $guid
    if (-not (Test-Path $key)) { continue }
    Get-ChildItem $key -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -like "*$Match*" } | ForEach-Object {
        $found++
        # The registry subkey name is the mangled symbolic link. Only the leading
        # '##?#' maps to the '\\?\' prefix; inner '#' remain separators in the path.
        $sym = $_.PSChildName -replace '^##\?#', '\\?\'
        Write-Output "Interface class GUID : $guid"
        Write-Output "Symbolic link        : $sym"
        Write-Output ""
    }
}

if ($found -eq 0) {
    Write-Warning "No matching device interfaces found for $Match."
} else {
    Write-Output "Total interface links: $found"
    Write-Output "Tip: 'python -m vod700 devices' enumerates the same paths via SetupAPI."
}
