#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Audit','Hunt','Enterprise','Baseline','Report')]
    [string]$Mode = 'Audit',
    [ValidateRange(1,1440)]
    [int]$ScanMinutes = 15,
    [string]$AegisScript = "$PSScriptRoot\..\vendor\ClearGlassCorp_AEGIS_v6.1.1_HARDENED_FINAL.ps1"
)

$ErrorActionPreference = 'Stop'
$resolved = Resolve-Path -LiteralPath $AegisScript -ErrorAction Stop
$allowedName = 'ClearGlassCorp_AEGIS_v6.1.1_HARDENED_FINAL.ps1'
if ([IO.Path]::GetFileName($resolved.Path) -ne $allowedName) {
    throw "Refusing to execute an unexpected script: $($resolved.Path)"
}

$argsList = @('-NoLogo','-NoProfile','-NonInteractive','-File',$resolved.Path,'-Mode',$Mode)
if ($Mode -in @('Audit','Hunt','Enterprise')) {
    $argsList += @('-ScanMinutes', $ScanMinutes, '-GenerateReport')
}

& powershell.exe @argsList
exit $LASTEXITCODE
