<#
    ClearGlass-AutoSync.ps1
    Idempotent GitHub Pages sync manager for clearglassinc/clearglassinc.github.io
    Plain ASCII only. No emojis. ExecutionPolicy Bypass invocation pattern only.
#>

[CmdletBinding()]
param(
    [string]$RepoOwner = 'clearglassinc',
    [string]$RepoName  = 'clearglassinc.github.io',
    [string]$BaseBranch = 'main',
    [string]$LiveUrl    = 'https://clearglassinc.github.io'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Script:RepoRoot       = (Get-Location).Path
$Script:ProtectedFiles = @('index.html', 'CNAME', '.nojekyll')
$Script:ProtectedDirs  = @('.github/workflows')
$Script:LogDir         = Join-Path $Script:RepoRoot 'logs'
$Script:LogFile        = Join-Path $Script:LogDir ("automation-{0}.log" -f (Get-Date -Format 'yyyyMM'))
$Script:IndexHashBefore = $null
$Script:CurrentFeatureBranch = $null

# ---------------------------------------------------------------------------
# Utility: ASCII-only console output
# ---------------------------------------------------------------------------
function Write-Plain {
    param([string]$Message, [string]$Level = 'INFO')
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    Write-Host $line
}

# ---------------------------------------------------------------------------
# Audit log: append UTC-stamped record of every action
# ---------------------------------------------------------------------------
function Write-Audit {
    param([string]$Action, [string]$Detail = '')
    try {
        if (-not (Test-Path -LiteralPath $Script:LogDir)) {
            New-Item -ItemType Directory -Path $Script:LogDir -Force | Out-Null
        }
        $utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        $entry = "{0} | {1} | {2}" -f $utc, $Action, $Detail
        Add-Content -LiteralPath $Script:LogFile -Value $entry -Encoding ascii
    } catch {
        Write-Plain "AUDIT WRITE FAILED: $($_.Exception.Message)" 'ERROR'
    }
}

# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------
function Get-Sha256 {
    param([string]$Path)
    try {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "File not found: $Path"
        }
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    } catch {
        throw "SHA256 failure on $Path : $($_.Exception.Message)"
    }
}

function Test-IndexUnchanged {
    param([string]$ExpectedHash)
    try {
        $current = Get-Sha256 -Path (Join-Path $Script:RepoRoot 'index.html')
        if ($current -ne $ExpectedHash) {
            return $false
        }
        return $true
    } catch {
        Write-Plain "Hash compare failure: $($_.Exception.Message)" 'ERROR'
        return $false
    }
}

# ---------------------------------------------------------------------------
# Command runner with try/catch
# ---------------------------------------------------------------------------
function Invoke-External {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$ArgumentList,
        [switch]$AllowNonZero
    )
    try {
        $output = & $FilePath @ArgumentList 2>&1
        $code = $LASTEXITCODE
        if (-not $AllowNonZero -and $code -ne 0) {
            throw "Command '$FilePath $($ArgumentList -join ' ')' exited $code. Output: $output"
        }
        return [pscustomobject]@{ ExitCode = $code; Output = $output }
    } catch {
        Write-Audit -Action 'EXTERNAL_FAIL' -Detail "$FilePath $($ArgumentList -join ' ') :: $($_.Exception.Message)"
        throw
    }
}

# ---------------------------------------------------------------------------
# Pre-flight: tools, cwd, hash, rebase
# ---------------------------------------------------------------------------
function Invoke-PreFlight {
    Write-Plain '--- PRE-FLIGHT START ---'
    Write-Audit -Action 'PREFLIGHT_START'

    foreach ($tool in @('git','gh','python3')) {
        try {
            $resolved = Get-Command $tool -ErrorAction Stop
            Write-Plain ("Found {0}: {1}" -f $tool, $resolved.Source)
        } catch {
            Write-Plain "Required tool missing on PATH: $tool" 'ERROR'
            Write-Audit -Action 'PREFLIGHT_FAIL' -Detail "missing tool $tool"
            throw "Pre-flight aborted: $tool not found."
        }
    }

    $indexPath = Join-Path $Script:RepoRoot 'index.html'
    if (-not (Test-Path -LiteralPath $indexPath)) {
        Write-Plain 'cwd does not look like the repo root (index.html missing).' 'ERROR'
        Write-Audit -Action 'PREFLIGHT_FAIL' -Detail 'index.html missing'
        throw 'Pre-flight aborted: must run from repo root.'
    }

    try {
        $insideRepo = Invoke-External -FilePath 'git' -ArgumentList @('rev-parse','--is-inside-work-tree')
        if (($insideRepo.Output -join '').Trim() -ne 'true') {
            throw 'Not inside a git work tree.'
        }
    } catch {
        Write-Plain "git work tree check failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'PREFLIGHT_FAIL' -Detail 'not a git work tree'
        throw
    }

    $Script:IndexHashBefore = Get-Sha256 -Path $indexPath
    Write-Plain ("index.html SHA256 (pre): {0}" -f $Script:IndexHashBefore)
    Write-Audit -Action 'HASH_PRE' -Detail $Script:IndexHashBefore

    Write-Plain 'Fetching origin and rebasing main...'
    try {
        Invoke-External -FilePath 'git' -ArgumentList @('fetch','origin',$BaseBranch) | Out-Null
        Invoke-External -FilePath 'git' -ArgumentList @('pull','--rebase','origin',$BaseBranch) | Out-Null
    } catch {
        Write-Plain "Rebase failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'REBASE_FAIL' -Detail $_.Exception.Message
        throw
    }

    if (-not (Test-IndexUnchanged -ExpectedHash $Script:IndexHashBefore)) {
        $postHash = Get-Sha256 -Path $indexPath
        Write-Plain "WARNING: index.html changed during rebase. pre=$($Script:IndexHashBefore) post=$postHash" 'WARN'
        Write-Audit -Action 'HASH_DRIFT_REBASE' -Detail "pre=$($Script:IndexHashBefore) post=$postHash"
        $Script:IndexHashBefore = $postHash
    }

    Write-Plain '--- PRE-FLIGHT OK ---'
    Write-Audit -Action 'PREFLIGHT_OK' -Detail $Script:IndexHashBefore
}

# ---------------------------------------------------------------------------
# Protected-path guard
# ---------------------------------------------------------------------------
function Test-IsProtectedPath {
    param([string]$RelativePath)
    $norm = $RelativePath -replace '\\','/'
    foreach ($p in $Script:ProtectedFiles) {
        if ($norm -ieq $p) { return $true }
    }
    foreach ($d in $Script:ProtectedDirs) {
        if ($norm -ilike "$d/*" -or $norm -ieq $d) { return $true }
    }
    return $false
}

# ---------------------------------------------------------------------------
# Stage non-protected changes
# ---------------------------------------------------------------------------
function Invoke-StageChanges {
    Write-Plain '--- STAGE START ---'
    Write-Audit -Action 'STAGE_START'

    if (-not $Script:IndexHashBefore) {
        throw 'Run pre-flight (option 1) before staging.'
    }

    $statusResult = Invoke-External -FilePath 'git' -ArgumentList @('status','--porcelain=v1')
    $lines = @($statusResult.Output | Where-Object { $_ -and $_.ToString().Trim() -ne '' })

    if ($lines.Count -eq 0) {
        Write-Plain 'No changes detected. Nothing to stage.'
        Write-Audit -Action 'STAGE_NOOP'
        return
    }

    $staged   = New-Object System.Collections.Generic.List[string]
    $skipped  = New-Object System.Collections.Generic.List[string]

    foreach ($raw in $lines) {
        $entry = $raw.ToString()
        if ($entry.Length -lt 4) { continue }
        $path = $entry.Substring(3).Trim()
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Trim('"')
        }
        if ($path -match ' -> ') {
            $path = ($path -split ' -> ')[-1]
        }

        if (Test-IsProtectedPath -RelativePath $path) {
            $skipped.Add($path) | Out-Null
            continue
        }

        try {
            Invoke-External -FilePath 'git' -ArgumentList @('add','--',$path) | Out-Null
            $staged.Add($path) | Out-Null
        } catch {
            Write-Plain "Failed to stage $path : $($_.Exception.Message)" 'ERROR'
            Write-Audit -Action 'STAGE_FAIL' -Detail "$path :: $($_.Exception.Message)"
        }
    }

    foreach ($p in $Script:ProtectedFiles) {
        try { Invoke-External -FilePath 'git' -ArgumentList @('reset','HEAD','--',$p) -AllowNonZero | Out-Null } catch {}
    }
    foreach ($d in $Script:ProtectedDirs) {
        try { Invoke-External -FilePath 'git' -ArgumentList @('reset','HEAD','--',$d) -AllowNonZero | Out-Null } catch {}
    }

    Write-Plain ("Staged: {0}" -f $staged.Count)
    foreach ($s in $staged)  { Write-Plain ("  + {0}" -f $s) }
    Write-Plain ("Skipped (protected): {0}" -f $skipped.Count)
    foreach ($s in $skipped) { Write-Plain ("  ! {0}" -f $s) }

    if (-not (Test-IndexUnchanged -ExpectedHash $Script:IndexHashBefore)) {
        Write-Plain 'ABORT: index.html hash changed during stage. Rolling back stage.' 'ERROR'
        Write-Audit -Action 'STAGE_HASH_DRIFT' -Detail 'rollback'
        Invoke-External -FilePath 'git' -ArgumentList @('reset','HEAD') -AllowNonZero | Out-Null
        throw 'Stage aborted due to protected-file hash drift.'
    }

    Write-Audit -Action 'STAGE_OK' -Detail ("staged={0} skipped={1}" -f $staged.Count, $skipped.Count)
    Write-Plain '--- STAGE OK ---'
}

# ---------------------------------------------------------------------------
# Commit on a fresh feature branch
# ---------------------------------------------------------------------------
function Invoke-Commit {
    Write-Plain '--- COMMIT START ---'
    Write-Audit -Action 'COMMIT_START'

    if (-not $Script:IndexHashBefore) {
        throw 'Run pre-flight (option 1) before commit.'
    }

    $cachedResult = Invoke-External -FilePath 'git' -ArgumentList @('diff','--cached','--name-only')
    $cached = @($cachedResult.Output | Where-Object { $_ -and $_.ToString().Trim() -ne '' })
    if ($cached.Count -eq 0) {
        Write-Plain 'No staged changes. Run option 2 first.'
        Write-Audit -Action 'COMMIT_NOOP'
        return
    }

    foreach ($c in $cached) {
        if (Test-IsProtectedPath -RelativePath $c.ToString().Trim()) {
            Write-Plain "ABORT: protected path found in staged set: $c" 'ERROR'
            Write-Audit -Action 'COMMIT_BLOCKED' -Detail "protected staged: $c"
            throw 'Commit aborted: protected path in index.'
        }
    }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmm'
    $featureBranch = "auto/sync-$stamp"

    try {
        Invoke-External -FilePath 'git' -ArgumentList @('checkout','-B',$featureBranch) | Out-Null
        $Script:CurrentFeatureBranch = $featureBranch
        Write-Plain ("Feature branch: {0}" -f $featureBranch)
        Write-Audit -Action 'BRANCH_CREATE' -Detail $featureBranch
    } catch {
        Write-Plain "Branch create failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'BRANCH_FAIL' -Detail $_.Exception.Message
        throw
    }

    $defaultMsg = "auto: sync working assets {0}" -f (Get-Date -Format 'yyyy-MM-dd')
    $inputMsg = Read-Host -Prompt ("Commit message [default: {0}]" -f $defaultMsg)
    if ([string]::IsNullOrWhiteSpace($inputMsg)) { $inputMsg = $defaultMsg }

    try {
        Invoke-External -FilePath 'git' -ArgumentList @('commit','-m',$inputMsg) | Out-Null
        Write-Plain ("Commit created: {0}" -f $inputMsg)
        Write-Audit -Action 'COMMIT_OK' -Detail $inputMsg
    } catch {
        Write-Plain "Commit failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'COMMIT_FAIL' -Detail $_.Exception.Message
        throw
    }

    if (-not (Test-IndexUnchanged -ExpectedHash $Script:IndexHashBefore)) {
        Write-Plain 'ABORT: index.html hash drift after commit.' 'ERROR'
        Write-Audit -Action 'COMMIT_HASH_DRIFT' -Detail 'rollback advised'
        throw 'Hash drift detected after commit. Use rollback (option 6).'
    }

    Write-Plain '--- COMMIT OK ---'
}

# ---------------------------------------------------------------------------
# Push to feature branch and open PR with auto-merge disabled
# ---------------------------------------------------------------------------
function Invoke-PushAndPR {
    Write-Plain '--- PUSH + PR START ---'
    Write-Audit -Action 'PUSH_START'

    try {
        $auth = Invoke-External -FilePath 'gh' -ArgumentList @('auth','status') -AllowNonZero
        if ($auth.ExitCode -ne 0) {
            Write-Plain 'gh is not authenticated. Run: gh auth login' 'ERROR'
            Write-Audit -Action 'GH_AUTH_FAIL' -Detail ($auth.Output -join '; ')
            exit 1
        }
    } catch {
        Write-Plain "gh auth check failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'GH_AUTH_ERR' -Detail $_.Exception.Message
        exit 1
    }

    $branchResult = Invoke-External -FilePath 'git' -ArgumentList @('rev-parse','--abbrev-ref','HEAD')
    $currentBranch = ($branchResult.Output -join '').Trim()
    if (-not $currentBranch.StartsWith('auto/sync-')) {
        Write-Plain "Refusing to push: current branch '$currentBranch' is not a feature branch." 'ERROR'
        Write-Audit -Action 'PUSH_BLOCKED' -Detail "branch=$currentBranch"
        throw 'Push aborted: not on auto/sync-* branch.'
    }
    if ($currentBranch -eq $BaseBranch) {
        Write-Plain "Refusing to push directly to $BaseBranch." 'ERROR'
        Write-Audit -Action 'PUSH_BLOCKED' -Detail "branch=$currentBranch"
        throw "Push aborted: on $BaseBranch."
    }

    $attempt = 0
    $maxAttempts = 4
    $delays = @(2,4,8,16)
    $pushed = $false
    while (-not $pushed -and $attempt -lt $maxAttempts) {
        try {
            Invoke-External -FilePath 'git' -ArgumentList @('push','-u','origin',$currentBranch) | Out-Null
            $pushed = $true
        } catch {
            $attempt += 1
            if ($attempt -ge $maxAttempts) {
                Write-Plain "Push failed after $attempt attempts: $($_.Exception.Message)" 'ERROR'
                Write-Audit -Action 'PUSH_FAIL' -Detail $_.Exception.Message
                throw
            }
            $wait = $delays[$attempt - 1]
            Write-Plain ("Push attempt {0} failed. Retrying in {1}s..." -f $attempt, $wait) 'WARN'
            Write-Audit -Action 'PUSH_RETRY' -Detail "attempt=$attempt wait=$wait"
            Start-Sleep -Seconds $wait
        }
    }
    Write-Plain ("Pushed branch: {0}" -f $currentBranch)
    Write-Audit -Action 'PUSH_OK' -Detail $currentBranch

    $prTitle = "auto-sync: $currentBranch"
    $prBody  = "Automated working-asset sync from ClearGlass-AutoSync.ps1. Protected files (index.html, CNAME, .nojekyll, .github/workflows/*) untouched. Auto-merge disabled."

    try {
        $pr = Invoke-External -FilePath 'gh' -ArgumentList @('pr','create','--base',$BaseBranch,'--head',$currentBranch,'--title',$prTitle,'--body',$prBody) -AllowNonZero
        if ($pr.ExitCode -eq 0) {
            Write-Plain ("PR created. Output: {0}" -f ($pr.Output -join ' '))
            Write-Audit -Action 'PR_OK' -Detail ($pr.Output -join ' ')
        } else {
            Write-Plain ("PR create returned non-zero. Output: {0}" -f ($pr.Output -join ' ')) 'WARN'
            Write-Audit -Action 'PR_WARN' -Detail ($pr.Output -join ' ')
        }
    } catch {
        Write-Plain "PR create failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'PR_FAIL' -Detail $_.Exception.Message
        throw
    }

    try {
        $disable = Invoke-External -FilePath 'gh' -ArgumentList @('pr','merge',$currentBranch,'--disable-auto') -AllowNonZero
        Write-Audit -Action 'AUTOMERGE_DISABLE' -Detail ("exit=$($disable.ExitCode)")
    } catch {
        Write-Audit -Action 'AUTOMERGE_DISABLE_WARN' -Detail $_.Exception.Message
    }

    if (-not (Test-IndexUnchanged -ExpectedHash $Script:IndexHashBefore)) {
        Write-Plain 'ABORT: index.html hash drift after push.' 'ERROR'
        Write-Audit -Action 'PUSH_HASH_DRIFT' -Detail 'investigate'
        throw 'Hash drift detected after push.'
    }

    Write-Plain '--- PUSH + PR OK ---'
}

# ---------------------------------------------------------------------------
# Deploy check: curl live site, assert 200 and (best-effort) hash hint
# ---------------------------------------------------------------------------
function Invoke-DeployCheck {
    Write-Plain '--- DEPLOY CHECK START ---'
    Write-Audit -Action 'DEPLOY_CHECK_START' -Detail $LiveUrl

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("clearglass-live-{0}.html" -f ([guid]::NewGuid().ToString('N')))
    try {
        $curl = Invoke-External -FilePath 'curl' -ArgumentList @('-sS','-L','-o',$tmp,'-w','%{http_code}',$LiveUrl) -AllowNonZero
        $code = ($curl.Output -join '').Trim()
        Write-Plain ("HTTP status: {0}" -f $code)
        Write-Audit -Action 'DEPLOY_HTTP' -Detail $code
        if ($code -ne '200') {
            throw "Live site returned HTTP $code"
        }

        $liveHash  = Get-Sha256 -Path $tmp
        $localHash = Get-Sha256 -Path (Join-Path $Script:RepoRoot 'index.html')
        Write-Plain ("Local index.html SHA256 : {0}" -f $localHash)
        Write-Plain ("Live  index.html SHA256 : {0}" -f $liveHash)
        if ($liveHash -eq $localHash) {
            Write-Plain 'Deploy hash MATCH.'
            Write-Audit -Action 'DEPLOY_MATCH' -Detail $liveHash
        } else {
            Write-Plain 'Deploy hash MISMATCH (expected if CDN cache lag or local edits pending).' 'WARN'
            Write-Audit -Action 'DEPLOY_MISMATCH' -Detail ("local=$localHash live=$liveHash")
        }
    } catch {
        Write-Plain "Deploy check failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'DEPLOY_FAIL' -Detail $_.Exception.Message
        throw
    } finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Plain '--- DEPLOY CHECK OK ---'
}

# ---------------------------------------------------------------------------
# Rollback: hard reset to origin/main with confirmation
# ---------------------------------------------------------------------------
function Invoke-Rollback {
    Write-Plain '--- ROLLBACK START ---'
    Write-Audit -Action 'ROLLBACK_REQUEST'

    $confirm = Read-Host -Prompt "Type EXACTLY 'ROLLBACK' to hard-reset to origin/$BaseBranch"
    if ($confirm -cne 'ROLLBACK') {
        Write-Plain 'Rollback cancelled.'
        Write-Audit -Action 'ROLLBACK_CANCEL'
        return
    }

    try {
        Invoke-External -FilePath 'git' -ArgumentList @('fetch','origin',$BaseBranch) | Out-Null
        Invoke-External -FilePath 'git' -ArgumentList @('checkout',$BaseBranch) | Out-Null
        Invoke-External -FilePath 'git' -ArgumentList @('reset','--hard',"origin/$BaseBranch") | Out-Null
        Write-Plain "Reset to origin/$BaseBranch complete."
        Write-Audit -Action 'ROLLBACK_OK' -Detail "origin/$BaseBranch"
    } catch {
        Write-Plain "Rollback failed: $($_.Exception.Message)" 'ERROR'
        Write-Audit -Action 'ROLLBACK_FAIL' -Detail $_.Exception.Message
        throw
    }

    Write-Plain '--- ROLLBACK OK ---'
}

# ---------------------------------------------------------------------------
# Audit log viewer
# ---------------------------------------------------------------------------
function Show-AuditLog {
    Write-Plain '--- AUDIT LOG ---'
    if (-not (Test-Path -LiteralPath $Script:LogFile)) {
        Write-Plain "No log file yet at $($Script:LogFile)."
        return
    }
    try {
        $tail = Get-Content -LiteralPath $Script:LogFile -Tail 50
        foreach ($l in $tail) { Write-Host $l }
        Write-Plain ("Log file: {0}" -f $Script:LogFile)
    } catch {
        Write-Plain "Could not read log: $($_.Exception.Message)" 'ERROR'
    }
}

# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
function Show-Menu {
    Write-Host ''
    Write-Host '======================================================'
    Write-Host '  ClearGlass AutoSync - clearglassinc.github.io'
    Write-Host '======================================================'
    Write-Host '  [1] Pre-flight (verify tools, hash, rebase main)'
    Write-Host '  [2] Stage non-protected changes'
    Write-Host '  [3] Commit (feature branch auto/sync-YYYYMMDD-HHmm)'
    Write-Host '  [4] Push branch and open PR (auto-merge disabled)'
    Write-Host '  [5] Deploy check (curl live site + hash compare)'
    Write-Host '  [6] Rollback (hard reset to origin/main)'
    Write-Host '  [7] View audit log tail'
    Write-Host '  [0] Exit'
    Write-Host '------------------------------------------------------'
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
Write-Plain ("Repo root: {0}" -f $Script:RepoRoot)
Write-Plain ("Log file : {0}" -f $Script:LogFile)
Write-Audit -Action 'SESSION_START' -Detail $Script:RepoRoot

while ($true) {
    try {
        Show-Menu
        $choice = Read-Host -Prompt 'Select option'
        switch ($choice) {
            '1' { Invoke-PreFlight }
            '2' { Invoke-StageChanges }
            '3' { Invoke-Commit }
            '4' { Invoke-PushAndPR }
            '5' { Invoke-DeployCheck }
            '6' { Invoke-Rollback }
            '7' { Show-AuditLog }
            '0' {
                Write-Plain 'Exit requested.'
                Write-Audit -Action 'SESSION_END'
                break
            }
            default {
                Write-Plain 'Invalid selection.' 'WARN'
            }
        }
        if ($choice -eq '0') { break }
    } catch {
        Write-Plain ("Operation failed: {0}" -f $_.Exception.Message) 'ERROR'
        Write-Audit -Action 'OP_FAIL' -Detail $_.Exception.Message
    }
}
