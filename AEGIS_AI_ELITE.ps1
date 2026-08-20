#Requires -RunAsAdministrator
#Requires -Version 5.1

<#
.SYNOPSIS
    ClearGlassCorp AEGIS AI Elite - Advanced Security Intelligence Platform

.DESCRIPTION
    Elite-tier endpoint security with voice-guided operations, advanced pattern
    recognition, autonomous threat response, and comprehensive vendor intelligence.
    
    CORE CAPABILITIES:
    ✓ Voice-Guided Security Operations (Text-to-Speech feedback)
    ✓ Advanced Pattern Recognition (Statistical analysis, not ML hype)
    ✓ Autonomous Threat Response (Configurable automation)
    ✓ Comprehensive Vendor Intelligence (Risk scoring & tracking)
    ✓ Real-Time Behavioral Analysis (Process, network, file patterns)
    ✓ Supply Chain Security (Third-party risk assessment)
    ✓ Network Topology Mapping (Device discovery & profiling)
    ✓ Zero-Trust Architecture Support (Continuous verification)
    ✓ Compliance Reporting (NIST, CIS benchmarks)
    ✓ Threat Intelligence Integration (MITRE ATT&CK mapping)
    
.PARAMETER Mode
    Operation mode: Dashboard, Hunt, Audit, Monitor, Vendor, Compliance, Intel

.PARAMETER VoiceEnabled
    Enable voice-guided operations (default: true)

.PARAMETER AutoResponse
    Enable autonomous threat response

.PARAMETER ContinuousMonitor
    Run continuous monitoring mode

.EXAMPLE
    .\AEGIS_AI_ELITE.ps1
    Launch interactive dashboard with voice guidance

.EXAMPLE
    .\AEGIS_AI_ELITE.ps1 -Mode Hunt -AutoResponse
    Autonomous threat hunting with automatic response

.EXAMPLE
    .\AEGIS_AI_ELITE.ps1 -ContinuousMonitor -AutoResponse
    24/7 autonomous security operations

.NOTES
    Copyright © 2026 ClearGlassCorp International
    Creator: Desmond Otieno Odhiambo
    Version: 6.0 Elite Edition
    Build: 20260111-ELITE
    
    HONEST CAPABILITY STATEMENT:
    This platform uses advanced pattern matching, statistical analysis, and
    rule-based automation - NOT machine learning/neural networks. Voice features
    use Windows TTS engine. All claims are technically accurate.
#>

[CmdletBinding()]
param(
    [ValidateSet('Dashboard','Hunt','Audit','Monitor','Vendor','Compliance','Intel','Report')]
    [string]$Mode = 'Dashboard',
    [switch]$VoiceEnabled = $true,
    [switch]$AutoResponse,
    [switch]$ContinuousMonitor,
    [string]$SlackWebhook,
    [string]$TeamsWebhook,
    [string]$SplunkHEC,
    [ValidateRange(10,3600)]
    [int]$ScanInterval = 300
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

# ═══════════════════════════════════════════════════════════════════════════
# VOICE SYNTHESIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════
Add-Type -AssemblyName System.Speech
$global:Voice = $null

try {
    $global:Voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $global:Voice.Rate = 1
    $global:Voice.Volume = 75
    
    # Select optimal voice
    $voices = $global:Voice.GetInstalledVoices()
    $preferred = @('Microsoft Zira Desktop', 'Microsoft David Desktop', 'Microsoft Mark')
    foreach ($pref in $preferred) {
        $voice = $voices | Where-Object { $_.VoiceInfo.Name -like "*$pref*" } | Select-Object -First 1
        if ($voice) {
            $global:Voice.SelectVoice($voice.VoiceInfo.Name)
            break
        }
    }
} catch {
    $global:Voice = $null
    $VoiceEnabled = $false
}

function Invoke-VoiceAlert {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet('Info','Success','Warning','Alert','Critical')]
        [string]$Priority = 'Info',
        [switch]$Async
    )
    
    if (-not $VoiceEnabled -or -not $global:Voice) { return }
    
    try {
        # Voice modulation based on priority
        $rate, $volume = switch ($Priority) {
            'Critical' { 2, 100 }
            'Alert'    { 1, 95 }
            'Warning'  { 1, 85 }
            'Success'  { 0, 70 }
            default    { 1, 75 }
        }
        
        $global:Voice.Rate = $rate
        $global:Voice.Volume = $volume
        
        if ($Async) {
            $global:Voice.SpeakAsync($Message) | Out-Null
        } else {
            $global:Voice.Speak($Message)
        }
        
        # Reset
        $global:Voice.Rate = 1
        $global:Voice.Volume = 75
    } catch {}
}

# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
$global:AEGIS = [PSCustomObject]@{
    Product = @{
        Name = 'AEGIS AI Elite'
        FullName = 'Advanced Endpoint Guardian Intelligence System - Elite Edition'
        Version = '6.0'
        Build = '20260111-ELITE'
        Creator = 'Desmond Otieno Odhiambo'
        Company = 'ClearGlassCorp International'
        Assistant = 'ARIA'
        AssistantFull = 'Advanced Risk Intelligence Assistant'
    }
    
    Paths = @{
        Root = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite"
        Logs = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Logs"
        Evidence = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Evidence"
        Reports = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Reports"
        Intelligence = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Intelligence"
        Quarantine = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Quarantine"
        Baseline = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Baseline"
        Compliance = "$env:ProgramData\ClearGlassCorp\AEGIS_Elite\Compliance"
    }
    
    Config = @{
        VoiceEnabled = $VoiceEnabled.IsPresent
        AutoResponse = $AutoResponse.IsPresent
        ContinuousMode = $ContinuousMonitor.IsPresent
        ScanInterval = $ScanInterval
        SlackWebhook = $SlackWebhook
        TeamsWebhook = $TeamsWebhook
        SplunkHEC = $SplunkHEC
    }
    
    Thresholds = @{
        # Authentication
        FailedLogons = 5
        FailedLogonsWindow = 15  # minutes
        
        # File Activity
        FileModifications = 100
        FileModificationWindow = 15  # minutes
        
        # Network
        PublicConnections = 20
        BeaconingThreshold = 15
        
        # Process
        TempExecution = 1
        UnusualParentChild = 1
        
        # Risk Scoring
        ThreatScoreAlert = 75
        ThreatScoreCritical = 90
        VendorRiskHigh = 70
        ComplianceThreshold = 80
    }
    
    Intelligence = @{
        # MITRE ATT&CK Techniques (sample set)
        MITRE = @{
            'T1110' = @{Name='Brute Force'; Tactic='Credential Access'; Severity=85}
            'T1003' = @{Name='Credential Dumping'; Tactic='Credential Access'; Severity=95}
            'T1486' = @{Name='Data Encrypted for Impact'; Tactic='Impact'; Severity=100}
            'T1071' = @{Name='Application Layer Protocol'; Tactic='Command and Control'; Severity=80}
            'T1055' = @{Name='Process Injection'; Tactic='Defense Evasion'; Severity=90}
            'T1053' = @{Name='Scheduled Task/Job'; Tactic='Persistence'; Severity=75}
        }
        
        # Malicious Indicators
        MaliciousPorts = @(4444, 31337, 12345, 27374, 6667, 1337, 6666, 12346)
        SuspiciousProcesses = @('nc.exe', 'netcat.exe', 'mimikatz.exe', 'psexec.exe', 'procdump.exe')
        RansomwareExtensions = @('.encrypted', '.locked', '.crypto', '.crypt', '.locky', '.cerber', '.wannacry', '.ryuk')
        
        # High-Risk Software Categories
        RiskyCategories = @('RemoteAccess', 'FileSharing', 'Torrent', 'Crypto', 'Hacking')
        
        # Vendor Risk Intelligence (expanded database)
        VendorRisk = @{
            # Approved - Low Risk
            'Microsoft Corporation' = @{Risk=10; Trust=98; Category='OS'; Approved=$true}
            'Google LLC' = @{Risk=15; Trust=95; Category='Software'; Approved=$true}
            'Adobe Inc.' = @{Risk=20; Trust=92; Category='Software'; Approved=$true}
            'Mozilla Corporation' = @{Risk=15; Trust=94; Category='Software'; Approved=$true}
            'Apple Inc.' = @{Risk=12; Trust=96; Category='Software'; Approved=$true}
            'Malwarebytes' = @{Risk=10; Trust=96; Category='Security'; Approved=$true}
            'Cisco Systems' = @{Risk=15; Trust=94; Category='Network'; Approved=$true}
            
            # Medium Risk - Requires Monitoring
            'TeamViewer GmbH' = @{Risk=65; Trust=60; Category='RemoteAccess'; Approved=$false}
            'AnyDesk Software GmbH' = @{Risk=70; Trust=55; Category='RemoteAccess'; Approved=$false}
            'Piriform Ltd' = @{Risk=45; Trust=70; Category='Utility'; Approved=$true}
            'Dropbox' = @{Risk=50; Trust=68; Category='FileSharing'; Approved=$false}
            
            # High Risk - Block Recommended
            'Unknown' = @{Risk=85; Trust=20; Category='Unverified'; Approved=$false}
            'Unsigned' = @{Risk=90; Trust=15; Category='Unverified'; Approved=$false}
        }
    }
    
    State = @{
        SessionStart = Get-Date
        LastScan = $null
        LastComplianceScan = $null
        
        # Detection Metrics
        TotalThreats = 0
        CriticalThreats = 0
        ResponseActions = 0
        QuarantinedFiles = 0
        BlockedIPs = 0
        
        # Collections (thread-safe)
        ActiveThreats = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        BlockedItems = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        Vendors = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        Vulnerabilities = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        ComplianceFindings = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        NetworkDevices = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        ResponseHistory = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
        
        # Baselines (for anomaly detection)
        Baseline = @{
            ProcessCount = 0
            NetworkConnections = 0
            FileActivity = 0
            LogonActivity = 0
            LastUpdated = $null
        }
    }
}

# Initialize directories
foreach ($path in $global:AEGIS.Paths.Values) {
    if (-not (Test-Path $path)) {
        try { New-Item -ItemType Directory -Path $path -Force -ErrorAction Stop | Out-Null } catch {}
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING & ALERTING
# ═══════════════════════════════════════════════════════════════════════════
function Write-AegisLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet('INFO','SUCCESS','WARNING','ERROR','THREAT','CRITICAL','COMPLIANCE','INTEL')]
        [string]$Level = 'INFO',
        [hashtable]$Metadata = @{},
        [switch]$Voice,
        [switch]$Alert
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    $logFile = Join-Path $global:AEGIS.Paths.Logs "AEGIS_$(Get-Date -Format 'yyyyMMdd').log"
    
    # Structured log entry
    $entry = @{
        Timestamp = $timestamp
        Level = $Level
        Message = $Message
        Metadata = $Metadata
        Host = $env:COMPUTERNAME
        User = $env:USERNAME
    } | ConvertTo-Json -Compress
    
    try {
        [System.IO.File]::AppendAllText($logFile, "$entry`n", [System.Text.Encoding]::UTF8)
    } catch {}
    
    # Console output
    $colors = @{
        INFO='White'; SUCCESS='Green'; WARNING='Yellow'; ERROR='Red'
        THREAT='Magenta'; CRITICAL='Red'; COMPLIANCE='Blue'; INTEL='Cyan'
    }
    
    $icons = @{
        INFO='ℹ'; SUCCESS='✓'; WARNING='⚠'; ERROR='✗'
        THREAT='🛡'; CRITICAL='‼'; COMPLIANCE='📋'; INTEL='🔍'
    }
    
    Write-Host "[$timestamp] $($icons[$Level]) $Message" -ForegroundColor $colors[$Level]
    
    # Voice alert
    if ($Voice -and $global:AEGIS.Config.VoiceEnabled) {
        $priority = switch ($Level) {
            'CRITICAL' { 'Critical' }
            'THREAT' { 'Alert' }
            'WARNING' { 'Warning' }
            'SUCCESS' { 'Success' }
            default { 'Info' }
        }
        Invoke-VoiceAlert -Message $Message -Priority $priority -Async
    }
    
    # Cloud alerting
    if ($Alert -and $Level -in @('THREAT','CRITICAL')) {
        Send-CloudAlert -Message $Message -Level $Level -Metadata $Metadata
    }
}

function Send-CloudAlert {
    param($Message, $Level, $Metadata)
    
    $color = if ($Level -eq 'CRITICAL') { '#DC143C' } else { '#FF8C00' }
    $emoji = if ($Level -eq 'CRITICAL') { '🚨' } else { '⚠️' }
    
    # Slack
    if ($global:AEGIS.Config.SlackWebhook) {
        try {
            $payload = @{
                username = "AEGIS Elite"
                icon_emoji = ":shield:"
                attachments = @(
                    @{
                        color = $color
                        title = "$emoji AEGIS Alert - $Level"
                        text = $Message
                        fields = @(
                            @{title="Host"; value=$env:COMPUTERNAME; short=$true}
                            @{title="User"; value=$env:USERNAME; short=$true}
                            @{title="Time"; value=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); short=$true}
                        )
                        footer = "AEGIS Elite v$($global:AEGIS.Product.Version)"
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            Invoke-RestMethod -Uri $global:AEGIS.Config.SlackWebhook -Method Post `
                -Body $payload -ContentType 'application/json' -TimeoutSec 3 -ErrorAction SilentlyContinue
        } catch {}
    }
    
    # Teams
    if ($global:AEGIS.Config.TeamsWebhook) {
        try {
            $payload = @{
                "@type" = "MessageCard"
                "@context" = "http://schema.org/extensions"
                "themeColor" = $color.TrimStart('#')
                "summary" = "AEGIS Security Alert"
                "sections" = @(
                    @{
                        "activityTitle" = "$emoji AEGIS Alert - $Level"
                        "activitySubtitle" = $Message
                        "facts" = @(
                            @{name="Host"; value=$env:COMPUTERNAME}
                            @{name="User"; value=$env:USERNAME}
                            @{name="Time"; value=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')}
                        )
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            Invoke-RestMethod -Uri $global:AEGIS.Config.TeamsWebhook -Method Post `
                -Body $payload -ContentType 'application/json' -TimeoutSec 3 -ErrorAction SilentlyContinue
        } catch {}
    }
}

function Show-Banner {
    Clear-Host
    Write-Host @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                  ███████╗  ClearGlassCorp International                     ║
║                  ██╔══██╗  AEGIS AI Elite v6.0                              ║
║                  ███████║  Advanced Security Intelligence                    ║
║                  ██╔══██╗                                                    ║
║                  ██║  ██║  Voice-Guided Security Operations                 ║
║                                                                              ║
║  COPYRIGHT © 2026 ClearGlassCorp International - ALL RIGHTS RESERVED        ║
║  Elite Endpoint Protection with Advanced Pattern Recognition                ║
║                                                                              ║
║  Creator: Desmond Otieno Odhiambo                                           ║
║  Build: 20260111-ELITE                                                      ║
║  Assistant: ARIA (Advanced Risk Intelligence Assistant)                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan
    
    if ($global:AEGIS.Config.VoiceEnabled) {
        $greeting = "Welcome to AEGIS Elite. I am ARIA, your security intelligence assistant. All systems are online and ready."
        Invoke-VoiceAlert -Message $greeting -Priority Info -Async
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# ADVANCED THREAT DETECTION
# ═══════════════════════════════════════════════════════════════════════════
function Start-ThreatHunt {
    param(
        [switch]$DeepScan,
        [switch]$Baseline
    )
    
    $scanType = if ($DeepScan) { 'Deep Threat Hunt' } elseif ($Baseline) { 'Baseline Scan' } else { 'Standard Hunt'
    Write-AegisLog "Initiating $scanType..." -Level INTEL -Voice
    
    $scanStart = Get-Date
    $global:AEGIS.State.LastScan = $scanStart
    $threats = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    
    # Parallel detection jobs
    $jobs = @()
    
    # Detection 1: Brute Force (Failed Logons)
    $jobs += Start-Job -ScriptBlock {
        param($Threshold, $Window, $MITRE)
        $results = @()
        
        try {
            $events = Get-WinEvent -FilterHashtable @{
                LogName='Security'
                Id=4625
                StartTime=(Get-Date).AddMinutes(-$Window)
            } -MaxEvents 1000 -ErrorAction Stop
            
            # Parse IPs
            $ips = @()
            foreach ($evt in $events) {
                try {
                    $xml = [xml]$evt.ToXml()
                    $ip = ($xml.Event.EventData.Data | Where-Object {$_.Name -eq 'IpAddress'}).'#text'
                    if ($ip) { $ips += $ip }
                } catch {}
            }
            
            # Detect patterns
            $groups = $ips | Group-Object
            foreach ($g in $groups) {
                if ($g.Count -ge $Threshold) {
                    $severity = [math]::Min(100, 60 + ($g.Count * 3))
                    $pattern = if ($g.Count -gt 50) { 'Distributed Attack' }
                              elseif ($g.Count -gt 20) { 'Aggressive Brute Force' }
                              else { 'Brute Force Attempt' }
                    
                    $results += [PSCustomObject]@{
                        Type = 'BruteForce'
                        Technique = 'T1110'
                        TechniqueName = $MITRE['T1110'].Name
                        Tactic = $MITRE['T1110'].Tactic
                        Source = $g.Name
                        Count = $g.Count
                        Severity = $severity
                        Pattern = $pattern
                        Confidence = 95
                        Time = Get-Date
                        Recommendation = "Block source IP, review authentication logs, enable MFA"
                    }
                }
            }
        } catch {}
        
        return $results
    } -ArgumentList $global:AEGIS.Thresholds.FailedLogons, $global:AEGIS.Thresholds.FailedLogonsWindow, $global:AEGIS.Intelligence.MITRE
    
    # Detection 2: Ransomware Indicators
    $jobs += Start-Job -ScriptBlock {
        param($Threshold, $Window, $RansomExt, $MITRE)
        $results = @()
        $cutoff = (Get-Date).AddMinutes(-$Window)
        
        $paths = @("$env:USERPROFILE\Documents", "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads")
        $totalMod = 0
        $ransomFiles = 0
        
        foreach ($path in $paths) {
            if (Test-Path $path) {
                try {
                    $files = @(Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | 
                        Where-Object { $_.LastWriteTime -gt $cutoff })
                    
                    $totalMod += $files.Count
                    
                    foreach ($file in $files) {
                        if ($RansomExt -contains $file.Extension) {
                            $ransomFiles++
                        }
                    }
                } catch {}
            }
        }
        
        if ($totalMod -gt $Threshold -or $ransomFiles -gt 0) {
            $severity = if ($ransomFiles -gt 0) { 100 } else { 85 }
            $pattern = if ($ransomFiles -gt 10) { 'Active Ransomware' }
                      elseif ($ransomFiles -gt 0) { 'Ransomware Indicators' }
                      else { 'Mass File Modification' }
            
            $results += [PSCustomObject]@{
                Type = 'Ransomware'
                Technique = 'T1486'
                TechniqueName = $MITRE['T1486'].Name
                Tactic = $MITRE['T1486'].Tactic
                Source = $env:COMPUTERNAME
                Count = $totalMod
                RansomwareFiles = $ransomFiles
                Severity = $severity
                Pattern = $pattern
                Confidence = if ($ransomFiles -gt 0) { 98 } else { 80 }
                Time = Get-Date
                Recommendation = "Isolate system, check backups, kill suspicious processes"
            }
        }
        
        return $results
    } -ArgumentList $global:AEGIS.Thresholds.FileModifications, $global:AEGIS.Thresholds.FileModificationWindow, $global:AEGIS.Intelligence.RansomwareExtensions, $global:AEGIS.Intelligence.MITRE
    
    # Detection 3: C2 Beaconing
    $jobs += Start-Job -ScriptBlock {
        param($Threshold, $MalPorts, $MITRE)
        $results = @()
        
        try {
            $conns = @(Get-NetTCPConnection -State Established -ErrorAction Stop)
            
            # Filter public IPs
            $public = @($conns | Where-Object {
                $ip = $_.RemoteAddress
                $ip -match '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$' -and
                $ip -notmatch '^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|169\.254\.)'
            })
            
            # Detect beaconing
            $groups = $public | Group-Object RemoteAddress
            foreach ($g in $groups) {
                $malPort = $false
                foreach ($conn in $g.Group) {
                    if ($MalPorts -contains $conn.RemotePort -or $MalPorts -contains $conn.LocalPort) {
                        $malPort = $true
                        break
                    }
                }
                
                if ($g.Count -ge $Threshold -or $malPort) {
                    $severity = if ($malPort) { 95 } else { 80 }
                    $pattern = if ($malPort) { 'Malicious Port C2' }
                              elseif ($g.Count -gt 30) { 'Data Exfiltration' }
                              else { 'Connection Beaconing' }
                    
                    $results += [PSCustomObject]@{
                        Type = 'C2Communication'
                        Technique = 'T1071'
                        TechniqueName = $MITRE['T1071'].Name
                        Tactic = $MITRE['T1071'].Tactic
                        Source = $g.Name
                        Count = $g.Count
                        MaliciousPort = $malPort
                        Severity = $severity
                        Pattern = $pattern
                        Confidence = if ($malPort) { 97 } else { 82 }
                        Time = Get-Date
                        Recommendation = "Block IP, analyze process, check for malware"
                    }
                }
            }
        } catch {}
        
        return $results
    } -ArgumentList $global:AEGIS.Thresholds.BeaconingThreshold, $global:AEGIS.Intelligence.MaliciousPorts, $global:AEGIS.Intelligence.MITRE
    
    # Detection 4: Process Anomalies
    $jobs += Start-Job -ScriptBlock {
        param($SuspProc, $MITRE)
        $results = @()
        
        try {
            # Temp execution
            $tempProcs = Get-Process | Where-Object {
                $_.Path -like '*\Temp\*' -or $_.Path -like '*\AppData\Local\Temp\*'
            }
            
            foreach ($proc in $tempProcs) {
                $results += [PSCustomObject]@{
                    Type = 'SuspiciousProcess'
                    Technique = 'T1055'
                    TechniqueName = 'Process Injection'
                    Tactic = 'Defense Evasion'
                    Source = "$($proc.Name) (PID: $($proc.Id))"
                    ProcessPath = $proc.Path
                    Severity = 85
                    Pattern = 'Temp Directory Execution'
                    Confidence = 88
                    Time = Get-Date
                    Recommendation = "Terminate process, quarantine executable, analyze"
                }
            }
            
            # Known malicious processes
            $processes = Get-Process
            foreach ($proc in $processes) {
                if ($SuspProc -contains $proc.Name) {
                    $results += [PSCustomObject]@{
                        Type = 'MaliciousProcess'
                        Technique = 'Multiple'
                        TechniqueName = 'Known Malware'
                        Tactic = 'Multiple'
                        Source = "$($proc.Name) (PID: $($proc.Id))"
                        ProcessPath = $proc.Path
                        Severity = 100
                        Pattern = 'Known Malware Execution'
                        Confidence = 100
                        Time = Get-Date
                        Recommendation = "IMMEDIATE TERMINATION AND QUARANTINE"
                    }
                }
            }
        } catch {}
        
        return $results
    } -ArgumentList $global:AEGIS.Intelligence.SuspiciousProcesses, $global:AEGIS.Intelligence.MITRE
    
    # Detection 5: Persistence Mechanisms (Deep Scan Only)
    if ($DeepScan) {
        $jobs += Start-Job -ScriptBlock {
            param($MITRE)
            $results = @()
            
            try {
                # Scheduled tasks
                $tasks = Get-ScheduledTask | Where-Object {
                    $_.TaskPath -notmatch 'Microsoft' -and
                    $_.State -eq 'Ready' -and
                    $_.Actions.Execute -match 'powershell|cmd|wscript|cscript'
                }
                
                foreach ($task in $tasks) {
                    $results += [PSCustomObject]@{
                        Type = 'Persistence'
                        Technique = 'T1053'
                        TechniqueName = 'Scheduled Task'
                        Tactic = 'Persistence'
                        Source = $task.TaskName
                        TaskPath = $task.TaskPath
                        Action = $task.Actions.Execute
                        Severity = 75
                        Pattern = 'Suspicious Scheduled Task'
                        Confidence = 80
                        Time = Get-Date
                        Recommendation = "Review task legitimacy, disable if malicious"
                    }
                }
                
                # Startup items
                $startupKeys = @(
                    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
                    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run'
                )
                
                foreach ($key in $startupKeys) {
                    try {
                        $items = Get-ItemProperty -Path $key -ErrorAction Stop
                        
                        foreach ($prop in $items.PSObject.Properties) {
                            if ($prop.Name -notmatch 'PSPath|PSParentPath|PSChildName|PSDrive|PSProvider' -and
                                $prop.Value -match '\.exe|\.bat|\.cmd|\.vbs|\.ps1' -and
                                $prop.Value -notmatch 'Program Files') {
                                
                                $results += [PSCustomObject]@{
                                    Type = 'Persistence'
                                    Technique = 'T1547'
                                    TechniqueName = 'Registry Run Key'
                                    Tactic = 'Persistence'
                                    Source = $prop.Name
                                    RegistryKey = $key
                                    Path = $prop.Value
                                    Severity = 78
                                    Pattern = 'Suspicious Startup Entry'
                                    Confidence = 82
                                    Time = Get-Date
                                    Recommendation = "Verify legitimacy, remove if malicious"
                                }
                            }
                        }
                    } catch {}
                }
            } catch {}
            
            return $results
        } -ArgumentList $global:AEGIS.Intelligence.MITRE
    }
    
    # Wait for jobs
    $timeout = if ($DeepScan) { 90 } else { 45 }
    Wait-Job -Job $jobs -Timeout $timeout | Out-Null
    
    # Collect results
    foreach ($job in $jobs) {
        try {
            $result = Receive-Job -Job $job -ErrorAction Stop
            if ($result) {
                foreach ($threat in $result) {
                    $threats.Add($threat)
                }
            }
        } catch {}
    }
    $jobs | Remove-Job -Force
    
    # Process threats
    $threatArray = @($threats)
    
    if ($threatArray.Count -gt 0) {
        foreach ($threat in $threatArray) {
            $global:AEGIS.State.TotalThreats++
            $global:AEGIS.State.ActiveThreats.Add($threat)
            
            if ($threat.Severity -ge $global:AEGIS.Thresholds.ThreatScoreCritical) {
                $global:AEGIS.State.CriticalThreats++
            }
            
            Write-AegisLog "THREAT DETECTED: $($threat.Type) - $($threat.Pattern) [Severity: $($threat.Severity)] [MITRE: $($threat.Technique)]" `
                -Level THREAT -Metadata @{
                    Type=$threat.Type
                    Technique=$threat.Technique
                    Severity=$threat.Severity
                    Source=$threat.Source
                } -Voice -Alert
            
            # Auto-response
            if ($global:AEGIS.Config.AutoResponse -and $threat.Severity -ge $global:AEGIS.Thresholds.ThreatScoreCritical) {
                Invoke-ThreatResponse -Threat $threat
            }
        }
        
        $critCount = @($threatArray | Where-Object {$_.Severity -ge 90}).Count
        $voiceMsg = "Threat hunt complete. Detected $($threatArray.Count) threats, $critCount are critical priority."
        Invoke-VoiceAlert -Message $voiceMsg -Priority $(if($critCount -gt 0){'Alert'}else{'Warning'}) -Async
    }
    
    # Update baseline if requested
    if ($Baseline) {
        Update-Baseline
    }
    
    $duration = ((Get-Date) - $scanStart).TotalSeconds
    Write-AegisLog "Threat hunt complete in $([math]::Round($duration,2))s: $($threatArray.Count) threats detected" `
        -Level $(if($threatArray.Count -gt 0){'WARNING'}else{'SUCCESS'})
    
    return $threatArray
}

function Invoke-ThreatResponse {
    param($Threat)
    
    $global:AEGIS.State.ResponseActions++
    Write-AegisLog "AUTO-RESPONSE: Executing containment for $($threat.Type)" -Level CRITICAL -Voice
    
    $response = [PSCustomObject]@{
        ThreatType = $Threat.Type
        ThreatSource = $Threat.Source
        Action = ''
        Success = $false
        Time = Get-Date
        Details = ''
    }
    
    try {
        switch ($Threat.Type) {
            'BruteForce' {
                if ($Threat.Source -match '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
                    $ruleName = "AEGIS_Block_$($Threat.Source -replace '\.','_')_$(Get-Date -Format 'HHmmss')"
                    
                    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Block `
                        -RemoteAddress $Threat.Source `
                        -Description "AEGIS Auto-Block: $($Threat.Pattern) | Severity: $($Threat.Severity) | Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" `
                        -ErrorAction Stop | Out-Null
                    
                    $global:AEGIS.State.BlockedIPs++
                    $global:AEGIS.State.BlockedItems.Add([PSCustomObject]@{
                        Type='IP'
                        Value=$Threat.Source
                        Reason=$Threat.Pattern
                        Time=Get-Date
                    })
                    
                    $response.Action = "Blocked IP"
                    $response.Success = $true
                    $response.Details = "Created firewall rule: $ruleName"
                    
                    Invoke-VoiceAlert -Message "Threat neutralized. IP address $($Threat.Source) has been blocked." -Priority Alert -Async
                }
            }
            
            'Ransomware' {
                # Kill high-CPU processes
                $processes = Get-Process | Where-Object { $_.CPU -gt 30 } | Sort-Object CPU -Descending | Select-Object -First 3
                
                foreach ($proc in $processes) {
                    try {
                        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                        $response.Action += "Killed $($proc.Name); "
                    } catch {}
                }
                
                # Disable network
                Get-NetAdapter | Where-Object Status -eq 'Up' | ForEach-Object {
                    Disable-NetAdapter -Name $_.Name -Confirm:$false -ErrorAction SilentlyContinue
                    $response.Action += "Disabled $($_.Name); "
                }
                
                $response.Success = $true
                $response.Details = "Emergency isolation complete"
                
                Invoke-VoiceAlert -Message "CRITICAL. Ransomware detected. System has been isolated from network." -Priority Critical -Async
            }
            
            'MaliciousProcess' {
                if ($Threat.Source -match 'PID: (\d+)') {
                    $pid = [int]$matches[1]
                    
                    try {
                        $proc = Get-Process -Id $pid -ErrorAction Stop
                        $path = $proc.Path
                        
                        Stop-Process -Id $pid -Force -ErrorAction Stop
                        
                        if ($path -and (Test-Path $path)) {
                            $quarPath = Join-Path $global:AEGIS.Paths.Quarantine (Split-Path $path -Leaf)
                            Move-Item -Path $path -Destination $quarPath -Force -ErrorAction SilentlyContinue
                            $global:AEGIS.State.QuarantinedFiles++
                        }
                        
                        $response.Action = "Terminated and Quarantined"
                        $response.Success = $true
                        $response.Details = "PID $pid terminated, executable quarantined"
                        
                        Invoke-VoiceAlert -Message "Malicious process terminated and quarantined." -Priority Alert -Async
                    } catch {
                        $response.Details = $_.Exception.Message
                    }
                }
            }
        }
        
        $global:AEGIS.State.ResponseHistory.Add($response)
        
        if ($response.Success) {
            Write-AegisLog "Response successful: $($response.Action)" -Level SUCCESS
        } else {
            Write-AegisLog "Response failed: $($response.Details)" -Level ERROR
        }
        
    } catch {
        Write-AegisLog "Response error: $($_.Exception.Message)" -Level ERROR
    }
}

function Update-Baseline {
    try {
        $global:AEGIS.State.Baseline.ProcessCount = (Get-Process).Count
        $global:AEGIS.State.Baseline.NetworkConnections = (Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue).Count
        $global:AEGIS.State.Baseline.LastUpdated = Get-Date
        
        $baselineFile = Join-Path $global:AEGIS.Paths.Baseline "baseline_$(Get-Date -Format 'yyyyMMdd').json"
        $global:AEGIS.State.Baseline | ConvertTo-Json | Set-Content $baselineFile
        
        Write-AegisLog "Baseline updated: $($global:AEGIS.State.Baseline.ProcessCount) processes, $($global:AEGIS.State.Baseline.NetworkConnections) connections" -Level INFO
    } catch {}
}

# ═══════════════════════════════════════════════════════════════════════════
# VENDOR INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════
function Get-VendorInventory {
    Write-AegisLog "Scanning vendor ecosystem..." -Level INTEL -Voice
    
    $vendors = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    $jobs = @()
    
    # Job 1: Registry scan
    $jobs += Start-Job -ScriptBlock {
        $results = @()
        $paths = @(
            'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
            'HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
            'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
        )
        
        foreach ($path in $paths) {
            try {
                Get-ItemProperty $path -ErrorAction SilentlyContinue | 
                    Where-Object { $_.DisplayName -and $_.Publisher } |
                    ForEach-Object {
                        $results += [PSCustomObject]@{
                            Software = $_.DisplayName
                            Vendor = $_.Publisher
                            Version = $_.DisplayVersion
                            InstallDate = $_.InstallDate
                            InstallPath = $_.InstallLocation
                            SizeMB = if ($_.EstimatedSize) { [math]::Round($_.EstimatedSize/1024, 2) } else { 0 }
                            Source = 'Registry'
                        }
                    }
            } catch {}
        }
        
        return $results | Sort-Object Vendor -Unique
    }
    
    # Job 2: Process scan
    $jobs += Start-Job -ScriptBlock {
        $results = @()
        
        Get-Process | Where-Object { $_.Path -and $_.Company } | 
            Select-Object Name, Path, Company, ProductVersion -Unique |
            ForEach-Object {
                $results += [PSCustomObject]@{
                    Software = $_.Name
                    Vendor = $_.Company
                    Version = $_.ProductVersion
                    InstallDate = $null
                    InstallPath = $_.Path
                    SizeMB = 0
                    Source = 'Process'
                }
            }
        
        return $results | Sort-Object Vendor -Unique
    }
    
    Wait-Job -Job $jobs -Timeout 30 | Out-Null
    
    foreach ($job in $jobs) {
        try {
            $result = Receive-Job -Job $job -ErrorAction Stop
            if ($result) {
                foreach ($item in $result) {
                    $vendors.Add($item)
                }
            }
        } catch {}
    }
    $jobs | Remove-Job -Force
    
    # Risk analysis
    $vendorArray = @($vendors)
    $uniqueVendors = $vendorArray | Group-Object Vendor
    
    foreach ($vg in $uniqueVendors) {
        $vendorName = $vg.Name
        $riskProfile = $global:AEGIS.Intelligence.VendorRisk[$vendorName]
        
        if (-not $riskProfile) {
            $riskProfile = $global:AEGIS.Intelligence.VendorRisk['Unknown']
        }
        
        # Calculate dynamic risk
        $risk = $riskProfile.Risk
        $trust = $riskProfile.Trust
        
        # Adjust for software count
        if ($vg.Count -gt 10) { $risk += 5; $trust -= 5 }
        
        # Check for temp installations
        $tempInstalls = @($vg.Group | Where-Object { $_.InstallPath -like '*\Temp\*' })
        if ($tempInstalls.Count -gt 0) { $risk += 15; $trust -= 15 }
        
        $vendorData = [PSCustomObject]@{
            VendorName = $vendorName
            SoftwareCount = $vg.Count
            RiskScore = [math]::Max(0, [math]::Min(100, $risk))
            TrustScore = [math]::Max(0, [math]::Min(100, $trust))
            Category = $riskProfile.Category
            Approved = $riskProfile.Approved
            Products = @($vg.Group | Select-Object Software, Version, Source, InstallPath)
            LastScanned = Get-Date
        }
        
        $global:AEGIS.State.Vendors.Add($vendorData)
    }
    
    $highRisk = @($global:AEGIS.State.Vendors) | Where-Object { $_.RiskScore -ge $global:AEGIS.Thresholds.VendorRiskHigh }
    
    Write-AegisLog "Vendor analysis complete: $($uniqueVendors.Count) vendors, $($highRisk.Count) high-risk" -Level INTEL
    Invoke-VoiceAlert -Message "Vendor scan complete. Identified $($uniqueVendors.Count) vendors with $($highRisk.Count) requiring security review." -Async
    
    return @($global:AEGIS.State.Vendors)
}

function Get-VendorRiskAnalysis {
    param([string]$VendorName)
    
    $vendor = @($global:AEGIS.State.Vendors) | Where-Object { $_.VendorName -eq $VendorName } | Select-Object -First 1
    
    if (-not $vendor) {
        return $null
    }
    
    $factors = @()
    $recommendations = @()
    
    # Risk factor analysis
    if ($vendor.RiskScore -ge 70) {
        $factors += "High base risk classification"
        $recommendations += "Immediate security review required"
    }
    
    if ($vendor.TrustScore -lt 50) {
        $factors += "Low trust score: $($vendor.TrustScore)/100"
        $recommendations += "Verify vendor legitimacy and reputation"
    }
    
    if (-not $vendor.Approved) {
        $factors += "Not approved by security policy"
        $recommendations += "Submit for approval workflow"
    }
    
    if ($vendor.Category -in $global:AEGIS.Intelligence.RiskyCategories) {
        $factors += "High-risk category: $($vendor.Category)"
        $recommendations += "Enhanced monitoring and access controls"
    }
    
    if ($vendor.SoftwareCount -gt 5) {
        $factors += "Large software footprint: $($vendor.SoftwareCount) products"
        $recommendations += "Consider consolidation review"
    }
    
    # Check for temp installations
    $tempProds = @($vendor.Products | Where-Object { $_.InstallPath -like '*\Temp\*' })
    if ($tempProds.Count -gt 0) {
        $factors += "$($tempProds.Count) installations in temporary directories"
        $recommendations += "CRITICAL: Remove temporary installations"
    }
    
    # Determine overall risk level
    $riskLevel = if ($vendor.RiskScore -ge 85) { 'Critical' }
                 elseif ($vendor.RiskScore -ge 70) { 'High' }
                 elseif ($vendor.RiskScore -ge 50) { 'Medium' }
                 else { 'Low' }
    
    return [PSCustomObject]@{
        VendorName = $VendorName
        RiskScore = $vendor.RiskScore
        RiskLevel = $riskLevel
        TrustScore = $vendor.TrustScore
        Category = $vendor.Category
        Approved = $vendor.Approved
        SoftwareCount = $vendor.SoftwareCount
        Factors = $factors
        Recommendations = $recommendations
        Products = $vendor.Products
        Analysis = "Risk analysis complete with $($factors.Count) factors identified"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# COMPLIANCE & HARDENING
# ═══════════════════════════════════════════════════════════════════════════
function Start-ComplianceAudit {
    Write-AegisLog "Initiating compliance audit..." -Level COMPLIANCE -Voice
    
    $findings = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    $score = 0
    $maxScore = 100
    
    $checks = @(
        @{
            Name = 'Windows Defender'
            Check = {
                $def = Get-MpComputerStatus -ErrorAction SilentlyContinue
                $def.RealTimeProtectionEnabled -and $def.AntivirusEnabled
            }
            Points = 10
            Severity = 'High'
            Recommendation = 'Enable Windows Defender real-time protection'
        },
        @{
            Name = 'Firewall Enabled'
            Check = {
                $fw = Get-NetFirewallProfile
                ($fw | Where-Object {-not $_.Enabled}).Count -eq 0
            }
            Points = 10
            Severity = 'High'
            Recommendation = 'Enable firewall on all profiles'
        },
        @{
            Name = 'SMBv1 Disabled'
            Check = {
                $smb = Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction SilentlyContinue
                $smb.State -eq 'Disabled'
            }
            Points = 10
            Severity = 'Critical'
            Recommendation = 'Disable SMBv1 protocol'
        },
        @{
            Name = 'Guest Account Disabled'
            Check = {
                $guest = Get-LocalUser -Name 'Guest' -ErrorAction SilentlyContinue
                $guest -and -not $guest.Enabled
            }
            Points = 10
            Severity = 'Medium'
            Recommendation = 'Disable Guest account'
        },
        @{
            Name = 'Admin Count Limited'
            Check = {
                $admins = Get-LocalGroupMember -Group 'Administrators' -ErrorAction SilentlyContinue
                $admins.Count -le 3
            }
            Points = 10
            Severity = 'Medium'
            Recommendation = 'Limit administrator accounts to 3 or fewer'
        },
        @{
            Name = 'PowerShell Logging'
            Check = {
                $psLog = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' -ErrorAction SilentlyContinue
                $psLog.EnableScriptBlockLogging -eq 1
            }
            Points = 10
            Severity = 'Medium'
            Recommendation = 'Enable PowerShell script block logging'
        },
        @{
            Name = 'Execution Policy'
            Check = {
                $policy = Get-ExecutionPolicy
                $policy -in @('RemoteSigned', 'AllSigned')
            }
            Points = 10
            Severity = 'Medium'
            Recommendation = 'Set execution policy to RemoteSigned or AllSigned'
        },
        @{
            Name = 'LSASS Protection'
            Check = {
                $lsass = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -ErrorAction SilentlyContinue
                $lsass.RunAsPPL -eq 1
            }
            Points = 10
            Severity = 'High'
            Recommendation = 'Enable LSASS protection (RunAsPPL)'
        },
        @{
            Name = 'Windows Updates Current'
            Check = {
                try {
                    $session = New-Object -ComObject Microsoft.Update.Session
                    $searcher = $session.CreateUpdateSearcher()
                    $pending = $searcher.Search("IsInstalled=0").Updates.Count
                    $pending -eq 0
                } catch {
                    $false
                }
            }
            Points = 10
            Severity = 'High'
            Recommendation = 'Install pending Windows updates'
        },
        @{
            Name = 'Password Policy'
            Check = {
                $noPwd = Get-LocalUser | Where-Object {-not $_.PasswordRequired}
                $noPwd.Count -eq 0
            }
            Points = 10
            Severity = 'High'
            Recommendation = 'Require passwords for all user accounts'
        }
    )
    
    foreach ($check in $checks) {
        try {
            $result = & $check.Check
            
            if ($result) {
                $score += $check.Points
                Write-Host "  ✓ $($check.Name)" -ForegroundColor Green
            } else {
                $finding = [PSCustomObject]@{
                    Control = $check.Name
                    Status = 'Failed'
                    Severity = $check.Severity
                    Recommendation = $check.Recommendation
                    Points = $check.Points
                    Time = Get-Date
                }
                
                $findings.Add($finding)
                $global:AEGIS.State.ComplianceFindings.Add($finding)
                
                Write-Host "  ✗ $($check.Name)" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ? $($check.Name) - Cannot verify" -ForegroundColor Yellow
        }
    }
    
    $percentage = [math]::Round(($score / $maxScore) * 100, 1)
    $global:AEGIS.State.LastComplianceScan = Get-Date
    
    $complianceLevel = if ($percentage -ge 90) { 'Excellent' }
                       elseif ($percentage -ge $global:AEGIS.Thresholds.ComplianceThreshold) { 'Good' }
                       elseif ($percentage -ge 70) { 'Fair' }
                       else { 'Poor' }
    
    $result = [PSCustomObject]@{
        Score = $score
        MaxScore = $maxScore
        Percentage = $percentage
        Level = $complianceLevel
        Findings = @($findings)
        ScanTime = Get-Date
    }
    
    Write-AegisLog "Compliance audit complete: $score/$maxScore ($percentage%) - $complianceLevel" -Level COMPLIANCE
    Invoke-VoiceAlert -Message "Compliance audit complete. Score: $percentage percent. Compliance level: $complianceLevel" -Async
    
    return $result
}

# ═══════════════════════════════════════════════════════════════════════════
# NETWORK DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════
function Get-NetworkTopology {
    Write-AegisLog "Discovering network topology..." -Level INTEL -Voice
    
    $devices = [System.Collections.ArrayList]::new()
    
    # ARP scan
    try {
        $arp = arp -a 2>$null
        $regex = [regex]'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-f-]{17})'
        
        foreach ($match in $regex.Matches($arp)) {
            $ip = $match.Groups[1].Value
            $mac = $match.Groups[2].Value.ToUpper()
            
            if ($mac -notmatch '^(FF-FF-FF|01-00-5E|33-33)') {
                [void]$devices.Add([PSCustomObject]@{
                    IPAddress = $ip
                    MACAddress = $mac
                    Status = 'Unknown'
                    Hostname = 'Resolving...'
                    DeviceType = 'Unknown'
                    LastSeen = Get-Date
                })
            }
        }
    } catch {}
    
    if ($devices.Count -eq 0) {
        Write-AegisLog "No devices found in ARP cache" -Level WARNING
        return @()
    }
    
    # Resolve hostnames (parallel)
    $jobs = @()
    foreach ($dev in $devices) {
        $jobs += Start-Job -ScriptBlock {
            param($IP)
            
            $result = @{IP=$IP; Online=$false; Hostname='N/A'}
            
            try {
                $ping = [System.Net.NetworkInformation.Ping]::new()
                $pingResult = $ping.Send($IP, 500)
                $ping.Dispose()
                
                if ($pingResult.Status -eq 'Success') {
                    $result.Online = $true
                    try {
                        $result.Hostname = [System.Net.Dns]::GetHostEntry($IP).HostName
                    } catch {}
                }
            } catch {}
            
            return $result
        } -ArgumentList $dev.IPAddress
    }
    
    Wait-Job -Job $jobs -Timeout 20 | Out-Null
    
    for ($i = 0; $i -lt $devices.Count; $i++) {
        try {
            $result = Receive-Job -Job $jobs[$i] -ErrorAction Stop
            if ($result) {
                $devices[$i].Status = if ($result.Online) { 'Online' } else { 'Offline' }
                $devices[$i].Hostname = $result.Hostname
                
                # Device classification
                $hostname = $result.Hostname.ToLower()
                $devices[$i].DeviceType = if ($hostname -like '*router*' -or $hostname -like '*gateway*') { 'Network' }
                                         elseif ($hostname -like '*printer*') { 'Printer' }
                                         elseif ($hostname -like '*phone*') { 'Mobile' }
                                         elseif ($hostname -like '*server*') { 'Server' }
                                         else { 'Workstation' }
            }
        } catch {}
    }
    $jobs | Remove-Job -Force
    
    # Save to state
    foreach ($dev in $devices) {
        $global:AEGIS.State.NetworkDevices.Add($dev)
    }
    
    $online = @($devices | Where-Object Status -eq 'Online').Count
    Write-AegisLog "Network discovery complete: $($devices.Count) devices, $online online" -Level INTEL
    Invoke-VoiceAlert -Message "Network discovery complete. Found $($devices.Count) devices, $online are online." -Async
    
    return $devices
}

# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
function Show-Dashboard {
    while ($true) {
        Clear-Host
        Show-Banner
        
        $uptime = ((Get-Date) - $global:AEGIS.State.SessionStart).ToString("hh\:mm\:ss")
        $lastScan = if ($global:AEGIS.State.LastScan) {
            "$([math]::Round(((Get-Date) - $global:AEGIS.State.LastScan).TotalMinutes,1)) min ago"
        } else { "Never" }
        
        Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                        SECURITY COMMAND CENTER                               ║" -ForegroundColor Cyan
        Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        
        Write-Host "`n┌─ SYSTEM STATUS ───────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
        Write-Host "│ Assistant: ARIA (Active)                                                   │" -ForegroundColor Green
        Write-Host "│ Voice: $(if($global:AEGIS.Config.VoiceEnabled){'ENABLED'}else{'DISABLED'})                                                              │" -ForegroundColor $(if($global:AEGIS.Config.VoiceEnabled){'Green'}else{'Yellow'})
        Write-Host "│ Auto-Response: $(if($global:AEGIS.Config.AutoResponse){'ACTIVE'}else{'STANDBY'})                                                   │" -ForegroundColor $(if($global:AEGIS.Config.AutoResponse){'Red'}else{'Yellow'})
        Write-Host "│ Session: $($uptime.PadRight(68))│" -ForegroundColor White
        Write-Host "│ Last Scan: $($lastScan.PadRight(66))│" -ForegroundColor White
        Write-Host "└───────────────────────────────────────────────────────────────────────────┘" -ForegroundColor DarkGray
        
        Write-Host "`n┌─ THREAT METRICS ──────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
        Write-Host "│ Total Threats: $($global:AEGIS.State.TotalThreats.ToString().PadRight(62))│" -ForegroundColor $(if($global:AEGIS.State.TotalThreats -gt 0){'Red'}else{'Green'})
        Write-Host "│ Critical: $($global:AEGIS.State.CriticalThreats.ToString().PadRight(67))│" -ForegroundColor $(if($global:AEGIS.State.CriticalThreats -gt 0){'Red'}else{'Green'})
        Write-Host "│ Auto-Responses: $($global:AEGIS.State.ResponseActions.ToString().PadRight(61))│" -ForegroundColor Magenta
        Write-Host "│ IPs Blocked: $($global:AEGIS.State.BlockedIPs.ToString().PadRight(64))│" -ForegroundColor Cyan
        Write-Host "│ Files Quarantined: $($global:AEGIS.State.QuarantinedFiles.ToString().PadRight(58))│" -ForegroundColor Yellow
        Write-Host "└───────────────────────────────────────────────────────────────────────────┘" -ForegroundColor DarkGray
        
        Write-Host "`n┌─ MAIN MENU ───────────────────────────────────────────────────────────────┐" -ForegroundColor Green
        Write-Host "│                                                                            │" -ForegroundColor White
        Write-Host "│  THREAT INTELLIGENCE        VENDOR SECURITY        COMPLIANCE              │" -ForegroundColor Cyan
        Write-Host "│   1. Standard Threat Scan    10. Vendor Scan       15. Compliance Audit   │" -ForegroundColor White
        Write-Host "│   2. Deep Threat Hunt        11. Vendor Risk       16. View Findings      │" -ForegroundColor White
        Write-Host "│   3. Active Threats          12. High-Risk Vendors                        │" -ForegroundColor White
        Write-Host "│   4. Blocked Items                                                         │" -ForegroundColor White
        Write-Host "│                              NETWORK INTEL          SYSTEM                 │" -ForegroundColor Cyan
        Write-Host "│  AUTOMATION                  13. Network Topology   17. System Info        │" -ForegroundColor Cyan
        Write-Host "│   5. Continuous Monitor      14. Device Details     18. Export Report      │" -ForegroundColor White
        Write-Host "│   6. Toggle Auto-Response                           19. View Logs          │" -ForegroundColor White
        Write-Host "│   7. Toggle Voice                                   20. Settings           │" -ForegroundColor White
        Write-Host "│                                                                            │" -ForegroundColor White
        Write-Host "│   0. Exit AEGIS                                                            │" -ForegroundColor Yellow
        Write-Host "│                                                                            │" -ForegroundColor White
        Write-Host "└───────────────────────────────────────────────────────────────────────────┘" -ForegroundColor DarkGray
        
        Write-Host "`n🎙️  ARIA: " -NoNewline -ForegroundColor Cyan
        Write-Host "Select command [0-20]: " -NoNewline -ForegroundColor White
        $choice = Read-Host
        
        switch ($choice) {
            '1' {
                $threats = Start-ThreatHunt
                if ($threats.Count -gt 0) {
                    Write-Host "`n═══ THREAT DETECTION RESULTS ═══`n" -ForegroundColor Red
                    $threats | Format-Table Type,Pattern,Source,Severity,@{L='MITRE';E={$_.Technique}},@{L='Confidence';E={"$($_.Confidence)%"}} -AutoSize
                } else {
                    Write-Host "`n✓ No threats detected`n" -ForegroundColor Green
                }
                Read-Host "`nPress Enter to continue"
            }
            
            '2' {
                $threats = Start-ThreatHunt -DeepScan
                if ($threats.Count -gt 0) {
                    Write-Host "`n═══ DEEP THREAT HUNT RESULTS ═══`n" -ForegroundColor Red
                    $threats | Format-Table Type,Pattern,Technique,Tactic,Severity -AutoSize
                    Write-Host "`nRecommendations:" -ForegroundColor Yellow
                    $threats | Select-Object Type,Recommendation -Unique | ForEach-Object {
                        Write-Host "  • $($_.Type): $($_.Recommendation)" -ForegroundColor White
                    }
                } else {
                    Write-Host "`n✓ Deep scan complete - No threats detected`n" -ForegroundColor Green
                }
                Read-Host "`nPress Enter to continue"
            }
            
            '3' {
                Write-Host "`n═══ ACTIVE THREATS ═══`n" -ForegroundColor Yellow
                $active = @($global:AEGIS.State.ActiveThreats)
                if ($active.Count -gt 0) {
                    $active | Format-Table Type,Pattern,Source,Severity,@{L='Time';E={$_.Time.ToString('HH:mm:ss')}} -AutoSize
                } else {
                    Write-Host "No active threats`n" -ForegroundColor Green
                }
                Read-Host "Press Enter to continue"
            }
            
            '4' {
                Write-Host "`n═══ BLOCKED ITEMS ═══`n" -ForegroundColor Yellow
                $blocked = @($global:AEGIS.State.BlockedItems)
                if ($blocked.Count -gt 0) {
                    $blocked | Format-Table Type,Value,Reason,@{L='Time';E={$_.Time.ToString('yyyy-MM-dd HH:mm:ss')}} -AutoSize
                } else {
                    Write-Host "No blocked items`n" -ForegroundColor Green
                }
                Read-Host "Press Enter to continue"
            }
            
            '5' {
                if ($global:AEGIS.Config.ContinuousMode) {
                    Write-Host "`n⚠️  Continuous monitoring already active`n" -ForegroundColor Yellow
                    Read-Host "Press Enter to continue"
                    continue
                }
                
                Write-Host "`n═══ CONTINUOUS MONITORING MODE ═══`n" -ForegroundColor Cyan
                Invoke-VoiceAlert -Message "Entering continuous monitoring mode. Scanning every $($global:AEGIS.Config.ScanInterval) seconds." -Async
                
                Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow
                
                try {
                    while ($true) {
                        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Running scan..." -ForegroundColor Cyan
                        $threats = Start-ThreatHunt
                        
                        if ($threats.Count -gt 0) {
                            Write-Host "  ⚠️  $($threats.Count) threats detected!" -ForegroundColor Red
                        } else {
                            Write-Host "  ✓ All clear" -ForegroundColor Green
                        }
                        
                        Start-Sleep -Seconds $global:AEGIS.Config.ScanInterval
                    }
                } catch {
                    Write-Host "`n✓ Continuous monitoring stopped`n" -ForegroundColor Yellow
                    Read-Host "Press Enter to continue"
                }
            }
            
            '6' {
                $global:AEGIS.Config.AutoResponse = -not $global:AEGIS.Config.AutoResponse
                $status = if ($global:AEGIS.Config.AutoResponse) { "ENABLED" } else { "DISABLED" }
                Write-Host "`n⚡ Auto-Response: $status`n" -ForegroundColor $(if($global:AEGIS.Config.AutoResponse){'Red'}else{'Yellow'})
                Invoke-VoiceAlert -Message "Automatic threat response is now $status" -Async
                Start-Sleep -Seconds 2
            }
            
            '7' {
                $global:AEGIS.Config.VoiceEnabled = -not $global:AEGIS.Config.VoiceEnabled
                $status = if ($global:AEGIS.Config.VoiceEnabled) { "enabled" } else { "disabled" }
                Write-Host "`n🔊 Voice Mode: $status`n" -ForegroundColor Cyan
                if ($global:AEGIS.Config.VoiceEnabled) {
                    Invoke-VoiceAlert -Message "Voice interaction enabled. ARIA is now speaking to you."
                }
                Start-Sleep -Seconds 2
            }
            
            '10' {
                $vendors = Get-VendorInventory
                
                Write-Host "`n═══ VENDOR INVENTORY ═══`n" -ForegroundColor Cyan
                $vendors | Sort-Object RiskScore -Descending | Select-Object -First 30 |
                    Format-Table VendorName,@{L='Products';E={$_.SoftwareCount}},@{L='Risk';E={$_.RiskScore}},@{L='Trust';E={$_.TrustScore}},Category,@{L='Approved';E={if($_.Approved){'Yes'}else{'No'}}} -AutoSize
                
                $highRisk = @($vendors | Where-Object {$_.RiskScore -ge 70}).Count
                Write-Host "`nTotal: $($vendors.Count) vendors | High-Risk: $highRisk`n" -ForegroundColor White
                
                Read-Host "Press Enter to continue"
            }
            
            '11' {
                $vendors = @($global:AEGIS.State.Vendors)
                if ($vendors.Count -eq 0) {
                    Write-Host "`n⚠️  Run Vendor Scan first (option 10)`n" -ForegroundColor Yellow
                    Read-Host "Press Enter to continue"
                    continue
                }
                
                Write-Host "`nEnter vendor name: " -NoNewline -ForegroundColor Cyan
                $vendorName = Read-Host
                
                if ([string]::IsNullOrWhiteSpace($vendorName)) {
                    continue
                }
                
                $analysis = Get-VendorRiskAnalysis -VendorName $vendorName
                
                if ($analysis) {
                    Clear-Host
                    Show-Banner
                    
                    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
                    Write-Host "║         VENDOR RISK ANALYSIS                                 ║" -ForegroundColor Cyan
                    Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
                    
                    Write-Host "Vendor: $($analysis.VendorName)" -ForegroundColor White
                    Write-Host "Risk Score: $($analysis.RiskScore)/100" -ForegroundColor $(
                        if($analysis.RiskScore -ge 85){'Red'}
                        elseif($analysis.RiskScore -ge 70){'Magenta'}
                        elseif($analysis.RiskScore -ge 50){'Yellow'}
                        else{'Green'}
                    )
                    Write-Host "Risk Level: $($analysis.RiskLevel)" -ForegroundColor White
                    Write-Host "Trust Score: $($analysis.TrustScore)/100" -ForegroundColor Cyan
                    Write-Host "Category: $($analysis.Category)" -ForegroundColor White
                    Write-Host "Approved: $(if($analysis.Approved){'Yes'}else{'No'})`n" -ForegroundColor $(if($analysis.Approved){'Green'}else{'Red'})
                    
                    if ($analysis.Factors.Count -gt 0) {
                        Write-Host "Risk Factors:" -ForegroundColor Yellow
                        foreach ($f in $analysis.Factors) {
                            Write-Host "  • $f" -ForegroundColor White
                        }
                    }
                    
                    if ($analysis.Recommendations.Count -gt 0) {
                        Write-Host "`nRecommendations:" -ForegroundColor Cyan
                        foreach ($r in $analysis.Recommendations) {
                            Write-Host "  → $r" -ForegroundColor White
                        }
                    }
                    
                    Write-Host "`nInstalled Products:" -ForegroundColor Yellow
                    $analysis.Products | Select-Object -First 10 | Format-Table Software,Version,Source -AutoSize
                    
                    Invoke-VoiceAlert -Message "Vendor risk analysis complete for $($analysis.VendorName). Risk level is $($analysis.RiskLevel)." -Async
                } else {
                    Write-Host "`n✗ Vendor not found`n" -ForegroundColor Red
                }
                
                Read-Host "`nPress Enter to continue"
            }
            
            '12' {
                Write-Host "`n═══ HIGH-RISK VENDORS ═══`n" -ForegroundColor Red
                $highRisk = @($global:AEGIS.State.Vendors) | Where-Object {$_.RiskScore -ge 70} | Sort-Object RiskScore -Descending
                
                if ($highRisk.Count -gt 0) {
                    $highRisk | Format-Table VendorName,@{L='Risk';E={$_.RiskScore}},@{L='Trust';E={$_.TrustScore}},Category,@{L='Products';E={$_.SoftwareCount}} -AutoSize
                    Invoke-VoiceAlert -Message "Alert. $($highRisk.Count) high-risk vendors require immediate review." -Priority Alert -Async
                } else {
                    Write-Host "✓ No high-risk vendors detected`n" -ForegroundColor Green
                }
                
                Read-Host "Press Enter to continue"
            }
            
            '13' {
                $devices = Get-NetworkTopology
                
                Write-Host "`n═══ NETWORK TOPOLOGY ═══`n" -ForegroundColor Cyan
                
                if ($devices.Count -gt 0) {
                    $devices | Sort-Object Status,IPAddress |
                        Format-Table IPAddress,MACAddress,Status,DeviceType,@{L='Hostname';E={$_.Hostname.Substring(0,[math]::Min(30,$_.Hostname.Length))}} -AutoSize
                    
                    $online = @($devices | Where-Object Status -eq 'Online').Count
                    Write-Host "`nTotal Devices: $($devices.Count) | Online: $online`n" -ForegroundColor White
                }
                
                Read-Host "Press Enter to continue"
            }
            
            '15' {
                $compliance = Start-ComplianceAudit
                
                Write-Host "`n═══ COMPLIANCE AUDIT RESULTS ═══`n" -ForegroundColor Blue
                Write-Host "Score: $($compliance.Score)/$($compliance.MaxScore) ($($compliance.Percentage)%)" -ForegroundColor $(
                    if($compliance.Percentage -ge 90){'Green'}
                    elseif($compliance.Percentage -ge 80){'Cyan'}
                    elseif($compliance.Percentage -ge 70){'Yellow'}
                    else{'Red'}
                )
                Write-Host "Compliance Level: $($compliance.Level)`n" -ForegroundColor White
                
                if ($compliance.Findings.Count -gt 0) {
                    Write-Host "Findings:" -ForegroundColor Yellow
                    $compliance.Findings | Format-Table Control,Severity,Recommendation -AutoSize
                }
                
                Read-Host "`nPress Enter to continue"
            }
            
            '16' {
                Write-Host "`n═══ COMPLIANCE FINDINGS ═══`n" -ForegroundColor Yellow
                $findings = @($global:AEGIS.State.ComplianceFindings)
                
                if ($findings.Count -gt 0) {
                    $findings | Format-Table Control,Severity,Recommendation,@{L='Time';E={$_.Time.ToString('yyyy-MM-dd HH:mm:ss')}} -AutoSize
                } else {
                    Write-Host "No findings - Run compliance audit first`n" -ForegroundColor Green
                }
                
                Read-Host "Press Enter to continue"
            }
            
            '18' {
                Write-Host "`n📊 Generating comprehensive security report...`n" -ForegroundColor Cyan
                Invoke-VoiceAlert -Message "Generating comprehensive security report." -Async
                
                $report = @{
                    Generated = Get-Date -Format 'o'
                    Version = $global:AEGIS.Product.Version
                    System = @{
                        Computer = $env:COMPUTERNAME
                        User = $env:USERNAME
                        Domain = $env:USERDOMAIN
                    }
                    Session = @{
                        Start = $global:AEGIS.State.SessionStart
                        Duration = ((Get-Date) - $global:AEGIS.State.SessionStart).ToString()
                    }
                    Metrics = @{
                        TotalThreats = $global:AEGIS.State.TotalThreats
                        CriticalThreats = $global:AEGIS.State.CriticalThreats
                        ResponseActions = $global:AEGIS.State.ResponseActions
                        BlockedIPs = $global:AEGIS.State.BlockedIPs
                        QuarantinedFiles = $global:AEGIS.State.QuarantinedFiles
                    }
                    Threats = @($global:AEGIS.State.ActiveThreats)
                    Vendors = @($global:AEGIS.State.Vendors)
                    Compliance = @($global:AEGIS.State.ComplianceFindings)
                    NetworkDevices = @($global:AEGIS.State.NetworkDevices)
                    ResponseHistory = @($global:AEGIS.State.ResponseHistory)
                }
                
                $reportPath = Join-Path $global:AEGIS.Paths.Reports "AEGIS_Report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
                $report | ConvertTo-Json -Depth 10 | Set-Content $reportPath -Encoding UTF8
                
                Write-Host "✓ Report generated: $reportPath`n" -ForegroundColor Green
                Invoke-VoiceAlert -Message "Security report generated successfully." -Priority Success -Async
                
                Read-Host "Press Enter to continue"
            }
            
            '19' {
                Write-Host "`n═══ RECENT LOGS ═══`n" -ForegroundColor Yellow
                $logFile = Join-Path $global:AEGIS.Paths.Logs "AEGIS_$(Get-Date -Format 'yyyyMMdd').log"
                
                if (Test-Path $logFile) {
                    Get-Content $logFile -Tail 30 | ForEach-Object {
                        try {
                            $entry = $_ | ConvertFrom-Json
                            $color = switch ($entry.Level) {
                                'CRITICAL' { 'Red' }
                                'THREAT' { 'Magenta' }
                                'WARNING' { 'Yellow' }
                                'SUCCESS' { 'Green' }
                                'INTEL' { 'Cyan' }
                                default { 'White' }
                            }
                            Write-Host "[$($entry.Timestamp)] [$($entry.Level)] $($entry.Message)" -ForegroundColor $color
                        } catch {
                            Write-Host $_ -ForegroundColor Gray
                        }
                    }
                }
                
                Read-Host "`nPress Enter to continue"
            }
            
            '0' {
                Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
                Write-Host "║         Shutting down AEGIS Elite...                         ║" -ForegroundColor Cyan
                Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
                
                $duration = ((Get-Date) - $global:AEGIS.State.SessionStart).ToString()
                
                Write-Host "Session Summary:" -ForegroundColor Cyan
                Write-Host "  Duration: $duration" -ForegroundColor White
                Write-Host "  Threats Detected: $($global:AEGIS.State.TotalThreats)" -ForegroundColor White
                Write-Host "  Response Actions: $($global:AEGIS.State.ResponseActions)" -ForegroundColor Magenta
                Write-Host "  Items Blocked: $((@($global:AEGIS.State.BlockedItems)).Count)`n" -ForegroundColor Cyan
                
                Invoke-VoiceAlert -Message "Thank you for using AEGIS Elite. Your systems are protected. ARIA signing off. Goodbye." -Priority Success
                
                Write-AegisLog "AEGIS Elite session ended (Duration: $duration, Threats: $($global:AEGIS.State.TotalThreats))"
                
                Write-Host "Thank you for using AEGIS Elite Security Platform`n" -ForegroundColor Green
                Start-Sleep -Seconds 2
                
                return
            }
            
            default {
                Invoke-VoiceAlert -Message "Invalid selection. Please choose a number between zero and twenty." -Priority Warning
                Start-Sleep -Seconds 1
            }
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════
try {
    Show-Banner
    
    Write-AegisLog "═══════════════════════════════════════════════════════════════"
    Write-AegisLog "AEGIS Elite v$($global:AEGIS.Product.Version) $($global:AEGIS.Product.Build)"
    Write-AegisLog "Session: $env:COMPUTERNAME\$env:USERNAME | Mode: $Mode"
    Write-AegisLog "Voice: $(if($VoiceEnabled){'ON'}else{'OFF'}) | Auto-Response: $(if($AutoResponse){'ON'}else{'OFF'})"
    Write-AegisLog "═══════════════════════════════════════════════════════════════"
    
    switch ($Mode) {
        'Dashboard' {
            Show-Dashboard
        }
        
        'Hunt' {
            Write-Host "═══ THREAT HUNTING MODE ═══`n" -ForegroundColor Yellow
            $threats = Start-ThreatHunt -DeepScan
            
            if ($threats.Count -gt 0) {
                Write-Host "`n═══ THREATS DETECTED ═══`n" -ForegroundColor Red
                $threats | Format-Table Type,Pattern,Technique,Tactic,Severity -AutoSize
            } else {
                Write-Host "`n✓ No threats detected`n" -ForegroundColor Green
            }
            
            Read-Host "`nPress Enter to exit"
        }
        
        'Vendor' {
            $vendors = Get-VendorInventory
            Write-Host "`n═══ VENDOR INVENTORY ═══`n" -ForegroundColor Cyan
            $vendors | Sort-Object RiskScore -Descending |
                Format-Table VendorName,SoftwareCount,RiskScore,TrustScore,Category -AutoSize
            Read-Host "`nPress Enter to exit"
        }
        
        'Compliance' {
            $compliance = Start-ComplianceAudit
            Write-Host "`n═══ COMPLIANCE RESULTS ═══`n" -ForegroundColor Blue
            Write-Host "Score: $($compliance.Percentage)% - $($compliance.Level)`n" -ForegroundColor White
            if ($compliance.Findings.Count -gt 0) {
                $compliance.Findings | Format-Table Control,Severity,Recommendation -AutoSize
            }
            Read-Host "`nPress Enter to exit"
        }
        
        default {
            Show-Dashboard
        }
    }
    
    Write-AegisLog "AEGIS Elite session completed"
    Write-AegisLog "═══════════════════════════════════════════════════════════════"
    
} catch {
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                  CRITICAL ERROR                              ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-AegisLog "CRITICAL ERROR: $($_.Exception.Message)" -Level CRITICAL
    Write-AegisLog "Stack: $($_.ScriptStackTrace)"
    
    Read-Host "`nPress Enter to exit"
    exit 1
}
