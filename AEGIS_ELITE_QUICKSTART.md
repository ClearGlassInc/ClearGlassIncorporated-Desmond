# AEGIS AI Elite - Quick Start Guide

## 🚀 INSTANT START

### Minimum Requirements
- Windows 10/11 or Windows Server 2016+
- PowerShell 5.1 or higher
- Administrator privileges
- Windows Event Logging enabled

### First Launch
```powershell
# Right-click PowerShell → Run as Administrator
.\AEGIS_AI_ELITE.ps1
```

Voice greeting will play (if enabled), then dashboard appears.

---

## 📋 QUICK REFERENCE

### Command Line Options
```powershell
# Interactive dashboard (default)
.\AEGIS_AI_ELITE.ps1

# Threat hunting mode
.\AEGIS_AI_ELITE.ps1 -Mode Hunt

# Deep scan with auto-response
.\AEGIS_AI_ELITE.ps1 -Mode Hunt -AutoResponse

# Continuous monitoring (300 sec intervals)
.\AEGIS_AI_ELITE.ps1 -ContinuousMonitor -ScanInterval 300

# Compliance audit
.\AEGIS_AI_ELITE.ps1 -Mode Compliance

# Vendor inventory
.\AEGIS_AI_ELITE.ps1 -Mode Vendor

# Disable voice
.\AEGIS_AI_ELITE.ps1 -VoiceEnabled:$false

# With Slack alerts
.\AEGIS_AI_ELITE.ps1 -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK"

# With Teams alerts
.\AEGIS_AI_ELITE.ps1 -TeamsWebhook "https://outlook.office.com/webhook/YOUR/WEBHOOK"
```

---

## 🎯 DASHBOARD MENU

```
1.  Standard Threat Scan       → Quick security check
2.  Deep Threat Hunt           → Comprehensive scan (slower)
3.  Active Threats             → View detected threats
4.  Blocked Items              → IPs/files blocked by AEGIS

5.  Continuous Monitor         → 24/7 scanning mode
6.  Toggle Auto-Response       → Enable/disable automation
7.  Toggle Voice               → Voice on/off

10. Vendor Scan                → Inventory all software vendors
11. Vendor Risk                → Analyze specific vendor
12. High-Risk Vendors          → View risky software

13. Network Topology           → Discover network devices
14. Device Details             → (Future capability)

15. Compliance Audit           → 10-point security assessment
16. View Findings              → Compliance failures

17. System Info                → System status
18. Export Report              → Generate JSON report
19. View Logs                  → Recent log entries
20. Settings                   → (Future capability)

0.  Exit AEGIS                 → Shutdown
```

---

## 🔥 COMMON TASKS

### Daily Security Check
```
1. Launch dashboard
2. Press "1" → Standard Threat Scan
3. Review any detected threats
4. Press "15" → Compliance Audit
5. Address any compliance failures
```

### Investigating Suspicious Activity
```
1. Press "2" → Deep Threat Hunt
2. Review results with MITRE ATT&CK mappings
3. Press "3" → View active threats
4. Press "18" → Export report for documentation
```

### Vendor Security Review
```
1. Press "10" → Vendor Scan (takes 15-30 sec)
2. Press "12" → View high-risk vendors
3. Press "11" → Analyze specific vendor
4. Review risk factors and recommendations
```

### Network Security Audit
```
1. Press "13" → Network Topology Discovery
2. Review discovered devices
3. Identify unknown or suspicious devices
4. Cross-reference with asset inventory
```

### Automated Protection
```powershell
# Enable auto-response from command line
.\AEGIS_AI_ELITE.ps1 -AutoResponse

# Or toggle in dashboard:
# Press "6" → Auto-response ON/OFF
```

⚠️ **Warning:** Auto-response will automatically:
- Block IPs after brute force detection
- Isolate system during ransomware detection
- Terminate malicious processes

Test in non-production first!

### Continuous Monitoring
```
Option 1: From Dashboard
1. Press "5" → Continuous Monitor
2. Scans run every 5 minutes (default)
3. Press Ctrl+C to stop

Option 2: From Command Line
.\AEGIS_AI_ELITE.ps1 -ContinuousMonitor -ScanInterval 300
```

---

## 📊 UNDERSTANDING RESULTS

### Threat Severity Scores
- **90-100**: CRITICAL - Immediate action required
- **75-89**: HIGH - Investigate urgently
- **60-74**: MEDIUM - Review when possible
- **<60**: LOW - Informational

### Threat Types
| Type | Description | MITRE | Severity Range |
|------|-------------|-------|----------------|
| BruteForce | Failed login attempts | T1110 | 60-100 |
| Ransomware | Mass file encryption | T1486 | 85-100 |
| C2Communication | Beaconing to C2 server | T1071 | 75-95 |
| SuspiciousProcess | Unusual process execution | T1055 | 85-100 |
| MaliciousProcess | Known malware | Multiple | 100 |
| Persistence | Startup/scheduled tasks | T1053/T1547 | 75-85 |

### Vendor Risk Levels
| Risk Score | Level | Action Required |
|------------|-------|-----------------|
| 85-100 | Critical | Remove or restrict immediately |
| 70-84 | High | Security review required |
| 50-69 | Medium | Enhanced monitoring |
| 0-49 | Low | Standard monitoring |

### Compliance Scoring
| Score | Level | Meaning |
|-------|-------|---------|
| 90-100% | Excellent | Strong security posture |
| 80-89% | Good | Meets compliance threshold |
| 70-79% | Fair | Improvements needed |
| <70% | Poor | Immediate remediation required |

---

## 🔧 CUSTOMIZATION

### Adjusting Thresholds
Edit the script, find `$global:AEGIS.Thresholds`:

```powershell
$global:AEGIS.Thresholds = @{
    FailedLogons = 5              # Brute force: Lower = more sensitive
    FileModifications = 100       # Ransomware: Adjust for environment
    BeaconingThreshold = 15       # C2: Depends on normal traffic
    ThreatScoreCritical = 90      # Auto-response trigger
    VendorRiskHigh = 70           # High-risk vendor threshold
    ComplianceThreshold = 80      # Passing compliance score
}
```

### Adding Vendors to Database
Find `$global:AEGIS.Intelligence.VendorRisk`:

```powershell
'Your Company Name' = @{
    Risk = 20          # 0-100, lower is better
    Trust = 90         # 0-100, higher is better
    Category = 'Software'
    Approved = $true
}
```

### Cloud Webhook Configuration

**Slack:**
1. Go to https://api.slack.com/apps
2. Create incoming webhook
3. Copy webhook URL
4. Launch: `.\AEGIS_AI_ELITE.ps1 -SlackWebhook "URL"`

**Microsoft Teams:**
1. Add "Incoming Webhook" connector to channel
2. Copy webhook URL
3. Launch: `.\AEGIS_AI_ELITE.ps1 -TeamsWebhook "URL"`

---

## 🎤 VOICE FEATURES

### Voice Commands
AEGIS doesn't recognize voice commands - it only speaks to you.

### Voice Feedback Examples
- **Info**: "Initiating threat scan..."
- **Success**: "Compliance audit complete. Score: 95%"
- **Warning**: "Vendor scan found 5 high-risk vendors"
- **Alert**: "Threat detected. Brute force attack from 192.168.1.100"
- **Critical**: "CRITICAL. Ransomware detected. System isolated."

### Disabling Voice
```powershell
# Command line
.\AEGIS_AI_ELITE.ps1 -VoiceEnabled:$false

# Or in dashboard
Press "7" → Toggle Voice
```

### Troubleshooting Voice
If voice doesn't work:
1. Check Windows TTS is installed
2. Run: `Add-Type -AssemblyName System.Speech`
3. Test: `(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("Test")`
4. AEGIS will continue without voice if initialization fails

---

## 🐛 TROUBLESHOOTING

### "Administrator privileges required"
- Right-click PowerShell → Run as Administrator
- Or: Press Win+X → Windows PowerShell (Admin)

### "Event log access denied"
- Ensure running as Administrator
- Check Event Log service is running
- Verify user is in Event Log Readers group

### "No threats detected but I know there are issues"
- Thresholds may be too high - lower them
- Check Event Logging is enabled: `wevtutil gl Security`
- Verify Security log has recent events

### Voice not working
- AEGIS continues without voice (by design)
- Install Windows TTS voices if needed
- Check audio output device is working
- Try: `Get-InstalledVoice` in System.Speech.Synthesis

### High false positive rate
- Increase thresholds in configuration
- Add legitimate software to vendor database
- Review and tune after baseline period (1 week)

### Slow scans
- Reduce scan scope (disable deep scan features)
- Increase scan interval for continuous mode
- Close unnecessary applications
- Check disk I/O performance

### Auto-response blocking legitimate traffic
1. **Immediate**: Disable auto-response (Option 6)
2. View blocked items (Option 4)
3. Manually remove firewall rules:
   ```powershell
   Get-NetFirewallRule -DisplayName "AEGIS_Block_*" | Remove-NetFirewallRule
   ```
4. Adjust FailedLogons threshold higher
5. Re-enable with caution

---

## 📁 FILES & DIRECTORIES

### Log Files
```
C:\ProgramData\ClearGlassCorp\AEGIS_Elite\Logs\AEGIS_YYYYMMDD.log
```
- JSON format, one entry per line
- Daily rotation
- Parse with: `Get-Content | ConvertFrom-Json`

### Reports
```
C:\ProgramData\ClearGlassCorp\AEGIS_Elite\Reports\AEGIS_Report_*.json
```
- Comprehensive security report
- JSON format
- Generated via Option 18

### Quarantine
```
C:\ProgramData\ClearGlassCorp\AEGIS_Elite\Quarantine\
```
- Stores quarantined executables
- Review before deletion
- Can be analyzed with tools like VirusTotal

### Baselines
```
C:\ProgramData\ClearGlassCorp\AEGIS_Elite\Baseline\baseline_YYYYMMDD.json
```
- System activity baselines
- Manual update: Run scan with -Baseline flag
- Used for anomaly detection

---

## 🔐 SECURITY RECOMMENDATIONS

### Before Production Deployment
1. ✓ Test in lab environment
2. ✓ Tune thresholds for your environment
3. ✓ Configure cloud alerting
4. ✓ Document baseline values
5. ✓ Train security team on tool
6. ✓ Plan incident response procedures

### After Deployment
1. ✓ Monitor for false positives (first week)
2. ✓ Review logs daily
3. ✓ Export weekly reports
4. ✓ Update vendor database monthly
5. ✓ Archive logs quarterly
6. ✓ Re-baseline after major changes

### Auto-Response Best Practices
1. **Start disabled** - Learn your environment first
2. **Test manually** - Verify each response action works
3. **Document procedures** - Know how to rollback
4. **Monitor closely** - Watch for false positives
5. **Gradual rollout** - Test servers → workstations

---

## 💡 PRO TIPS

### Tip 1: Baseline After Hours
Run initial baseline during low-activity period:
```powershell
.\AEGIS_AI_ELITE.ps1 -Mode Hunt -Baseline
```

### Tip 2: Schedule Regular Scans
Create scheduled task:
```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-File C:\Path\To\AEGIS_AI_ELITE.ps1 -Mode Hunt"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "AEGIS Daily Scan" -Action $action `
    -Trigger $trigger -Principal $principal
```

### Tip 3: Export Reports Automatically
Add to scheduled task:
```powershell
-Argument "-File C:\Path\To\AEGIS_AI_ELITE.ps1 -Mode Hunt; Get-Content C:\ProgramData\...\Reports\*.json -Tail 1 | Out-File C:\Reports\Latest.json"
```

### Tip 4: Quick Log Search
```powershell
# Find all THREAT entries
Get-Content "C:\ProgramData\ClearGlassCorp\AEGIS_Elite\Logs\AEGIS_*.log" | 
    ConvertFrom-Json | 
    Where-Object Level -eq 'THREAT'

# Find specific IP
Get-Content "...\AEGIS_*.log" | 
    ConvertFrom-Json | 
    Where-Object {$_.Message -match '192.168.1.100'}
```

### Tip 5: Performance Optimization
- Exclude AEGIS directories from antivirus scanning
- Run deep scans during maintenance windows only
- Use SSD for log directory (faster I/O)
- Limit continuous mode to critical servers

---

## 📞 GETTING HELP

### Self-Help Resources
1. Review log files for error messages
2. Check Technical Documentation (AEGIS_ELITE_TECHNICAL_DOCS.md)
3. Verify system requirements met
4. Test with minimal configuration first

### Information to Collect
When reporting issues:
1. PowerShell version: `$PSVersionTable`
2. Windows version: `Get-ComputerInfo | Select WindowsVersion`
3. Error messages from logs
4. Steps to reproduce
5. Expected vs actual behavior

---

## ⚖️ LEGAL & COMPLIANCE

**Authorized Use Only**: Deploy only on systems you own or are authorized to protect.

**Privacy**: This tool monitors system activity. Ensure compliance with:
- Company IT policies
- Privacy regulations (GDPR, CCPA, etc.)
- Employee monitoring laws
- Data retention policies

**Audit Trail**: All actions are logged. Logs may be subject to:
- Legal discovery
- Compliance audits
- Forensic investigation
- Regulatory review

**No Warranty**: Provided "as-is". User responsible for:
- Proper configuration
- False positive management
- Incident response
- Legal compliance

---

## 🎯 QUICK WIN SCENARIOS

### Scenario 1: Detect Active Brute Force
```
1. Launch AEGIS
2. Press "1" → Standard Scan
3. If brute force detected:
   - Note source IP
   - Press "6" → Enable auto-response
   - Press "1" → Re-scan
   - IP will be automatically blocked
4. Verify with: Get-NetFirewallRule -DisplayName "AEGIS_Block_*"
```

### Scenario 2: Find Risky Software
```
1. Press "10" → Vendor Scan
2. Press "12" → High-Risk Vendors
3. For each vendor:
   - Press "11" → Enter vendor name
   - Review risk factors
   - Take action per recommendations
```

### Scenario 3: Improve Compliance Score
```
1. Press "15" → Compliance Audit
2. Note failed controls
3. Fix each finding:
   - Windows Defender → Enable real-time
   - Firewall → Enable all profiles
   - SMBv1 → Disable (run as admin):
     Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol
   - etc.
4. Press "15" → Re-audit
5. Verify score improved
```

---

**End of Quick Start Guide**

*Get started in minutes, master in hours.*
