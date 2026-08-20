# ==============================================================================
# ClearGlass HyperSpeed — Stable Maximum Network Throughput (Audit-First)
# ClearGlassInc Windows utility
#
# Design goals:
# - Maximize stable Windows LAN/Internet throughput without legacy "magic" tweaks.
# - Preserve Windows TCP receive-window autotuning and RSS.
# - Tune only adapter capabilities the installed driver explicitly exposes.
# - Never guess fixed buffer sizes; choose the driver's highest advertised value.
# - Keep latency-biased changes, power-saving changes, Delivery Optimization policy,
#   congestion-provider overrides, and network-stack resets explicit/opt-in.
# - Back up every adapter value this script changes and provide rollback support.
#
# IMPORTANT:
# - This cannot exceed ISP/router/switch/NIC/link-rate limits.
# - Advanced NIC properties are driver-specific. Unsupported settings are skipped.
# - Changes are staged with -NoRestart where possible. Reboot after applying.
# - -LowLatency disables Interrupt Moderation when supported; that can increase CPU
#   load and may reduce bulk throughput on some systems. Benchmark before keeping it.
# - -ResetNetworkStack is troubleshooting-only and requires a reboot.
#
# Examples:
#   # Audit only (no changes)
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1
#
#   # Stable throughput baseline
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -Apply
#
#   # Throughput + disable NIC power saving while plugged in
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -Apply -DisableAdapterPowerSaving
#
#   # Optional peer-to-peer update traffic reduction
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -Apply -DisableDeliveryOptimizationPeering
#
#   # Optional latency bias (benchmark; not always faster for bulk transfers)
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -Apply -LowLatency
#
#   # Optional congestion provider override (modern Windows supports provider selection
#   # through the Internet supplemental TCP template; availability is build-dependent)
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -Apply -CongestionProvider ctcp
#
#   # Roll back values captured by a prior run
#   powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -RollbackFrom "C:\ProgramData\ClearGlass\HyperSpeed\Backup\YYYYMMDD_HHMMSS"
# ==============================================================================

#Requires -RunAsAdministrator

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Apply,
    [switch]$LowLatency,
    [switch]$DisableAdapterPowerSaving,
    [switch]$DisableDeliveryOptimizationPeering,
    [ValidateSet('default', 'ctcp', 'cubic', 'bbr2')]
    [string]$CongestionProvider,
    [switch]$ResetNetworkStack,
    [string]$RollbackFrom
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$script:Root = Join-Path $env:ProgramData 'ClearGlass\HyperSpeed'
$script:LogRoot = Join-Path $script:Root 'Logs'
$script:BackupRoot = Join-Path $script:Root 'Backup'
$script:ReportRoot = Join-Path $script:Root 'Reports'

foreach ($path in @($script:Root, $script:LogRoot, $script:BackupRoot, $script:ReportRoot)) {
    if (-not (Test-Path $path)) {
        New-Item -Path $path -ItemType Directory -Force | Out-Null
    }
}

$script:LogFile = Join-Path $script:LogRoot "HyperSpeed_$($script:Stamp).log"
$script:ReportFile = Join-Path $script:ReportRoot "HyperSpeed_$($script:Stamp).txt"
$script:BackupFolder = Join-Path $script:BackupRoot $script:Stamp
$script:AdapterChangeFile = $null
$script:PowerSnapshotFile = $null
$script:RegistrySnapshotFile = $null
$script:TranscriptStarted = $false

function Write-LogLine {
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet('INFO', 'OK', 'WARN', 'ERROR')][string]$Level = 'INFO'
    )

    $line = '{0} [{1}] {2}' -f (Get-Date -Format o), $Level, $Message
    Write-Host $line
    Add-Content -Path $script:LogFile -Value $line
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = & $FilePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()

    if ($text) {
        Write-LogLine "$FilePath $($Arguments -join ' ') -> $text"
    }

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "Command failed with exit code $exitCode: $FilePath $($Arguments -join ' ')"
    }

    [pscustomobject]@{
        ExitCode = $exitCode
        Output   = $text
    }
}

function New-RunBackup {
    New-Item -Path $script:BackupFolder -ItemType Directory -Force | Out-Null
    $script:AdapterChangeFile = Join-Path $script:BackupFolder 'adapter_changes.jsonl'
    $script:PowerSnapshotFile = Join-Path $script:BackupFolder 'adapter_power.json'
    $script:RegistrySnapshotFile = Join-Path $script:BackupFolder 'registry_snapshot.json'

    Get-NetAdapter -ErrorAction Stop |
        Get-NetAdapterAdvancedProperty -AllProperties -ErrorAction SilentlyContinue |
        Export-Clixml -Path (Join-Path $script:BackupFolder 'netadapter_advanced_all.xml')

    Get-NetAdapter -ErrorAction Stop |
        Export-Clixml -Path (Join-Path $script:BackupFolder 'netadapters.xml')

    try {
        Get-NetTCPSetting -ErrorAction Stop |
            Export-Clixml -Path (Join-Path $script:BackupFolder 'nettcp_settings.xml')
    }
    catch {
        Write-LogLine "Could not export NetTCP settings: $($_.Exception.Message)" 'WARN'
    }

    try {
        Get-NetAdapterPowerManagement -Name '*' -ErrorAction Stop |
            ConvertTo-Json -Depth 5 |
            Set-Content -Path $script:PowerSnapshotFile -Encoding UTF8
    }
    catch {
        Write-LogLine "Could not export adapter power-management state: $($_.Exception.Message)" 'WARN'
    }

    $doPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization'
    $doValue = $null
    $doExists = $false
    if (Test-Path $doPath) {
        $item = Get-ItemProperty -Path $doPath -Name 'DODownloadMode' -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            $doExists = $true
            $doValue = [int]$item.DODownloadMode
        }
    }

    [pscustomobject]@{
        DeliveryOptimization = [pscustomobject]@{
            Path   = $doPath
            Name   = 'DODownloadMode'
            Exists = $doExists
            Value  = $doValue
        }
        CongestionProviderWasOverriddenByThisRun = $false
    } | ConvertTo-Json -Depth 5 | Set-Content -Path $script:RegistrySnapshotFile -Encoding UTF8

    (Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'show', 'global') -AllowFailure).Output |
        Set-Content -Path (Join-Path $script:BackupFolder 'tcp_global_before.txt') -Encoding UTF8

    (Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'show', 'supplemental') -AllowFailure).Output |
        Set-Content -Path (Join-Path $script:BackupFolder 'tcp_supplemental_before.txt') -Encoding UTF8

    Write-LogLine "Backup created: $script:BackupFolder" 'OK'
}

function Save-AdapterChange {
    param(
        [Parameter(Mandatory)][string]$AdapterName,
        [Parameter(Mandatory)][string]$DisplayName,
        [Parameter(Mandatory)][string]$DisplayValue
    )

    [pscustomobject]@{
        AdapterName = $AdapterName
        DisplayName = $DisplayName
        DisplayValue = $DisplayValue
    } | ConvertTo-Json -Compress | Add-Content -Path $script:AdapterChangeFile -Encoding UTF8
}

function Get-DriverAdvancedProperty {
    param(
        [Parameter(Mandatory)][string]$AdapterName,
        [Parameter(Mandatory)][string[]]$CandidateNames
    )

    $all = @(Get-NetAdapterAdvancedProperty -Name $AdapterName -AllProperties -ErrorAction SilentlyContinue)
    foreach ($candidate in $CandidateNames) {
        $match = $all | Where-Object { $_.DisplayName -eq $candidate } | Select-Object -First 1
        if ($null -ne $match) { return $match }
    }
    return $null
}

function Set-AdvancedPropertySafe {
    param(
        [Parameter(Mandatory)][string]$AdapterName,
        [Parameter(Mandatory)][string[]]$CandidateNames,
        [Parameter(Mandatory)][string[]]$PreferredValues,
        [Parameter(Mandatory)][string]$Reason
    )

    $property = Get-DriverAdvancedProperty -AdapterName $AdapterName -CandidateNames $CandidateNames
    if ($null -eq $property) {
        Write-LogLine "$AdapterName: property not exposed by driver; skipped: $($CandidateNames -join ' / ')" 'WARN'
        return $false
    }

    $validValues = @($property.ValidDisplayValues) | Where-Object { $_ -ne $null } | ForEach-Object { [string]$_ }
    $chosen = $null

    foreach ($preferred in $PreferredValues) {
        $chosen = $validValues | Where-Object { $_ -ieq $preferred } | Select-Object -First 1
        if ($chosen) { break }
    }

    if (-not $chosen) {
        Write-LogLine "$AdapterName: no safe supported target value found for '$($property.DisplayName)'. Valid values: $($validValues -join ', ')" 'WARN'
        return $false
    }

    if ([string]$property.DisplayValue -ieq [string]$chosen) {
        Write-LogLine "$AdapterName: '$($property.DisplayName)' already set to '$chosen'." 'OK'
        return $true
    }

    Save-AdapterChange -AdapterName $AdapterName -DisplayName $property.DisplayName -DisplayValue ([string]$property.DisplayValue)

    if ($PSCmdlet.ShouldProcess("$AdapterName / $($property.DisplayName)", "Set '$chosen' ($Reason)")) {
        Set-NetAdapterAdvancedProperty -Name $AdapterName -DisplayName $property.DisplayName -DisplayValue $chosen -NoRestart -ErrorAction Stop
        Write-LogLine "$AdapterName: '$($property.DisplayName)' -> '$chosen' ($Reason)" 'OK'
    }
    return $true
}

function Set-BufferPropertyToDriverMaximum {
    param(
        [Parameter(Mandatory)][string]$AdapterName,
        [Parameter(Mandatory)][string[]]$CandidateNames
    )

    $property = Get-DriverAdvancedProperty -AdapterName $AdapterName -CandidateNames $CandidateNames
    if ($null -eq $property) {
        Write-LogLine "$AdapterName: buffer property not exposed; skipped: $($CandidateNames -join ' / ')" 'WARN'
        return
    }

    $numericValues = @()
    foreach ($value in @($property.ValidDisplayValues)) {
        $parsed = 0
        if ([int]::TryParse(([string]$value).Trim(), [ref]$parsed)) {
            $numericValues += $parsed
        }
    }

    if ($numericValues.Count -eq 0) {
        Write-LogLine "$AdapterName: '$($property.DisplayName)' does not advertise numeric valid values; refusing to guess." 'WARN'
        return
    }

    $maximum = ($numericValues | Measure-Object -Maximum).Maximum
    $target = [string]$maximum

    if ([string]$property.DisplayValue -eq $target) {
        Write-LogLine "$AdapterName: '$($property.DisplayName)' already at driver maximum '$target'." 'OK'
        return
    }

    Save-AdapterChange -AdapterName $AdapterName -DisplayName $property.DisplayName -DisplayValue ([string]$property.DisplayValue)

    if ($PSCmdlet.ShouldProcess("$AdapterName / $($property.DisplayName)", "Set driver-advertised maximum '$target'")) {
        Set-NetAdapterAdvancedProperty -Name $AdapterName -DisplayName $property.DisplayName -DisplayValue $target -NoRestart -ErrorAction Stop
        Write-LogLine "$AdapterName: '$($property.DisplayName)' -> '$target' (driver-advertised maximum)" 'OK'
    }
}

function Enable-RssSafe {
    param([Parameter(Mandatory)][string]$AdapterName)

    try {
        $rss = Get-NetAdapterRss -Name $AdapterName -ErrorAction Stop
        if ($rss.Enabled) {
            Write-LogLine "$AdapterName: RSS already enabled." 'OK'
            return
        }

        if ($PSCmdlet.ShouldProcess($AdapterName, 'Enable Receive Side Scaling (RSS)')) {
            Enable-NetAdapterRss -Name $AdapterName -NoRestart -ErrorAction Stop
            Write-LogLine "$AdapterName: RSS enabled." 'OK'
        }
    }
    catch {
        Write-LogLine "$AdapterName: RSS unsupported or unavailable; skipped. $($_.Exception.Message)" 'WARN'
    }
}

function Disable-AdapterPowerSavingSafe {
    param([Parameter(Mandatory)][string]$AdapterName)

    try {
        $current = Get-NetAdapterPowerManagement -Name $AdapterName -ErrorAction Stop
        $params = @{
            Name      = $AdapterName
            NoRestart = $true
            ErrorAction = 'Stop'
        }

        foreach ($propertyName in @('SelectiveSuspend', 'DeviceSleepOnDisconnect', 'D0PacketCoalescing')) {
            if ($current.PSObject.Properties.Name -contains $propertyName) {
                $value = [string]$current.$propertyName
                if ($value -match 'Enabled|Unsupported') {
                    if ($value -eq 'Enabled') { $params[$propertyName] = 'Disabled' }
                }
            }
        }

        if ($params.Keys.Count -le 3) {
            Write-LogLine "$AdapterName: no supported power-saving property required a change." 'OK'
            return
        }

        if ($PSCmdlet.ShouldProcess($AdapterName, 'Disable supported NIC sleep/coalescing power-saving features')) {
            Set-NetAdapterPowerManagement @params
            Write-LogLine "$AdapterName: supported NIC power-saving features disabled without immediate adapter restart." 'OK'
        }
    }
    catch {
        Write-LogLine "$AdapterName: power-management tuning skipped. $($_.Exception.Message)" 'WARN'
    }
}

function Set-DeliveryOptimizationNoPeering {
    $path = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization'
    if (-not (Test-Path $path)) {
        New-Item -Path $path -Force | Out-Null
    }

    if ($PSCmdlet.ShouldProcess("$path::DODownloadMode", 'Set HTTP-only / no peer-to-peer mode (0)')) {
        New-ItemProperty -Path $path -Name 'DODownloadMode' -Value 0 -PropertyType DWord -Force | Out-Null
        Write-LogLine 'Delivery Optimization peer-to-peer disabled via supported policy value DODownloadMode=0. Windows Update downloads remain enabled.' 'OK'
    }
}

function Set-InternetCongestionProvider {
    param([Parameter(Mandatory)][string]$Provider)

    if ($PSCmdlet.ShouldProcess('TCP supplemental template: internet', "Set congestion provider '$Provider'")) {
        $result = Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'set', 'supplemental', 'template=internet', "congestionprovider=$Provider") -AllowFailure
        if ($result.ExitCode -ne 0) {
            Write-LogLine "Congestion provider '$Provider' was rejected by this Windows build; leaving current provider unchanged." 'WARN'
            return $false
        }

        $snapshot = Get-Content -Path $script:RegistrySnapshotFile -Raw | ConvertFrom-Json
        $snapshot.CongestionProviderWasOverriddenByThisRun = $true
        $snapshot | ConvertTo-Json -Depth 5 | Set-Content -Path $script:RegistrySnapshotFile -Encoding UTF8
        Write-LogLine "Internet TCP congestion provider set to '$Provider'." 'OK'
        return $true
    }
    return $false
}

function Restore-PowerManagement {
    param([Parameter(Mandatory)][string]$SnapshotPath)

    if (-not (Test-Path $SnapshotPath)) { return }

    $items = @(Get-Content -Path $SnapshotPath -Raw | ConvertFrom-Json)
    foreach ($item in $items) {
        $name = [string]$item.Name
        if (-not $name) { continue }

        $params = @{
            Name = $name
            NoRestart = $true
            ErrorAction = 'SilentlyContinue'
        }

        foreach ($propertyName in @('SelectiveSuspend', 'DeviceSleepOnDisconnect', 'D0PacketCoalescing')) {
            if ($item.PSObject.Properties.Name -contains $propertyName) {
                $value = [string]$item.$propertyName
                if ($value -in @('Enabled', 'Disabled')) {
                    $params[$propertyName] = $value
                }
            }
        }

        if ($params.Keys.Count -gt 3) {
            Set-NetAdapterPowerManagement @params
            Write-LogLine "$name: restored saved power-management values." 'OK'
        }
    }
}

function Invoke-Rollback {
    param([Parameter(Mandatory)][string]$Folder)

    if (-not (Test-Path $Folder)) {
        throw "Rollback folder does not exist: $Folder"
    }

    $changesFile = Join-Path $Folder 'adapter_changes.jsonl'
    if (Test-Path $changesFile) {
        $changes = @(Get-Content -Path $changesFile | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
        [array]::Reverse($changes)
        foreach ($change in $changes) {
            try {
                Set-NetAdapterAdvancedProperty -Name ([string]$change.AdapterName) -DisplayName ([string]$change.DisplayName) -DisplayValue ([string]$change.DisplayValue) -NoRestart -ErrorAction Stop
                Write-LogLine "$($change.AdapterName): restored '$($change.DisplayName)' to '$($change.DisplayValue)'." 'OK'
            }
            catch {
                Write-LogLine "Rollback failed for $($change.AdapterName) / $($change.DisplayName): $($_.Exception.Message)" 'WARN'
            }
        }
    }

    Restore-PowerManagement -SnapshotPath (Join-Path $Folder 'adapter_power.json')

    $registryFile = Join-Path $Folder 'registry_snapshot.json'
    if (Test-Path $registryFile) {
        $snapshot = Get-Content -Path $registryFile -Raw | ConvertFrom-Json
        $do = $snapshot.DeliveryOptimization
        if ($null -ne $do) {
            if ([bool]$do.Exists) {
                if (-not (Test-Path ([string]$do.Path))) { New-Item -Path ([string]$do.Path) -Force | Out-Null }
                New-ItemProperty -Path ([string]$do.Path) -Name ([string]$do.Name) -Value ([int]$do.Value) -PropertyType DWord -Force | Out-Null
                Write-LogLine "Restored Delivery Optimization policy value to $($do.Value)." 'OK'
            }
            else {
                Remove-ItemProperty -Path ([string]$do.Path) -Name ([string]$do.Name) -ErrorAction SilentlyContinue
                Write-LogLine 'Removed Delivery Optimization policy value created by HyperSpeed.' 'OK'
            }
        }

        if ([bool]$snapshot.CongestionProviderWasOverriddenByThisRun) {
            Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'set', 'supplemental', 'template=internet', 'congestionprovider=default') -AllowFailure | Out-Null
            Write-LogLine 'Restored Internet congestion provider to Windows default.' 'OK'
        }
    }

    Write-LogLine 'Rollback staged. Restart Windows so adapter properties reload cleanly.' 'OK'
}

function Write-AuditReport {
    param([string]$Mode)

    $adapters = @(Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' })
    $tcpGlobal = (Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'show', 'global') -AllowFailure).Output
    $tcpSupplemental = (Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'show', 'supplemental') -AllowFailure).Output

    $adapterSummary = foreach ($adapter in $adapters) {
        $speed = if ($adapter.LinkSpeed) { [string]$adapter.LinkSpeed } else { 'Unknown' }
        "- $($adapter.Name) | $($adapter.InterfaceDescription) | LinkSpeed=$speed | Status=$($adapter.Status)"
    }

    @"
ClearGlass HyperSpeed — Network Report
Generated: $(Get-Date -Format o)
Computer: $env:COMPUTERNAME
Mode: $Mode

Active adapters:
$($adapterSummary -join "`r`n")

TCP global state:
$tcpGlobal

TCP supplemental state:
$tcpSupplemental

Notes:
- Link speed is the negotiated local adapter link, not guaranteed ISP throughput.
- This script does not bypass ISP/router/switch/NIC limitations.
- For repeatable validation, test the same wired endpoint, server, cable, and workload before/after.
- Reboot after applied adapter changes before judging final results.
"@ | Set-Content -Path $script:ReportFile -Encoding UTF8

    Write-LogLine "Report written: $script:ReportFile" 'OK'
}

Start-Transcript -Path $script:LogFile -Append | Out-Null
$script:TranscriptStarted = $true

try {
    Write-Host '========================================='
    Write-Host ' CLEARGLASS HYPERSPEED'
    Write-Host ' Stable Maximum Network Throughput'
    Write-Host '========================================='

    if ($RollbackFrom) {
        Invoke-Rollback -Folder $RollbackFrom
        Write-AuditReport -Mode 'Rollback'
        return
    }

    if (-not $Apply) {
        Write-LogLine 'Audit-only mode. No system settings will be changed.' 'INFO'
        Write-AuditReport -Mode 'Audit only'
        Write-Host ''
        Write-Host 'To apply the stable throughput baseline, re-run with -Apply.'
        return
    }

    New-RunBackup

    if ($PSCmdlet.ShouldProcess('Windows TCP/IP stack', 'Set receive-window autotuning to Normal')) {
        $result = Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'set', 'global', 'autotuninglevel=normal') -AllowFailure
        if ($result.ExitCode -eq 0) {
            Write-LogLine 'TCP receive-window autotuning set to Normal.' 'OK'
        }
        else {
            Write-LogLine 'Could not set TCP receive-window autotuning; current state retained.' 'WARN'
        }
    }

    if ($PSCmdlet.ShouldProcess('Windows TCP/IP stack', 'Enable OS-level Receive Side Scaling')) {
        $result = Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'tcp', 'set', 'global', 'rss=enabled') -AllowFailure
        if ($result.ExitCode -eq 0) {
            Write-LogLine 'OS-level RSS enabled.' 'OK'
        }
        else {
            Write-LogLine 'Could not enable OS-level RSS; current state retained.' 'WARN'
        }
    }

    $activeAdapters = @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' })
    if ($activeAdapters.Count -eq 0) {
        $activeAdapters = @(Get-NetAdapter -ErrorAction Stop | Where-Object { $_.Status -eq 'Up' })
    }

    foreach ($adapter in $activeAdapters) {
        Write-LogLine "Tuning active adapter: $($adapter.Name) [$($adapter.InterfaceDescription)]"

        Enable-RssSafe -AdapterName $adapter.Name

        Set-BufferPropertyToDriverMaximum -AdapterName $adapter.Name -CandidateNames @('Receive Buffers', 'Receive Buffer')
        Set-BufferPropertyToDriverMaximum -AdapterName $adapter.Name -CandidateNames @('Transmit Buffers', 'Transmit Buffer')

        Set-AdvancedPropertySafe -AdapterName $adapter.Name -CandidateNames @('Energy-Efficient Ethernet', 'Energy Efficient Ethernet', 'EEE') -PreferredValues @('Disabled', 'Off') -Reason 'Reduce energy-saving latency/link-state transitions on supported Ethernet adapters.' | Out-Null
        Set-AdvancedPropertySafe -AdapterName $adapter.Name -CandidateNames @('Green Ethernet', 'Advanced EEE') -PreferredValues @('Disabled', 'Off') -Reason 'Disable driver energy-saving mode when explicitly exposed.' | Out-Null

        if ($LowLatency) {
            Set-AdvancedPropertySafe -AdapterName $adapter.Name -CandidateNames @('Interrupt Moderation') -PreferredValues @('Disabled', 'Off') -Reason 'Latency-biased mode; increases interrupt rate and CPU load.' | Out-Null
        }

        if ($DisableAdapterPowerSaving) {
            Disable-AdapterPowerSavingSafe -AdapterName $adapter.Name
        }
    }

    if ($DisableDeliveryOptimizationPeering) {
        Set-DeliveryOptimizationNoPeering
    }

    if ($PSBoundParameters.ContainsKey('CongestionProvider')) {
        Set-InternetCongestionProvider -Provider $CongestionProvider | Out-Null
    }

    if ($ResetNetworkStack) {
        Write-LogLine 'Network-stack reset requested. This is troubleshooting-only and can remove custom Winsock/LSP/IP state.' 'WARN'
        if ($PSCmdlet.ShouldProcess('Winsock and TCP/IP configuration', 'Reset network stack')) {
            Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('winsock', 'reset') -AllowFailure | Out-Null
            Invoke-NativeCommand -FilePath 'netsh.exe' -Arguments @('int', 'ip', 'reset') -AllowFailure | Out-Null
            Write-LogLine 'Winsock/IP reset staged. Reboot required.' 'OK'
        }
    }

    try {
        Clear-DnsClientCache -ErrorAction Stop
        Write-LogLine 'DNS client cache flushed.' 'OK'
    }
    catch {
        Write-LogLine "DNS cache flush skipped: $($_.Exception.Message)" 'WARN'
    }

    Write-AuditReport -Mode 'Applied'

    Write-Host ''
    Write-Host '========================================='
    Write-Host ' HYPERSPEED OPTIMIZATION STAGED'
    Write-Host '========================================='
    Write-Host "Backup: $script:BackupFolder"
    Write-Host "Log:    $script:LogFile"
    Write-Host "Report: $script:ReportFile"
    Write-Host ''
    Write-Host 'Restart Windows before final benchmarking.'
    Write-Host "Rollback: powershell -ExecutionPolicy Bypass -File .\tools\windows\clearglass-hyperspeed-network.ps1 -RollbackFrom `"$script:BackupFolder`""
}
catch {
    Write-LogLine $_.Exception.Message 'ERROR'
    throw
}
finally {
    if ($script:TranscriptStarted) {
        try { Stop-Transcript | Out-Null } catch {}
    }
}
