# AEGIS v6.0 Enhanced - Quick Start Guide

## 🚀 Get Started in 15 Minutes

This guide gets AEGIS v6.0 running on your system in under 15 minutes.

---

## Prerequisites Check (2 minutes)

```powershell
# 1. Verify you're running as Administrator
[Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()

# 2. Check PowerShell version (must be 5.1+)
$PSVersionTable.PSVersion

# 3. Check disk space (need 500MB+)
Get-PSDrive C | Select-Object Free
```

✅ All checks passed? Continue below!

---

## Installation (3 minutes)

### Step 1: Download AEGIS

```powershell
# Create AEGIS directory
New-Item -ItemType Directory -Path "C:\Program Files\AEGIS" -Force

# Copy the script to this location
# Place: AEGIS-v6.0-Enhanced.ps1 in C:\Program Files\AEGIS\
```

### Step 2: Deploy with Defaults

```powershell
cd "C:\Program Files\AEGIS"

# Standard deployment
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy
```

**This automatically configures**:
- ✅ Windows Defender (all protections)
- ✅ Firewall (all profiles)
- ✅ SMBv1 disabled
- ✅ PowerShell v2 disabled
- ✅ Audit policies enabled
- ✅ PowerShell logging enabled
- ✅ Guest account disabled

---

## Launch Dashboard (1 minute)

```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard
```

**Dashboard Menu**:
1. Run Threat Scan
2. View Recent Threats
3. Security Audit
4. System Health
5. View Logs
6. Network Analysis
7. Process Monitor
8. ML Baseline Manager
9. Settings
0. Exit

---

## First Scan (2 minutes)

From the dashboard:

1. Press `1` (Run Full Threat Scan)
2. Wait for scan to complete (~30-60 seconds)
3. Review any detected threats
4. Press Enter to return to menu

**Expected Output**:
```
✓ No threats detected - System secure
```

---

## Enable Advanced Features (Optional, 5 minutes)

### Option A: Threat Intelligence

Get free API keys:

1. **AbuseIPDB** → https://www.abuseipdb.com/
   - Create account → API → Copy key
   - Free: 1,000 checks/day

2. **VirusTotal** → https://www.virustotal.com/
   - Create account → Profile → API Key
   - Free: 4 requests/minute

```powershell
# Set API keys (in PowerShell as Admin)
[Environment]::SetEnvironmentVariable('AEGIS_ABUSEIPDB_KEY', 'YOUR_KEY_HERE', 'Machine')
[Environment]::SetEnvironmentVariable('AEGIS_VIRUSTOTAL_KEY', 'YOUR_KEY_HERE', 'Machine')

# Restart PowerShell, then launch with threat intel
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ThreatIntelligence
```

### Option B: Slack Alerts

1. Create Slack webhook → https://api.slack.com/apps
2. New App → Incoming Webhooks → Add to Workspace
3. Copy webhook URL

```powershell
# Configure Slack
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Or via Dashboard: Menu → 9 (Settings) → 4 (Configure Slack)
```

### Option C: ML Detection

```powershell
# Build baseline (requires 10+ samples over several days)
# Option 1: Automated collection for 7 days
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline

# Option 2: Manual samples via Dashboard
# Menu → 8 (ML Baseline Manager) → 1 (Collect New Sample)
# Repeat 10+ times over several days

# Enable ML detection once baseline established
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -MLDetection
```

---

## Maximum Security Mode (2 minutes)

For high-security environments:

```powershell
# Deploy Burlington mode (strictest settings)
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy -Burlington

# Launch with all features
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard `
    -Burlington `
    -ThreatIntelligence `
    -MLDetection `
    -SlackWebhook "https://hooks.slack.com/..."
```

**Burlington Mode Changes**:
- Failed logon threshold: 2 (vs 5)
- File modification threshold: 50 (vs 100)
- LSASS protection enabled
- Stricter threat scoring

---

## Schedule Automated Scans (2 minutes)

```powershell
# Daily scan at 2 AM
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"C:\Program Files\AEGIS\AEGIS-v6.0-Enhanced.ps1`" -Mode Hunt -ThreatIntelligence"

$trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask -TaskName "AEGIS-DailyScan" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Description "AEGIS automated threat scan"
```

---

## Verification (2 minutes)

### Check Security Score

```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit
```

**Target**: 85%+ security score

### View Logs

```powershell
# Check today's log
Get-Content "C:\ProgramData\ClearGlassCorp\AEGIS\Logs\AEGIS_$(Get-Date -Format 'yyyyMMdd').log" -Tail 20
```

### Test Detection

```powershell
# Verify threat detection is working
# Dashboard → Menu → 1 (Run Threat Scan)
# Should complete without errors
```

---

## Quick Reference

### Common Commands

```powershell
# Run threat scan
.\AEGIS-v6.0-Enhanced.ps1 -Mode Hunt

# Security audit
.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit

# Dashboard
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard

# With all features
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ThreatIntelligence -MLDetection

# Build baseline
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline
```

### Key File Locations

```
C:\ProgramData\ClearGlassCorp\AEGIS\
├── Logs\                    # Daily logs
├── Incidents\               # Threat detections (JSON)
├── Forensics\               # Forensic captures
├── Baseline\                # ML baseline data
└── Backups\                 # Configuration backups
```

### Dashboard Quick Actions

| Key | Action |
|-----|--------|
| `1` | Run full threat scan |
| `2` | View recent threats (last 15) |
| `3` | Security audit (get score) |
| `4` | System health check |
| `5` | View logs (last 30 lines) |
| `8` | ML baseline manager |
| `9` | Settings & configuration |
| `0` | Exit dashboard |

---

## Troubleshooting

### "Administrator Privileges Required"
```powershell
# Right-click PowerShell → Run as Administrator
```

### "Cannot load baseline" (ML Detection)
```powershell
# Build baseline first
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline
# OR collect 10+ manual samples via Dashboard
```

### "Threat intelligence lookup failed"
```powershell
# Verify API keys set
$env:AEGIS_ABUSEIPDB_KEY
$env:AEGIS_VIRUSTOTAL_KEY

# If blank, set them:
[Environment]::SetEnvironmentVariable('AEGIS_ABUSEIPDB_KEY', 'your-key', 'Machine')
```

### High CPU usage during scan
```powershell
# Increase scan window to reduce frequency
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ScanMinutes 30
```

---

## Next Steps

### ✅ You're Now Protected!

**Immediately Available**:
- ✅ Real-time threat detection (9 attack vectors)
- ✅ Security hardening applied
- ✅ Automated logging
- ✅ Interactive dashboard

**Add within 24 hours**:
1. Threat intelligence (get free API keys)
2. Slack alerts (5-minute setup)
3. Scheduled daily scans

**Add within 7 days**:
1. ML-based anomaly detection (needs baseline)
2. Auto-remediation (test first!)

### 📚 Read Full Documentation

- **Deployment Guide**: AEGIS-Deployment-Guide.md
- **Security Hardening**: AEGIS-Security-Hardening.md
- **Configuration Template**: AEGIS-Config-Template.json

### 🔒 Recommended Security Timeline

**Week 1**: Standard deployment + threat intel
```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Deploy
# Set API keys
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ThreatIntelligence
```

**Week 2**: Start baseline collection
```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Baseline
```

**Week 3**: Enable ML detection
```powershell
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -ThreatIntelligence -MLDetection
```

**Week 4**: Test auto-remediation in non-production
```powershell
# Test environment only!
.\AEGIS-v6.0-Enhanced.ps1 -Mode Dashboard -AutoRemediate
```

---

## Support

**Questions?**
- Email: desmond.otieno@clearglasscorp.com
- Documentation: See full deployment guide
- Logs: `C:\ProgramData\ClearGlassCorp\AEGIS\Logs\`

**Reporting Issues:**
1. Run: `.\AEGIS-v6.0-Enhanced.ps1 -Mode Audit`
2. Collect logs from last 24 hours
3. Email to: desmond.otieno@clearglasscorp.com
4. Subject: "AEGIS-ISSUE: [brief description]"

---

## Security Best Practices

### Daily
- Review dashboard for threats (1 minute)
- Check Slack alerts (if configured)

### Weekly
- Run security audit (`Mode Audit`)
- Collect ML baseline sample (if using ML detection)

### Monthly
- Review false positives
- Update API keys if expired
- Check disk space for logs

---

## Success Criteria

After deployment, you should have:

✅ Security score: 85%+ (run `Mode Audit`)  
✅ No deployment errors in logs  
✅ Scheduled scan working  
✅ Dashboard launches successfully  
✅ First threat scan completes  
✅ Zero critical security findings  

---

## Common First-Run Questions

**Q: Do I need API keys immediately?**  
A: No, AEGIS works without them. Add within first week for enhanced detection.

**Q: Can I run this on Windows Home?**  
A: Yes, but some features are limited (no Credential Guard, Group Policy).

**Q: Will this impact performance?**  
A: Minimal. CPU: <1% idle, ~5-15% during scans. RAM: ~50-200MB.

**Q: Can I run alongside other antivirus?**  
A: Yes, AEGIS complements Windows Defender. Not recommended to run with other endpoint protection.

**Q: How do I uninstall?**  
A: Delete scheduled tasks, remove firewall rules, delete `C:\Program Files\AEGIS\` folder.

**Q: Is this safe for production?**  
A: Yes. Start without auto-remediation, test for 1-2 weeks, then enable if desired.

---

## What Gets Installed

AEGIS makes these changes to your system:

**File System**:
- `C:\Program Files\AEGIS\` (script location)
- `C:\ProgramData\ClearGlassCorp\AEGIS\` (logs, config, data)

**Registry** (during Deploy mode):
- PowerShell logging enabled
- LSASS protection (Burlington mode)
- Audit policies configured

**Scheduled Tasks** (if you create them):
- AEGIS-DailyScan (optional)
- AEGIS-BaselineCollection (optional)

**Windows Features** (during Deploy mode):
- SMBv1: Disabled
- PowerShell v2: Disabled
- Windows Defender: Enhanced protection

**No network changes** unless threat detected and auto-remediate enabled.

---

**🎉 Congratulations! AEGIS v6.0 is now protecting your system.**

**Version**: 6.0 Enhanced  
**Build**: 20260123-SECURITY-PATCH  
**Patent**: US-2026-AEGIS-001

---

**© 2026 ClearGlassCorp International. All Rights Reserved.**
