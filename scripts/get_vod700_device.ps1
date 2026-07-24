<#
.SYNOPSIS
    Read-only inventory of the VOD700 USB device node (VID_0483 & PID_5265).
.DESCRIPTION
    Uses Get-PnpDevice / Get-PnpDeviceProperty only. The device is never opened,
    written to, reset, or re-enumerated. Safe to run with the device idle.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\get_vod700_device.ps1
#>
[CmdletBinding()]
param(
    [string]$VidPid = 'VID_0483&PID_5265'
)

$ErrorActionPreference = 'Stop'

$devices = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.InstanceId -like "*$VidPid*" }

if (-not $devices) {
    Write-Warning "No present device matching $VidPid. Is the VOD700 connected by USB?"
    return
}

$keys = @(
    'DEVPKEY_Device_BusReportedDeviceDesc',
    'DEVPKEY_Device_Service',
    'DEVPKEY_Device_DriverInfPath',
    'DEVPKEY_Device_DriverVersion',
    'DEVPKEY_Device_DriverProvider',
    'DEVPKEY_Device_Address',
    'DEVPKEY_Device_LocationInfo',
    'DEVPKEY_Device_Manufacturer'
)

foreach ($d in $devices) {
    Write-Output "==================================================================="
    Write-Output "  $($d.FriendlyName)"
    Write-Output "==================================================================="
    $d | Select-Object Status, Present, Class, ClassGuid, InstanceId | Format-List | Out-String | Write-Output
    foreach ($k in $keys) {
        $val = (Get-PnpDeviceProperty -InstanceId $d.InstanceId -KeyName $k -ErrorAction SilentlyContinue).Data
        Write-Output ("{0,-40}: {1}" -f $k, $val)
    }
    Write-Output ""
    Write-Output "Hardware IDs:"
    (Get-PnpDeviceProperty -InstanceId $d.InstanceId -KeyName 'DEVPKEY_Device_HardwareIds' -ErrorAction SilentlyContinue).Data |
        ForEach-Object { Write-Output "  $_" }
    Write-Output ""
}
