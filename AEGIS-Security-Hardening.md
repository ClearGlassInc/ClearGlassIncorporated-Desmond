# AEGIS v6.0 - Security Hardening Guide

## 🔐 Executive Summary

This guide provides comprehensive security hardening procedures for AEGIS-protected systems. Following these recommendations will achieve defense-in-depth by combining AEGIS threat detection with operating system and network hardening.

**Target Security Score**: 95%+  
**Hardening Time**: 2-4 hours per system  
**Maintenance**: Quarterly review

---

## Table of Contents

1. [Security Layers](#security-layers)
2. [Pre-Hardening Assessment](#pre-hardening-assessment)
3. [Operating System Hardening](#operating-system-hardening)
4. [AEGIS Configuration](#aegis-configuration)
5. [Network Security](#network-security)
6. [Application Hardening](#application-hardening)
7. [Monitoring & Logging](#monitoring--logging)
8. [Compliance Frameworks](#compliance-frameworks)
9. [Validation & Testing](#validation--testing)
10. [Incident Response](#incident-response)

---

## Security Layers

AEGIS implements a **multi-layered defense strategy**:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Perimeter Defense                            │
│  • Firewall rules                                      │
│  • Network segmentation                                │
│  • Threat intelligence IP blocking                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Operating System Hardening                   │
│  • Patch management                                    │
│  • Service minimization                                │
│  • Privilege management                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: AEGIS Real-Time Detection                    │
│  • Behavioral analysis                                 │
│  • Threat intelligence                                 │
│  • ML anomaly detection                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Automated Response                           │
│  • Network isolation                                   │
│  • Process termination                                 │
│  • Forensic collection                                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Monitoring & Forensics                       │
│  • Centralized logging                                 │
│  • SIEM integration                                    │
│  • Incident documentation                              │
└─────────────────────────────────────────────────────────┘
```

---

## Pre-Hardening Assessment

### 1. Run Initial Security Audit

```powershell
# Run AEGIS security audit
.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit

# Document current score
# Target: Identify gaps to address
```

### 2. Inventory System

```powershell
# System information
Get-ComputerInfo | Select-Object CsName, WindowsVersion, OsArchitecture

# Installed applications
Get-Package | Select-Object Name, Version

# Running services
Get-Service | Where-Object Status -eq 'Running' | Select-Object Name, DisplayName

# Network adapters
Get-NetAdapter | Select-Object Name, Status, LinkSpeed

# Scheduled tasks
Get-ScheduledTask | Where-Object State -eq 'Ready'
```

### 3. Document Current State

Create baseline documentation:
- Current security score
- Installed software
- Network configuration
- User accounts
- Service configuration

---

## Operating System Hardening

### Windows Defender Configuration

#### Enable All Protection Features

```powershell
# Enable real-time protection
Set-MpPreference -DisableRealtimeMonitoring $false

# Enable cloud-delivered protection
Set-MpPreference -MAPSReporting Advanced
Set-MpPreference -SubmitSamplesConsent SendAllSamples

# Enable network protection
Set-MpPreference -EnableNetworkProtection Enabled

# Enable controlled folder access (ransomware protection)
Set-MpPreference -EnableControlledFolderAccess Enabled

# Add protected folders
Add-MpPreference -ControlledFolderAccessProtectedFolders "C:\Users\*\Documents"
Add-MpPreference -ControlledFolderAccessProtectedFolders "C:\Users\*\Desktop"

# Enable exploit protection
Set-ProcessMitigation -System -Enable DEP,SEHOP,ForceRelocateImages

# Update definitions
Update-MpSignature
```

#### Configure Scanning

```powershell
# Schedule daily quick scan
$action = New-ScheduledTaskAction -Execute "C:\Program Files\Windows Defender\MpCmdRun.exe" -Argument "-Scan -ScanType 1"
$trigger = New-ScheduledTaskTrigger -Daily -At "01:00AM"
Register-ScheduledTask -TaskName "Defender-QuickScan" -Action $action -Trigger $trigger -User "SYSTEM"

# Schedule weekly full scan
$action = New-ScheduledTaskAction -Execute "C:\Program Files\Windows Defender\MpCmdRun.exe" -Argument "-Scan -ScanType 2"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "02:00AM"
Register-ScheduledTask -TaskName "Defender-FullScan" -Action $action -Trigger $trigger -User "SYSTEM"
```

---

### Disable Vulnerable Protocols

#### SMBv1 (CRITICAL)

```powershell
# Disable SMBv1
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# Verify disabled
Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# Block SMBv1 via registry (additional protection)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name "SMB1" -Value 0 -Type DWord
```

#### PowerShell v2

```powershell
# Disable PowerShell v2
Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root -NoRestart

# Verify disabled
Get-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root
```

#### LLMNR and NetBIOS

```powershell
# Disable LLMNR
New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -Value 0

# Disable NetBIOS over TCP/IP
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled=true"
foreach ($adapter in $adapters) {
    $adapter.SetTcpipNetbios(2)  # 2 = Disable
}
```

---

### LSASS Protection (Critical)

```powershell
# Enable LSASS protection (prevents credential dumping)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RunAsPPL" -Value 1 -PropertyType DWORD -Force

# Enable Credential Guard (Windows 10 Enterprise/Server 2016+)
# Requires UEFI and Virtualization-Based Security
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart

# Via Group Policy (for domain):
# Computer Configuration → Administrative Templates → System → Device Guard
# Turn On Virtualization Based Security: Enabled
# Credential Guard Configuration: Enabled with UEFI lock
```

**Note**: LSASS protection and Credential Guard require system restart.

---

### Audit Policies (Enhanced Logging)

```powershell
# Enable comprehensive auditing
auditpol /set /category:"Account Logon" /success:enable /failure:enable
auditpol /set /category:"Account Management" /success:enable /failure:enable
auditpol /set /category:"Detailed Tracking" /success:enable /failure:enable
auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable
auditpol /set /category:"Object Access" /success:enable /failure:enable
auditpol /set /category:"Policy Change" /success:enable /failure:enable
auditpol /set /category:"Privilege Use" /success:enable /failure:enable
auditpol /set /category:"System" /success:enable /failure:enable

# Specific subcategories critical for AEGIS
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
auditpol /set /subcategory:"Registry" /success:enable /failure:enable
auditpol /set /subcategory:"File System" /success:enable /failure:enable
auditpol /set /subcategory:"Filtering Platform Connection" /success:enable /failure:enable

# Verify configuration
auditpol /get /category:*
```

---

### PowerShell Security

```powershell
# Enable PowerShell script block logging
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force
}
Set-ItemProperty -Path $regPath -Name "EnableScriptBlockLogging" -Value 1

# Enable module logging
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force
}
Set-ItemProperty -Path $regPath -Name "EnableModuleLogging" -Value 1

# Log all modules
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging\ModuleNames"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force
}
Set-ItemProperty -Path $regPath -Name "*" -Value "*"

# Enable transcription (optional - generates large logs)
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force
}
Set-ItemProperty -Path $regPath -Name "EnableTranscripting" -Value 1
Set-ItemProperty -Path $regPath -Name "OutputDirectory" -Value "C:\PSTranscripts"

# Set execution policy
Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
```

---

### Account Security

#### Disable Unnecessary Accounts

```powershell
# Disable Guest account
Disable-LocalUser -Name "Guest"

# Disable built-in Administrator (create named admin instead)
# Only if you have another admin account!
Rename-LocalUser -Name "Administrator" -NewName "SystemAdmin"
Disable-LocalUser -Name "SystemAdmin"

# List all local users
Get-LocalUser | Select-Object Name, Enabled, LastLogon
```

#### Password Policy

```powershell
# Set password policy (via Group Policy or net accounts)
net accounts /minpwlen:14
net accounts /maxpwage:90
net accounts /minpwage:1
net accounts /uniquepw:5

# Enforce complexity (via Group Policy)
# Computer Configuration → Windows Settings → Security Settings → Account Policies → Password Policy
# Password must meet complexity requirements: Enabled
```

#### Remove Excessive Privileges

```powershell
# Review administrators
Get-LocalGroupMember -Group "Administrators"

# Remove unnecessary users from Administrators group
Remove-LocalGroupMember -Group "Administrators" -Member "username"

# Review Remote Desktop Users
Get-LocalGroupMember -Group "Remote Desktop Users"
```

---

### Service Hardening

#### Disable Unnecessary Services

```powershell
# Identify running services
Get-Service | Where-Object {$_.Status -eq 'Running' -and $_.StartType -ne 'Disabled'} | 
    Select-Object Name, DisplayName, StartType

# Disable unnecessary services (examples - verify before disabling)
$servicesToDisable = @(
    'RemoteRegistry',      # Remote Registry
    'Browser',             # Computer Browser
    'WinRM',               # Windows Remote Management (if not needed)
    'TapiSrv',             # Telephony
    'fax',                 # Fax
    'WerSvc',              # Windows Error Reporting (optional)
    'WSearch'              # Windows Search (if not needed)
)

foreach ($service in $servicesToDisable) {
    if (Get-Service -Name $service -ErrorAction SilentlyContinue) {
        Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
        Set-Service -Name $service -StartupType Disabled
        Write-Host "Disabled: $service"
    }
}
```

**Critical Services to Keep Running**:
- Windows Defender (WinDefend, SecurityHealthService)
- Windows Update (wuauserv, UsoSvc)
- Event Log (EventLog)
- Cryptographic Services (CryptSvc)
- Windows Firewall (mpssvc)

---

### Registry Hardening

```powershell
# Disable AutoRun
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" -Name "NoDriveTypeAutoRun" -Value 255

# Disable Windows Script Host for non-admins
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows Script Host\Settings" -Name "Enabled" -Value 0

# Enable UAC
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -Value 1

# Require Admin approval for elevation
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -Value 2

# Enable ASLR (Address Space Layout Randomization)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name "MoveImages" -Value 1

# Disable anonymous SID enumeration
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RestrictAnonymousSAM" -Value 1
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RestrictAnonymous" -Value 1

# Prevent storing LAN Manager hashes
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "NoLMHash" -Value 1
```

---

## AEGIS Configuration

### Maximum Security Profile (Burlington Mode)

```powershell
# Deploy with maximum hardening
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy -Burlington -AutoRemediate

# Configure features
$env:AEGIS_ABUSEIPDB_KEY = "your-api-key"
$env:AEGIS_VIRUSTOTAL_KEY = "your-api-key"

# Launch with all protections
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard `
    -ThreatIntelligence `
    -MLDetection `
    -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK"
```

### Optimal Detection Thresholds

Configure in AEGIS script or via Dashboard settings:

```powershell
# Burlington Mode Thresholds (Strictest):
FailedLogons = 2              # vs 5 in standard mode
FileModifications = 50        # vs 100 in standard mode
NetworkConnections = 15       # Same in both modes
PrivilegeEvents = 3           # Same in both modes
LsassAccess = 1               # Same in both modes
AnomalyScore = 75             # ML detection trigger
ThreatIntelScore = 75         # Threat intel confidence
```

### Automated Baseline Collection

```powershell
# Create scheduled task for baseline collection
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-File `"C:\Program Files\AEGIS\AEGIS-v6.0-Enhanced.ps1`" -Mode Dashboard -MLDetection"

# Trigger: Every 4 hours
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "AEGIS-BaselineCollection" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User "SYSTEM" `
    -RunLevel Highest
```

### Alert Configuration

```powershell
# Configure multi-channel alerting

# 1. Slack (real-time)
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -SlackWebhook "https://hooks.slack.com/..."

# 2. Email alerts via Task Scheduler
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument @"
-Command "
Get-ChildItem 'C:\ProgramData\ClearGlassCorp\AEGIS\Logs\Incidents' -Filter *.json |
    Where-Object {`$_.LastWriteTime -gt (Get-Date).AddMinutes(-10)} |
    ForEach-Object {
        `$data = Get-Content `$_.FullName | ConvertFrom-Json
        Send-MailMessage -To 'security@company.com' -From 'aegis@company.com' -Subject 'AEGIS Alert' -Body (`$data | ConvertTo-Json) -SmtpServer 'mail.company.com'
    }
"
"@

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName "AEGIS-EmailAlerts" -Action $action -Trigger $trigger -User "SYSTEM"
```

---

## Network Security

### Windows Firewall Configuration

#### Enable All Profiles

```powershell
# Enable firewall for all profiles
Set-NetFirewallProfile -All -Enabled True

# Set default actions
Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultInboundAction Block -DefaultOutboundAction Allow

# Log dropped packets
Set-NetFirewallProfile -All -LogAllowed False -LogBlocked True -LogFileName "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
```

#### Block Vulnerable Ports

```powershell
# Block common attack vectors
$blockedPorts = @(
    @{Port=135; Protocol='TCP'; Name='RPC'},
    @{Port=137; Protocol='UDP'; Name='NetBIOS-NS'},
    @{Port=138; Protocol='UDP'; Name='NetBIOS-DGM'},
    @{Port=139; Protocol='TCP'; Name='NetBIOS-SSN'},
    @{Port=445; Protocol='TCP'; Name='SMB'},  # Only if not needed internally
    @{Port=1900; Protocol='UDP'; Name='SSDP'},
    @{Port=5355; Protocol='UDP'; Name='LLMNR'}
)

foreach ($port in $blockedPorts) {
    New-NetFirewallRule -DisplayName "Block-$($port.Name)" `
        -Direction Inbound `
        -LocalPort $port.Port `
        -Protocol $port.Protocol `
        -Action Block `
        -ErrorAction SilentlyContinue
}
```

#### Allow Only Required Services

```powershell
# Example: Allow RDP only from management network
New-NetFirewallRule -DisplayName "RDP-Management" `
    -Direction Inbound `
    -LocalPort 3389 `
    -Protocol TCP `
    -RemoteAddress 10.0.0.0/24 `
    -Action Allow

# Remove default RDP rule
Remove-NetFirewallRule -DisplayName "Remote Desktop*" -ErrorAction SilentlyContinue
```

---

### Network Segmentation

```powershell
# Implement IPSec policies for server-to-server communication
# Example: Require IPSec for database server communication

$endpointSet = New-NetIPsecPhase2AuthSet -DisplayName "DatabaseAuth" `
    -Proposal (New-NetIPsecAuthProposal -Machine -Cert -Authority "DC=company,DC=com")

$quickModePolicy = New-NetIPsecQuickModeCryptoSet -DisplayName "DatabaseEncryption" `
    -Proposal (New-NetIPsecQuickModeCryptoProposal -Encapsulation ESP -ESPHash SHA256 -Encryption AES256)

New-NetIPsecRule -DisplayName "Secure-Database-Traffic" `
    -InboundSecurity Require `
    -OutboundSecurity Request `
    -QuickModeCryptoSet $quickModePolicy.Name `
    -Phase2AuthSet $endpointSet.Name `
    -RemoteAddress 10.0.10.100
```

---

### DNS Security

```powershell
# Enable DNS Client over HTTPS (DoH)
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses ("1.1.1.1", "1.0.0.1")

# Enable DNSSEC validation
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -Validate

# Disable LLMNR and NetBIOS (already covered, but critical)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -Value 0
```

---

## Application Hardening

### Browser Security (Edge/Chrome)

```powershell
# Force HTTPS
# Group Policy: Computer Configuration → Administrative Templates → Microsoft Edge
# → Force HTTPS: Enabled

# Disable legacy plugins
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Edge" -Name "PluginsAllowedForUrls" -Value @()

# Enable SmartScreen
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Edge" -Name "SmartScreenEnabled" -Value 1

# Block potentially unwanted applications
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Edge" -Name "SmartScreenPuaEnabled" -Value 1
```

### Office Applications

```powershell
# Block macros in Office files from the internet
# Group Policy: User Configuration → Administrative Templates → Microsoft Office 2016
# → Security Settings → Trust Center
# → Block macros from running in Office files from the Internet: Enabled

# Disable DDE
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\Word\Options" -Name "DontUpdateLinks" -Value 1
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\Excel\Options" -Name "DontUpdateLinks" -Value 1
```

### Third-Party Software

1. **Keep Updated**: Enable automatic updates
2. **Remove Unnecessary**: Uninstall unused applications
3. **Restrict Execution**: Use AppLocker to control application execution

```powershell
# AppLocker example: Allow only signed applications
$rule = New-AppLockerPolicy -RuleType Publisher -User Everyone -RuleNamePrefix "Signed-Apps" `
    -PublisherName "*" -ProductName "*" -BinaryName "*" -BinaryVersion "*"

Set-AppLockerPolicy -PolicyObject $rule -Merge
```

---

## Monitoring & Logging

### Event Log Configuration

```powershell
# Increase event log sizes
wevtutil sl Security /ms:1073741824    # 1 GB
wevtutil sl System /ms:1073741824      # 1 GB
wevtutil sl Application /ms:1073741824 # 1 GB

# Enable retention
wevtutil sl Security /rt:false /ab:true
wevtutil sl System /rt:false /ab:true
wevtutil sl Application /rt:false /ab:true

# Create custom event log for AEGIS
New-EventLog -LogName "AEGIS" -Source "ClearGlassCorp"

# Verify
Get-EventLog -List
```

### SIEM Integration

Forward AEGIS logs to SIEM:

```powershell
# Example: Forward to Splunk via Windows Event Forwarding

# 1. Configure Event Collector
wecutil qc

# 2. Create subscription
$subscriptionXML = @"
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
    <SubscriptionId>AEGIS-to-SIEM</SubscriptionId>
    <SubscriptionType>SourceInitiated</SubscriptionType>
    <Description>Forward AEGIS events to SIEM</Description>
    <Enabled>true</Enabled>
    <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
    <Query><![CDATA[
        <QueryList>
            <Query Id="0">
                <Select Path="Security">*[System[(EventID=4625 or EventID=4624 or EventID=4656)]]</Select>
            </Query>
        </QueryList>
    ]]></Query>
</Subscription>
"@

$subscriptionXML | Out-File "C:\Temp\aegis-subscription.xml"
wecutil cs "C:\Temp\aegis-subscription.xml"
```

### Log Monitoring Script

```powershell
# Create monitoring script: Monitor-AEGISAlerts.ps1
$script = @'
# Monitor AEGIS incidents and alert
$incidentPath = "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\Incidents"
$lastCheck = (Get-Date).AddMinutes(-15)

Get-ChildItem $incidentPath -Filter "*.json" | 
    Where-Object {$_.LastWriteTime -gt $lastCheck} | 
    ForEach-Object {
        $incident = Get-Content $_.FullName | ConvertFrom-Json
        $threat = $incident.Threat
        
        if ($threat.Score -ge 90) {
            # Send email alert
            Send-MailMessage `
                -To "security@company.com" `
                -From "aegis@company.com" `
                -Subject "CRITICAL AEGIS Alert: $($threat.Type)" `
                -Body "Threat Score: $($threat.Score)`nSeverity: $($threat.Severity)`nHost: $env:COMPUTERNAME`nTime: $($threat.Time)" `
                -SmtpServer "mail.company.com"
        }
    }
'@

$script | Out-File "C:\Scripts\Monitor-AEGISAlerts.ps1"

# Schedule to run every 15 minutes
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\Monitor-AEGISAlerts.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "AEGIS-AlertMonitor" -Action $action -Trigger $trigger -User "SYSTEM"
```

---

## Compliance Frameworks

### CIS Benchmarks Alignment

AEGIS hardening aligns with CIS Windows Server/10 Benchmarks:

| CIS Control | AEGIS Implementation |
|-------------|---------------------|
| 1.1 - Account Policies | Password policy enforcement |
| 2.2 - Audit Policies | Comprehensive audit logging |
| 2.3 - User Rights | Privilege management |
| 5.1 - SMB Security | SMBv1 disabled |
| 8.1 - Defender | Real-time protection enabled |
| 9.1 - Firewall | All profiles enabled |
| 17.1 - Credential Protection | LSASS protection, Credential Guard |
| 18.9 - PowerShell | Script block logging enabled |

### NIST Cybersecurity Framework

| NIST Function | AEGIS Capability |
|---------------|------------------|
| **Identify** | Security audit, baseline profiling |
| **Protect** | OS hardening, LSASS protection |
| **Detect** | Real-time scanning, ML anomalies, threat intelligence |
| **Respond** | Auto-remediation, network isolation |
| **Recover** | Forensic collection, configuration backup |

### PCI-DSS Requirements

Relevant controls for payment processing environments:

- **Requirement 1**: Firewall configuration
- **Requirement 2**: System hardening, disable defaults
- **Requirement 5**: Anti-malware (Windows Defender)
- **Requirement 10**: Logging and monitoring
- **Requirement 11**: Vulnerability scanning (via security audits)

---

## Validation & Testing

### Post-Hardening Security Audit

```powershell
# Run AEGIS security audit
.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit

# Expected results after full hardening:
# Target Score: 95%+
# All checks should be green or yellow (no red)
```

### Penetration Testing Validation

Recommended tests (in controlled environment):

1. **Brute Force Detection**
```powershell
# Test failed logon detection
# From external system, attempt 5+ failed RDP logins
# AEGIS should detect within 15 minutes
```

2. **Ransomware Simulation**
```powershell
# Create test files and modify rapidly
$testPath = "C:\Users\$env:USERNAME\Documents\RansomwareTest"
New-Item -ItemType Directory -Path $testPath -Force

1..100 | ForEach-Object {
    $file = "$testPath\test$_.txt"
    "Original content" | Out-File $file
    Start-Sleep -Milliseconds 100
    "Modified content" | Out-File $file
}

# AEGIS should detect mass file modifications
```

3. **Network Beaconing**
```powershell
# Simulate C2 beaconing (safe test)
1..30 | ForEach-Object {
    Test-NetConnection -ComputerName "example.com" -Port 443
    Start-Sleep -Seconds 2
}

# AEGIS should detect excessive connections to same IP
```

### Compliance Scanning

```powershell
# Run CIS-CAT or Microsoft Security Compliance Toolkit
# Download from: https://www.cisecurity.org/cybersecurity-tools/cis-cat-pro/

# Example with MSCT:
.\LocalGPO\LGPO.exe /parse /m C:\MSCT\GPOs\MSCT-Windows-10\ > compliance-report.txt
```

---

## Incident Response

### AEGIS Incident Response Playbook

#### Phase 1: Detection (Automated by AEGIS)

1. Real-time threat scan detects anomaly
2. Threat scored and categorized
3. Alert sent (Slack/Email)
4. Incident JSON created

#### Phase 2: Containment

**For Critical Threats (Score ≥ 90)**:

```powershell
# If auto-remediation enabled, AEGIS automatically:
# 1. Isolates network
# 2. Terminates suspicious processes
# 3. Blocks malicious IPs
# 4. Collects forensics

# Manual containment (if auto-remediate disabled):
Get-NetAdapter | Disable-NetAdapter -Confirm:$false
```

**For High Threats (Score 75-89)**:

```powershell
# Manual review and decision
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard
# Option 2: View Recent Threats
# Investigate and decide on response
```

#### Phase 3: Eradication

```powershell
# Review forensic data
$forensics = Get-ChildItem "C:\ProgramData\ClearGlassCorp\AEGIS\Forensics" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1

Get-Content $forensics.FullName | ConvertFrom-Json

# Identify and remove malware/persistence
# Use incident details to guide removal
```

#### Phase 4: Recovery

```powershell
# Restore from clean backup if needed
# OR rebuild if severely compromised

# Re-enable network
Get-NetAdapter | Enable-NetAdapter

# Remove temporary firewall blocks
Get-NetFirewallRule -DisplayName "AEGIS-Block-*" | Remove-NetFirewallRule

# Verify system clean
.\AEGIS-v6.0-Enhanced.ps1 -Mode Hunt -ScanMinutes 60

# Restore configuration if needed
.\AEGIS-v6.0-Enhanced.ps1 -Mode Restore
```

#### Phase 5: Lessons Learned

1. Review incident JSON and forensics
2. Identify gaps in detection/response
3. Update baselines if needed
4. Adjust thresholds if false positive
5. Document for future reference

---

## Hardening Checklist

### Pre-Production Checklist

- [ ] Run initial security audit - document baseline score
- [ ] Disable SMBv1
- [ ] Disable PowerShell v2
- [ ] Enable LSASS protection
- [ ] Configure Windows Defender (all features)
- [ ] Enable audit policies
- [ ] Configure PowerShell logging
- [ ] Set password policy
- [ ] Disable unnecessary services
- [ ] Configure Windows Firewall
- [ ] Deploy AEGIS with Burlington mode
- [ ] Configure threat intelligence API keys
- [ ] Set up Slack/email alerts
- [ ] Build ML baseline (7 days minimum)
- [ ] Configure scheduled scans
- [ ] Test auto-remediation (controlled environment)
- [ ] Validate logging to SIEM
- [ ] Run post-hardening audit - verify 95%+ score
- [ ] Document configuration
- [ ] Create runbooks for incident response
- [ ] Train SOC team on AEGIS dashboard

### Quarterly Review Checklist

- [ ] Review security audit score
- [ ] Update AEGIS to latest version
- [ ] Review and update baseline
- [ ] Review firewall rules
- [ ] Audit administrator accounts
- [ ] Review threat incidents
- [ ] Test incident response procedures
- [ ] Update API keys if needed
- [ ] Review false positive rate
- [ ] Adjust thresholds if needed
- [ ] Backup AEGIS configuration
- [ ] Review logs for anomalies
- [ ] Update documentation

---

## Advanced Hardening (Optional)

### BitLocker Encryption

```powershell
# Enable BitLocker (requires TPM or USB key)
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 -UsedSpaceOnly -TpmProtector

# Backup recovery key
$key = (Get-BitLockerVolume -MountPoint "C:").KeyProtector | Where-Object {$_.KeyProtectorType -eq 'RecoveryPassword'}
$key.RecoveryPassword | Out-File "C:\BitLocker-Recovery-Key.txt"
```

### Application Whitelisting (AppLocker)

```powershell
# Create default allow rules for Windows and Program Files
$rules = Get-AppLockerFileInformation -Directory "C:\Windows\" -Recurse -FileType Exe,Dll,Script | New-AppLockerPolicy -RuleType Publisher,Path -User Everyone

# Add AEGIS to allowed applications
$aegisRules = Get-AppLockerFileInformation -Path "C:\Program Files\AEGIS\*" -FileType Exe,Script | New-AppLockerPolicy -RuleType Path -User Everyone

# Merge and apply
$combined = $rules.RuleCollections + $aegisRules.RuleCollections
Set-AppLockerPolicy -PolicyObject $combined
```

### Attack Surface Reduction (ASR)

```powershell
# Enable ASR rules
Add-MpPreference -AttackSurfaceReductionRules_Ids BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550 -AttackSurfaceReductionRules_Actions Enabled  # Block executable content from email
Add-MpPreference -AttackSurfaceReductionRules_Ids D4F940AB-401B-4EFC-AADC-AD5F3C50688A -AttackSurfaceReductionRules_Actions Enabled  # Block Office from creating child processes
Add-MpPreference -AttackSurfaceReductionRules_Ids 3B576869-A4EC-4529-8536-B80A7769E899 -AttackSurfaceReductionRules_Actions Enabled  # Block Office from creating executable content
Add-MpPreference -AttackSurfaceReductionRules_Ids 75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84 -AttackSurfaceReductionRules_Actions Enabled  # Block Office from injecting into processes
Add-MpPreference -AttackSurfaceReductionRules_Ids D3E037E1-3EB8-44C8-A917-57927947596D -AttackSurfaceReductionRules_Actions Enabled  # Block JavaScript/VBScript from launching executables
Add-MpPreference -AttackSurfaceReductionRules_Ids 5BEB7EFE-FD9A-4556-801D-275E5FFC04CC -AttackSurfaceReductionRules_Actions Enabled  # Block execution from PSExec and WMI
Add-MpPreference -AttackSurfaceReductionRules_Ids 92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B -AttackSurfaceReductionRules_Actions Enabled  # Block untrusted/unsigned processes from USB
Add-MpPreference -AttackSurfaceReductionRules_Ids 01443614-CD74-433A-B99E-2ECDC07BFC25 -AttackSurfaceReductionRules_Actions Enabled  # Block executable files from running unless criteria met
Add-MpPreference -AttackSurfaceReductionRules_Ids C1DB55AB-C21A-4637-BB3F-A12568109D35 -AttackSurfaceReductionRules_Actions Enabled  # Use advanced protection against ransomware
Add-MpPreference -AttackSurfaceReductionRules_Ids 9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2 -AttackSurfaceReductionRules_Actions Enabled  # Block credential stealing from lsass.exe
```

---

## Document Information

**Document Version**: 1.0  
**Last Updated**: January 23, 2026  
**Classification**: Confidential - Internal Use Only  
**Author**: ClearGlassCorp Security Team

**Revision History**:
- v1.0 (2026-01-23): Initial release for AEGIS v6.0 Enhanced

---

## Support

**Security Hardening Questions**:
- Email: desmond.otieno@clearglasscorp.com
- Subject: "AEGIS-HARDENING"

**Emergency Security Incidents**:
- Follow incident response playbook (Section 10)
- Contact: security-team@clearglasscorp.com
- Phone: [Emergency Hotline]

---

**© 2026 ClearGlassCorp International. All Rights Reserved.**  
**Patent: US-2026-AEGIS-001**
