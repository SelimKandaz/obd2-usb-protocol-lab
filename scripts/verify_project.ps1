[CmdletBinding()]
param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$ruff = Join-Path $root '.venv\Scripts\ruff.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project virtual-environment Python not found: $python"
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Validation command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')"
    }
}

Push-Location $root
try {
    Invoke-Checked $python @('-m', 'pytest', '-q')
    Invoke-Checked $ruff @('check', 'src', 'tests')
    Invoke-Checked $python @('-m', 'mypy', 'src')
    Invoke-Checked $python @('-m', 'compileall', '-q', 'src', 'tests')
    Invoke-Checked $python @('tools\validate_knowledge.py')
    if (-not $SkipBuild) {
        Invoke-Checked $python @('-m', 'build', '--wheel', '--no-isolation')
    }
    Write-Host 'VERIFY_OK — tests, lint, types, compilation, and requested build passed.'
}
finally {
    Pop-Location
}
