# AEGIS v6.0 Enhanced - Deployment Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Installation Methods](#installation-methods)
5. [Configuration](#configuration)
6. [Feature Activation](#feature-activation)
7. [Enterprise Deployment](#enterprise-deployment)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## Overview

AEGIS v6.0 Enhanced is a military-grade endpoint protection platform with:

- **Real-time threat detection** across 9 attack vectors
- **ML-based anomaly detection** with behavioral baseline profiling
- **Threat intelligence integration** (AbuseIPDB, VirusTotal)
- **Automated response** with multi-factor authentication
- **Enterprise-wide deployment** with Active Directory integration
- **Forensic data collection** for incident response

**Patent**: US-2026-AEGIS-001  
**Version**: 6.0 ENHANCED  
**Build**: 20260123-SECURITY-PATCH

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows Server 2016+ or Windows 10/11 Pro |
| **PowerShell** | Version 5.1 or higher |
| **RAM** | 4 GB minimum, 8 GB recommended |
| **Disk Space** | 500 MB for application and logs |
| **Privileges** | Administrator rights required |
| **Network** | Internet access for threat intelligence (optional) |

### Optional Requirements

| Feature | Requirement |
|---------|-------------|
| **Enterprise Deployment** | Active Directory PowerShell module |
| **Threat Intelligence** | API keys (AbuseIPDB, VirusTotal) |
| **Cloud Alerts** | Slack webhook URL |
| **ML Detection** | 7-day baseline collection period |

### Supported Platforms

- ✅ Windows Server 2016, 2019, 2022
- ✅ Windows 10 Pro/Enterprise (Build 1809+)
- ✅ Windows 11 Pro/Enterprise
- ❌ Windows Home editions (limited functionality)

---

## Pre-Deployment Checklist

### 1. Administrative Access
```powershell
# Verify administrator privileges
[Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent() | 
    Select-Object IsInRole(@([Security.Principal.WindowsBuiltInRole]::Administrator))
```

### 2. PowerShell Version
```powershell
# Check PowerShell version
$PSVersionTable.PSVersion
# Should be 5.1 or higher
```

### 3. Execution Policy
```powershell
# Check current policy
Get-ExecutionPolicy

# Set to RemoteSigned (if needed)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

### 4. Network Connectivity
```powershell
# Test internet connectivity
Test-NetConnection -ComputerName api.abuseipdb.com -Port 443
Test-NetConnection -ComputerName virustotal.com -Port 443
```

### 5. Disk Space
```powershell
# Check available disk space
Get-PSDrive C | Select-Object Used, Free
```

### 6. Windows Defender Status
```powershell
# Verify Defender is functional
Get-MpComputerStatus
```

---

## Installation Methods

### Method 1: Single Host Deployment (Quick Start)

#### Step 1: Download Script
```powershell
# Create AEGIS directory
$aegisPath = "C:\Program Files\AEGIS"
New-Item -ItemType Directory -Path $aegisPath -Force

# Download script (adjust source path)
Copy-Item "\\fileserver\AEGIS\AEGIS-v6.0-Enhanced.ps1" -Destination $aegisPath
```

#### Step 2: Run Initial Deployment
```powershell
cd "C:\Program Files\AEGIS"

# Standard deployment
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy

# High-security deployment (Burlington mode)
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy -Burlington

# With auto-remediation
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy -Burlington -AutoRemediate
```

#### Step 3: Configure Features
```powershell
# Enable threat intelligence
$env:AEGIS_ABUSEIPDB_KEY = "your-abuseipdb-api-key"
$env:AEGIS_VIRUSTOTAL_KEY = "your-virustotal-api-key"

# Add to system environment variables (persistent)
[System.Environment]::SetEnvironmentVariable('AEGIS_ABUSEIPDB_KEY', 'your-key', 'Machine')
[System.Environment]::SetEnvironmentVariable('AEGIS_VIRUSTOTAL_KEY', 'your-key', 'Machine')

# Configure Slack alerts
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

#### Step 4: Build ML Baseline
```powershell
# Start 7-day baseline collection
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline

# OR manually collect samples in Dashboard mode:
# Navigate to: Menu → Option 8 → ML Baseline Manager → Collect New Sample
```

---

### Method 2: Scheduled Task Deployment

```powershell
# Create scheduled task for automated scanning
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"C:\Program Files\AEGIS\AEGIS-v6.0-Enhanced.ps1`" -Mode Hunt -ThreatIntelligence -MLDetection"

$trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "AEGIS-DailyScan" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "AEGIS v6.0 automated threat scan"
```

---

### Method 3: Group Policy Deployment

#### Step 1: Create GPO
1. Open **Group Policy Management Console** (GPMC)
2. Create new GPO: `AEGIS-v6-Deployment`
3. Navigate to: **Computer Configuration → Policies → Windows Settings → Scripts → Startup**

#### Step 2: Configure Startup Script
```powershell
# Create deployment script: Deploy-AEGIS.ps1
$aegisPath = "C:\Program Files\AEGIS"
$scriptPath = "\\domain\SYSVOL\scripts\AEGIS-v6.0-Enhanced.ps1"

if (-not (Test-Path $aegisPath)) {
    New-Item -ItemType Directory -Path $aegisPath -Force
}

Copy-Item $scriptPath -Destination $aegisPath -Force

# Run deployment
& "$aegisPath\AEGIS-v6.0-Enhanced.ps1" -Mode Deploy -Burlington

# Create scheduled task
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-File `"$aegisPath\AEGIS-v6.0-Enhanced.ps1`" -Mode Dashboard"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask -TaskName "AEGIS-v6" -Action $action -Trigger $trigger -Principal $principal -Force
```

#### Step 3: Link GPO
- Link GPO to appropriate OUs containing target computers
- Force update: `gpupdate /force`

---

## Configuration

### Configuration Files Location

```
C:\ProgramData\ClearGlassCorp\AEGIS\
├── Config\
│   └── webhook.enc          # Encrypted Slack webhook
├── Logs\
│   └── AEGIS_YYYYMMDD.log  # Daily logs
├── Incidents\
│   └── CGC-*.json          # Threat incidents
├── Forensics\
│   └── forensics_*.json    # Forensic captures
├── Baseline\
│   └── baseline.json       # ML baseline data
└── Backups\
    └── config_backup_*.json # Configuration backups
```

### Environment Variables

Set these for advanced features:

```powershell
# Threat Intelligence API Keys
$env:AEGIS_ABUSEIPDB_KEY = "your-abuseipdb-key"
$env:AEGIS_VIRUSTOTAL_KEY = "your-virustotal-key"

# Make persistent
[Environment]::SetEnvironmentVariable('AEGIS_ABUSEIPDB_KEY', 'your-key', 'Machine')
[Environment]::SetEnvironmentVariable('AEGIS_VIRUSTOTAL_KEY', 'your-key', 'Machine')
```

### API Key Acquisition

#### AbuseIPDB
1. Visit: https://www.abuseipdb.com/
2. Create free account
3. Navigate to: **Account → API**
4. Generate API key
5. Free tier: 1,000 checks/day

#### VirusTotal
1. Visit: https://www.virustotal.com/
2. Create free account
3. Navigate to: **Profile → API Key**
4. Copy API key
5. Free tier: 4 requests/minute

### Slack Webhook Setup

1. Go to: https://api.slack.com/apps
2. Create new app → "From scratch"
3. Select workspace
4. **Add features**: Incoming Webhooks
5. Activate incoming webhooks
6. **Add New Webhook to Workspace**
7. Select channel
8. Copy webhook URL

```powershell
# Configure in AEGIS
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -SlackWebhook "https://hooks.slack.com/services/T00/B00/XX"

# OR through Settings menu:
# Dashboard → Option 9 → Option 4
```

---

## Feature Activation

### Burlington Mode (Maximum Hardening)

Enables strictest security settings:
- Failed logon threshold: 2 (vs 5)
- File modification threshold: 50 (vs 100)
- LSASS protection enabled
- Credential Guard activation

```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy -Burlington
```

### Auto-Remediation

Automatically responds to critical threats (Score ≥ 90):
- **Credential Dumping**: Network isolation
- **Ransomware**: Process termination + network isolation
- **Network Beaconing**: IP blocking
- **Brute Force**: Source IP blocking

⚠️ **WARNING**: Auto-remediation can disconnect systems. Use with caution.

```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -AutoRemediate

# Enable through Dashboard:
# Settings → Toggle Auto-Remediate
```

### Threat Intelligence

Real-time IP and file hash lookups against threat databases:

```powershell
# Enable with API keys set
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ThreatIntelligence

# Or through Dashboard:
# Settings → Toggle Threat Intelligence
```

**Benefits**:
- Identifies known malicious IPs
- Validates file hashes against malware databases
- Adds 10-15 points to threat scores for confirmed threats

### ML-Based Anomaly Detection

Detects deviations from normal system behavior:

**Requirements**:
1. 7-day baseline collection (minimum 10 samples)
2. Baseline mode running or manual sample collection

```powershell
# Option 1: Automated 7-day collection
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline

# Option 2: Manual samples via Dashboard
# Menu → ML Baseline Manager → Collect New Sample
# Collect at least 10 samples over several days

# Enable ML detection
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -MLDetection
```

**Detects**:
- Unusual process counts
- Abnormal network activity
- CPU/Memory spikes
- Unknown processes not in baseline

---

## Enterprise Deployment

### Prerequisites

```powershell
# Install Active Directory PowerShell module
Install-WindowsFeature RSAT-AD-PowerShell

# Or on Windows 10/11:
Add-WindowsCapability -Online -Name Rsat.ActiveDirectory.DS-LDS.Tools
```

### Deployment Steps

#### Step 1: Prepare Deployment Package

```powershell
# Create network share
$sharePath = "\\fileserver\AEGIS-Deploy"
New-Item -ItemType Directory -Path $sharePath -Force
New-SmbShare -Name "AEGIS-Deploy" -Path $sharePath -FullAccess "Domain Admins"

# Copy script
Copy-Item "AEGIS-v6.0-Enhanced.ps1" -Destination $sharePath
```

#### Step 2: Test Deployment on Pilot Group

```powershell
# Deploy to small OU first
.\AEGIS-v6.0-Enhanced.ps1 -Mode Enterprise -OU "OU=Pilot,OU=Servers,DC=company,DC=com"
```

#### Step 3: Monitor Pilot Group

Monitor for 48-72 hours:
- Check for false positives
- Verify performance impact
- Review threat detections
- Validate scheduled tasks

#### Step 4: Full Deployment

```powershell
# Production deployment
.\AEGIS-v6.0-Enhanced.ps1 -Mode Enterprise -OU "OU=Servers,DC=company,DC=com" -Burlington

# With additional features
.\AEGIS-v6.0-Enhanced.ps1 -Mode Enterprise `
    -OU "OU=Servers,DC=company,DC=com" `
    -Burlington `
    -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK"
```

### Deployment Features

- **Automatic retry logic**: 3 attempts per host
- **Connectivity checks**: Skips offline systems
- **Progress tracking**: Real-time deployment status
- **Summary report**: Success/failure statistics
- **Scheduled task creation**: Auto-starts AEGIS on boot

### Deployment Monitoring

```powershell
# Check deployed systems
$computers = Get-ADComputer -Filter * -SearchBase "OU=Servers,DC=company,DC=com"

foreach ($comp in $computers) {
    $status = Invoke-Command -ComputerName $comp.Name -ScriptBlock {
        Get-ScheduledTask -TaskName "AEGIS-v6" -ErrorAction SilentlyContinue
    } -ErrorAction SilentlyContinue
    
    if ($status) {
        Write-Host "$($comp.Name): Deployed" -ForegroundColor Green
    } else {
        Write-Host "$($comp.Name): Not Deployed" -ForegroundColor Red
    }
}
```

---

## Post-Deployment Verification

### 1. Service Verification

```powershell
# Check AEGIS scheduled task
Get-ScheduledTask -TaskName "AEGIS-v6" | Select-Object State, LastRunTime, NextRunTime

# Check if running
Get-Process | Where-Object {$_.Path -like "*AEGIS*"}
```

### 2. Log Verification

```powershell
# Check recent logs
Get-Content "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\AEGIS_$(Get-Date -Format 'yyyyMMdd').log" -Tail 20
```

### 3. Security Audit

```powershell
# Run security audit
.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit

# Target: 85%+ security score
```

### 4. Test Threat Detection

```powershell
# Safe test: Generate failed logon attempts (from different source)
# Monitor AEGIS for detection

# Run threat scan
.\AEGIS-v6.0-Enhanced.ps1 -Mode Hunt -ThreatIntelligence
```

### 5. Dashboard Verification

```powershell
# Launch dashboard
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard

# Verify:
# - System status shows correct host
# - Features enabled as configured
# - No errors in logs
# - Baseline status (if ML enabled)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Administrator Privileges Required"

**Symptom**: Script exits with privilege error

**Solution**:
```powershell
# Right-click PowerShell → Run as Administrator
# OR
Start-Process powershell -Verb RunAs
```

#### Issue 2: "Cannot load baseline"

**Symptom**: ML detection not working

**Solution**:
```powershell
# Check baseline exists
Test-Path "C:\ProgramData\ClearGlassCorp\AEGIS\Baseline\baseline.json"

# Rebuild baseline
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline

# OR collect manual samples
# Dashboard → ML Baseline Manager → Collect New Sample (repeat 10+ times)
```

#### Issue 3: "Threat intelligence lookup failed"

**Symptom**: API errors in logs

**Solution**:
```powershell
# Verify API keys set
$env:AEGIS_ABUSEIPDB_KEY
$env:AEGIS_VIRUSTOTAL_KEY

# Test connectivity
Test-NetConnection -ComputerName api.abuseipdb.com -Port 443

# Check rate limits (AbuseIPDB: 1000/day free tier)
```

#### Issue 4: "Failed to send alert"

**Symptom**: Slack alerts not working

**Solution**:
```powershell
# Verify webhook stored
Test-Path "C:\ProgramData\ClearGlassCorp\AEGIS\Config\webhook.enc"

# Re-configure webhook
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -SlackWebhook "https://hooks.slack.com/..."

# Test manually
$webhook = "https://hooks.slack.com/..."
$payload = @{text = "Test message"} | ConvertTo-Json
Invoke-RestMethod -Uri $webhook -Method Post -Body $payload -ContentType 'application/json'
```

#### Issue 5: High false positive rate

**Symptom**: Too many threat alerts for normal activity

**Solution**:
```powershell
# Adjust thresholds in script or use Burlington mode toggle

# Increase scan window
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ScanMinutes 30

# Build better baseline (more samples over longer period)
# Dashboard → ML Baseline Manager → Collect samples regularly
```

#### Issue 6: Performance impact

**Symptom**: High CPU/Memory usage

**Solution**:
```powershell
# Increase scan window (less frequent checks)
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ScanMinutes 30

# Disable features temporarily
# Dashboard → Settings → Toggle features off

# Check parallel job cleanup
Get-Job | Remove-Job -Force

# Reduce file scan scope by editing script
```

### Log Analysis

```powershell
# Search for errors
Select-String -Path "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\*.log" -Pattern "ERROR"

# Count threats by type
Get-ChildItem "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\Incidents" -Filter "*.json" | ForEach-Object {
    (Get-Content $_.FullName | ConvertFrom-Json).Threat.Type
} | Group-Object | Sort-Object Count -Descending

# View recent incidents
Get-ChildItem "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\Incidents" -Filter "*.json" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 10 | 
    ForEach-Object {
        Get-Content $_.FullName | ConvertFrom-Json | Select-Object -ExpandProperty Threat
    } | Format-Table Type, Score, Severity, Time
```

---

## Maintenance

### Daily Tasks

1. **Review Threat Dashboard**
   ```powershell
   .\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard
   # Check Option 2: View Recent Threats
   ```

2. **Check Logs for Errors**
   ```powershell
   Get-Content "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\AEGIS_$(Get-Date -Format 'yyyyMMdd').log" |
       Select-String "ERROR|CRITICAL"
   ```

### Weekly Tasks

1. **Security Audit**
   ```powershell
   .\AEGIS-v6.0-Enhanced.ps1 -Mode Audit
   ```

2. **Update Baseline** (if using ML detection)
   ```powershell
   # Dashboard → ML Baseline Manager → Collect New Sample
   ```

3. **Review Incidents**
   ```powershell
   # Dashboard → View Recent Threats
   # Investigate high-score threats (>90)
   ```

### Monthly Tasks

1. **Configuration Backup**
   ```powershell
   # Dashboard → Settings → Backup Configuration
   # OR automatic backups stored in:
   # C:\ProgramData\ClearGlassCorp\AEGIS\Backups\
   ```

2. **Log Rotation Review**
   ```powershell
   # Automatic rotation:
   # - Compresses logs older than 7 days
   # - Deletes logs older than 30 days
   
   # Manual check
   Get-ChildItem "C:\ProgramData\ClearGlassCorp\AEGIS\Logs" | Measure-Object -Property Length -Sum
   ```

3. **Update API Keys** (if expired)
   ```powershell
   [Environment]::SetEnvironmentVariable('AEGIS_ABUSEIPDB_KEY', 'new-key', 'Machine')
   ```

### Quarterly Tasks

1. **Script Updates**
   - Check for new AEGIS versions
   - Review changelog
   - Test in pilot environment
   - Deploy enterprise-wide

2. **Threat Intelligence Review**
   - Analyze detection accuracy
   - Review false positives
   - Adjust thresholds if needed

3. **Baseline Refresh** (ML detection)
   ```powershell
   # Reset and rebuild baseline if system role changed significantly
   # Dashboard → ML Baseline Manager → Reset Baseline
   .\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline
   ```

### Emergency Procedures

#### System Compromised

```powershell
# 1. Immediate isolation (if auto-remediate not enabled)
Get-NetAdapter | Disable-NetAdapter -Confirm:$false

# 2. Collect forensics
.\AEGIS-v6.0-Enhanced.ps1 -Mode Hunt
# Forensic data saved to: C:\ProgramData\ClearGlassCorp\AEGIS\Forensics\

# 3. Review incidents
Get-ChildItem "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\Incidents" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5

# 4. Contact security team with:
# - Incident JSON files
# - Forensic captures
# - System logs
```

#### False Positive Remediation

```powershell
# If auto-remediation blocked legitimate activity:

# 1. Re-enable network
Get-NetAdapter | Enable-NetAdapter

# 2. Remove firewall block rules
Get-NetFirewallRule -DisplayName "AEGIS-Block-*" | Remove-NetFirewallRule

# 3. Adjust thresholds
# Dashboard → Settings → Configure Scan Window (increase to 30+ minutes)

# 4. Disable auto-remediation
# Dashboard → Settings → Toggle Auto-Remediate
```

---

## Performance Optimization

### Recommended Settings

| Environment | Scan Window | Features | Auto-Remediate |
|-------------|-------------|----------|----------------|
| **Development** | 30 min | TI only | Off |
| **Production Servers** | 15 min | TI + ML | On (Burlington) |
| **Workstations** | 30 min | TI | Off |
| **High-Security** | 10 min | TI + ML | On (Burlington) |

### Resource Usage

Expected resource consumption:

| Component | CPU | RAM | Disk I/O |
|-----------|-----|-----|----------|
| **Idle** | <1% | ~50 MB | Minimal |
| **Scan** | 5-15% | ~200 MB | Medium |
| **Dashboard** | <2% | ~100 MB | Low |
| **Baseline Collection** | 2-5% | ~150 MB | Low |

---

## Support & Contact

**Technical Support:**
- Email: desmond.otieno@clearglasscorp.com
- Documentation: This guide
- Logs: `C:\ProgramData\ClearGlassCorp\AEGIS\Logs\`

**Reporting Issues:**
1. Collect logs from last 48 hours
2. Export recent incidents (Dashboard → View Recent Threats)
3. Note system configuration (OS version, features enabled)
4. Describe issue and reproduction steps
5. Email to support with "AEGIS-ISSUE" in subject

**Feature Requests:**
Contact via email with "AEGIS-FEATURE" in subject line

---

## Appendix A: Command Reference

### Quick Command Reference

```powershell
# Standard deployment
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy

# High-security deployment
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy -Burlington -AutoRemediate

# Launch dashboard with all features
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ThreatIntelligence -MLDetection

# Run threat scan
.\AEGIS-v6.0-Enhanced.ps1 -Mode Hunt -ScanMinutes 15

# Security audit
.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit

# Build baseline
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline

# Enterprise deployment
.\AEGIS-v6.0-Enhanced.ps1 -Mode Enterprise -OU "OU=Servers,DC=corp,DC=com"

# Restore configuration
.\AEGIS-v6.0-Enhanced.ps1 -Mode Restore
```

---

## Appendix B: Security Hardening Checklist

See separate **AEGIS-Security-Hardening.md** document for complete hardening guide.

---

## Document Information

**Document Version**: 1.0  
**Last Updated**: January 23, 2026  
**Author**: ClearGlassCorp Security Team  
**Classification**: Internal Use

**Changelog**:
- v1.0 (2026-01-23): Initial release for AEGIS v6.0
