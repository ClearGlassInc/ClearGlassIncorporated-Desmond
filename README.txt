# CLEARGLASS SECURITY SUITE — v2.0/v3.0
**Author:** Desmond | CLEARGLASS Security Solutions  
**Components:** Guardian v3 (PS) · Recon v2 (PS) · Python Suite v2

---

## ⚡ WHAT'S NEW — PARALLEL ENGINE

Both PowerShell scripts and the Python version now use **true concurrency** instead of sequential execution.

| Component | Engine | Speedup |
|---|---|---|
| GUARDIAN v3 security baseline | PowerShell Runspace Pool | 3-5x faster (10 checks simultaneously) |
| RECON v2 market scan | PowerShell Runspace Pool | 4 modules in 1 pass |
| Python Suite | asyncio + ThreadPoolExecutor | All checks concurrent |
| Network /24 scan | Parallel ping via runspaces | ~90s → ~4s |

---

## FILES

| File | Description |
|---|---|
| `CLEARGLASS_GUARDIAN_v3.ps1` | Security monitoring (PowerShell, requires Admin) |
| `CLEARGLASS_RECON_v2.ps1` | Market intelligence (PowerShell) |
| `clearglass_suite.py` | Full suite in Python (asyncio) |
| `CLEARGLASS_EULA.txt` | End User License Agreement |
| `CLEARGLASS_LICENSE.txt` | Software license |
| `README.txt` | This file |

---

## REQUIREMENTS

### PowerShell Scripts
- Windows PowerShell 5.1+ or PowerShell 7+
- **GUARDIAN requires Administrator privileges**
- RECON does NOT require Administrator

### Python Script
```bash
pip install psutil colorama tabulate
```
- Python 3.8+
- Works on Windows, Linux, macOS

---

## QUICK START

### GUARDIAN v3 (PowerShell)
```powershell
# Run as Administrator
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\CLEARGLASS_GUARDIAN_v3.ps1

# Options
.\CLEARGLASS_GUARDIAN_v3.ps1 -MaxRunspaces 32    # More threads
.\CLEARGLASS_GUARDIAN_v3.ps1 -SuppressSound       # No audio alerts
.\CLEARGLASS_GUARDIAN_v3.ps1 -ScanIntervalSeconds 30  # Faster monitoring
```

### RECON v2 (PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\CLEARGLASS_RECON_v2.ps1

# Options
.\CLEARGLASS_RECON_v2.ps1 -MaxRunspaces 32
.\CLEARGLASS_RECON_v2.ps1 -ExportOnScan   # Auto-export JSON after each scan
```

### Python Suite
```bash
python clearglass_suite.py
```

---

## PARALLEL ENGINE — TECHNICAL DETAILS

### PowerShell Runspace Pool
The `Initialize-RunspacePool` function creates a shared pool of reusable
runspaces (up to `MaxRunspaces`, default 16). `Invoke-Parallel` dispatches
an array of scriptblocks simultaneously via `BeginInvoke()`, then collects
results with `EndInvoke()` and a configurable timeout.

**Key difference from PowerShell Jobs:**
- Jobs spawn new processes (~200ms overhead each)
- Runspaces share a process, start in <1ms
- Thread-safe collections (ConcurrentBag, ConcurrentQueue) prevent race conditions

### Python asyncio + Executor
`asyncio.gather()` dispatches coroutines; CPU-bound checks use
`loop.run_in_executor(ThreadPoolExecutor)` for true parallelism.

---

## ANOMALY DETECTION

GUARDIAN v3 and the Python suite include a **statistical anomaly engine**:

1. Maintains a rolling 30-scan window of metrics (failed logins, connections, processes)
2. Computes mean and standard deviation per metric
3. Alerts when current value exceeds `mean + (2.5 × stddev)`
4. Requires minimum 5 scans before alerting (to build baseline)

Adjust `AnomalyDeviationFactor` in Config to tune sensitivity.

---

## REPORT OUTPUTS

- **HTML Reports** — Dark-themed responsive report (opens in browser)
- **JSON Export** — Raw data for integration with SIEM/dashboards
- **Text Reports** — Network performance summaries
- **Alert Logs** — Daily log files in `Logs/alerts_YYYYMMDD.log`

---

## ⚠ AUTHORIZED USE ONLY

This software is for use ONLY on systems and networks you own or have
explicit written authorization to monitor. Unauthorized use is illegal.

See `CLEARGLASS_EULA.txt` for complete legal terms.

---

## TROUBLESHOOTING

| Issue | Solution |
|---|---|
| "Requires Administrator" | Right-click PowerShell → Run as Administrator |
| Execution policy error | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| psutil not found (Python) | `pip install psutil` |
| Empty market scan results | Runspaces initialized — check -MaxRunspaces parameter |
| Slow network scan | Increase MaxRunspaces or reduce subnet size |
| Missing colorama (Python) | `pip install colorama` (optional, runs without it) |
