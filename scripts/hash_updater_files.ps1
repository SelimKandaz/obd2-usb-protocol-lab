<#
.SYNOPSIS
    Read-only static inventory of the official updater files (Phase 2).
.DESCRIPTION
    For each file under -Path, records: size, SHA-256, Authenticode signature
    status/subject, file version metadata, and the PE machine architecture (read
    from the header bytes). Nothing is executed, patched, or modified.

    Point -Path at the LOCAL, git-ignored vault, e.g. private_samples\updater.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\hash_updater_files.ps1 -Path private_samples\updater -OutJson private_samples\updater_inventory.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$OutJson
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Path)) { throw "Path not found: $Path" }

function Get-PeMachine {
    param([string]$File)
    try {
        $fs = [System.IO.File]::OpenRead($File)
        try {
            $br = New-Object System.IO.BinaryReader($fs)
            if ($fs.Length -lt 0x40) { return 'not-PE' }
            $fs.Position = 0
            if ($br.ReadUInt16() -ne 0x5A4D) { return 'not-PE' }  # 'MZ'
            $fs.Position = 0x3C
            $peOff = $br.ReadUInt32()
            if ($peOff + 6 -ge $fs.Length) { return 'not-PE' }
            $fs.Position = $peOff
            if ($br.ReadUInt32() -ne 0x00004550) { return 'not-PE' }  # 'PE\0\0'
            $machine = $br.ReadUInt16()
            switch ($machine) {
                0x8664 { 'x64' }
                0x014C { 'x86' }
                0xAA64 { 'ARM64' }
                default { ('0x{0:X4}' -f $machine) }
            }
        } finally { $fs.Close() }
    } catch { 'error' }
}

$rows = foreach ($f in Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue) {
    $sig = Get-AuthenticodeSignature -FilePath $f.FullName -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        RelativePath  = $f.FullName.Substring((Resolve-Path $Path).Path.Length).TrimStart('\')
        SizeBytes     = $f.Length
        SHA256        = (Get-FileHash -Algorithm SHA256 -Path $f.FullName).Hash
        PEArch        = Get-PeMachine -File $f.FullName
        CompanyName   = $f.VersionInfo.CompanyName
        ProductName   = $f.VersionInfo.ProductName
        FileVersion   = $f.VersionInfo.FileVersion
        SigStatus     = if ($sig) { $sig.Status } else { 'n/a' }
        SigSubject    = if ($sig -and $sig.SignerCertificate) { $sig.SignerCertificate.Subject } else { '' }
        LastWrite     = $f.LastWriteTimeUtc.ToString('o')
    }
}

$rows | Sort-Object RelativePath | Format-Table -AutoSize | Out-String -Width 4096 | Write-Output

if ($OutJson) {
    $rows | ConvertTo-Json -Depth 4 | Out-File -FilePath $OutJson -Encoding utf8
    Write-Output "Wrote inventory: $OutJson ($($rows.Count) files)"
}
