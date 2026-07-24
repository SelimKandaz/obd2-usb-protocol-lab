<#
.SYNOPSIS
    Check USB-capture prerequisites and print the current VOD700 capture target.
.DESCRIPTION
    Read-only. Reports whether Wireshark/tshark/USBPcap/Npcap are present, and
    prints the VOD700's current USB bus/address so a capture can target it
    (the address changes across reconnects — never hard-code it).
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\capture_prereqs.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

Write-Output "=== Capture tooling ==="
$checks = [ordered]@{
    'Wireshark (Program Files)' = 'C:\Program Files\Wireshark\Wireshark.exe'
    'tshark'                    = 'C:\Program Files\Wireshark\tshark.exe'
    'dumpcap'                   = 'C:\Program Files\Wireshark\dumpcap.exe'
    'USBPcapCMD'                = 'C:\Program Files\USBPcap\USBPcapCMD.exe'
}
foreach ($name in $checks.Keys) {
    $present = Test-Path $checks[$name]
    Write-Output ("  {0,-26} {1}" -f $name, $(if ($present) { 'FOUND' } else { 'missing' }))
}
$usbpcapDrv = Get-CimInstance Win32_SystemDriver -Filter "Name='USBPcap'" -ErrorAction SilentlyContinue
Write-Output ("  {0,-26} {1}" -f 'USBPcap driver', $(if ($usbpcapDrv) { $usbpcapDrv.State } else { 'not installed' }))
Write-Output "  NOTE: Npcap captures NETWORK interfaces only; USB capture needs USBPcap."
Write-Output ""

Write-Output "=== VOD700 capture target (current) ==="
$dev = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.InstanceId -like '*VID_0483&PID_5265*' }
if (-not $dev) {
    Write-Warning "VOD700 not present; connect it before capturing."
} else {
    $addr = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName 'DEVPKEY_Device_Address' -ErrorAction SilentlyContinue).Data
    $loc  = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName 'DEVPKEY_Device_LocationInfo' -ErrorAction SilentlyContinue).Data
    Write-Output "  InstanceId    : $($dev.InstanceId)"
    Write-Output "  USB address   : $addr   (changes on reconnect)"
    Write-Output "  Location      : $loc"
    Write-Output ""
    Write-Output "  Wireshark display filter (once capturing on the right USBPcap root hub):"
    Write-Output "    usb.device_address == $addr"
    Write-Output "  Or narrow to this device by VID/PID after the descriptor exchange:"
    Write-Output "    usb.idVendor == 0x0483 && usb.idProduct == 0x5265"
}
