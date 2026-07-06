<#
.SYNOPSIS
    Threads Growth Command Center V3 - Aggressive Execution Model.

.DESCRIPTION
    High-velocity, compliant Threads growth system:
    - 30-day accelerated content calendar
    - Ruthless daily action plan
    - Strict KPI tracking
    - Dynamic HTML dashboard with high-contrast UI

    RULES OF ENGAGEMENT:
    - Zero botting. Zero scraping.
    - Maximum manual volume.
    - If a format fails twice, kill it.

    This is a manual operating system only. It never logs in, auto-posts,
    auto-likes, auto-comments, follows/unfollows, scrapes, mass-DMs, stores
    credentials, or bypasses Threads/Instagram platform rules.
#>

[CmdletBinding()]
param(
    [ValidateSet("Init", "Daily", "AddKPI", "Dashboard", "All")]
    [string]$Mode = "All",

    [string]$BrandName = "ClearGlassInc",

    [string]$Niche = "AI security, business systems, cryptocurrency, discipline, strategy",

    [string]$RootPath = $(if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "Desktop/ThreadsGrowthCommandCenter_V3" } else { Join-Path (Get-Location) "ThreadsGrowthCommandCenter_V3" }),

    [int]$Followers = 0,
    [int]$Posts = 0,
    [int]$Replies = 0,
    [int]$Likes = 0,
    [int]$Reposts = 0,
    [int]$Impressions = 0,
    [int]$ProfileVisits = 0,
    [string]$Notes = "Manual update",
    [switch]$OpenDashboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Folders = @{
    Drafts     = Join-Path $RootPath "Drafts"
    Calendars  = Join-Path $RootPath "Calendars"
    Analytics  = Join-Path $RootPath "Analytics"
    Engagement = Join-Path $RootPath "Engagement"
    Reports    = Join-Path $RootPath "Reports"
    DailyPlans = Join-Path $RootPath "DailyPlans"
    Backups    = Join-Path $RootPath "Backups"
}

$CalendarPath      = Join-Path $Folders.Calendars "ContentCalendar.csv"
$KpiPath           = Join-Path $Folders.Analytics "ThreadsKPITracker.csv"
$EngagementPath    = Join-Path $Folders.Engagement "EngagementTracker.csv"
$FormatReviewPath  = Join-Path $Folders.Analytics "FormatReview.csv"
$DashboardPath     = Join-Path $Folders.Reports "ThreadsGrowthDashboard.html"

function Write-Status {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "[►] $Message" -ForegroundColor $Color
}

function New-FolderSafe {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Initialize-Folders {
    New-FolderSafe -Path $RootPath
    foreach ($folder in $Folders.Values) { New-FolderSafe -Path $folder }
}

function Backup-FileSafe {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        New-FolderSafe -Path $Folders.Backups
        $name = Split-Path $Path -Leaf
        $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $backupPath = Join-Path $Folders.Backups "$stamp`_$name"
        Copy-Item -LiteralPath $Path -Destination $backupPath -Force
    }
}

function Write-CsvIfMissing {
    param([string]$Path, [array]$Rows)
    if (-not (Test-Path -LiteralPath $Path)) {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

function Add-CsvRow {
    param([string]$Path, [pscustomobject]$Row)
    if (-not (Test-Path -LiteralPath $Path)) {
        $Row | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Row | Export-Csv -LiteralPath $Path -NoTypeInformation -Append -Encoding UTF8
    }
}

function ConvertTo-SafeFileName {
    param([string]$Text)
    $safe = $Text -replace '[^\w\s-]', ''
    $safe = $safe -replace '\s+', '_'
    $safe = $safe.Trim("_")
    if ([string]::IsNullOrWhiteSpace($safe)) { return "Untitled" }
    return $safe
}

function Encode-Html {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function Get-RandomHook {
    $hooks = @(
        "You are being outworked by people with half your talent and twice your discipline.",
        "Your business doesn't have a traffic problem. It has a trust problem.",
        "Stop building in secret. Nobody cares about your launch if they didn't see the struggle.",
        "90% of crypto accounts are wiped out by emotion. Here is the math behind survival:",
        "If you rely on motivation to run your company, you are one bad day away from failing.",
        "Most AI tools are liabilities disguised as assets. Here is what real security looks like:",
        "Stop posting generic advice. Show the actual data, operating lesson, or scar tissue.",
        "The market is ruthless. It only pays for systems, leverage, and undeniable proof."
    )
    return Get-Random -InputObject $hooks
}

function New-PostDraft {
    param([string]$Topic, [string]$Pillar, [string]$Format)
    $hook = Get-RandomHook
@"
[HOOK: COPY/PASTE OR REWRITE TO BE SHARPER]
$hook

[TARGET INTEL]
Topic: $Topic
Pillar: $Pillar
Format: $Format

[THE DIRECTIVE]
1. Core Point: No fluff. Make the first sentence impossible to ignore.
2. Proof: Give exact numbers, screenshots, code, lessons, or concrete evidence.
3. Takeaway: What must they change today? Make it actionable.

[CALL TO ACTION]
Follow $BrandName for aggressive manual execution and $Niche systems.

[RUTHLESS EDITING CHECKLIST]
[ ] Did I remove every useless adjective?
[ ] Is the hook impossible to scroll past?
[ ] Does this build authority or just make noise?
[ ] Is there zero botting, scraping, mass-DM, or fake-engagement behavior?
[ ] Is this compliant, truthful, and manually posted?
"@
}

function Get-ContentPlanRows {
    $pillars = @("AI Security", "Business Systems", "Crypto Discipline", "Mindset", "Operations", "Financial Freedom")
    $topics = @{
        "AI Security"       = @("Exposing the silent data leaks in your AI wrappers", "Why AI automation without audit trails is corporate suicide", "The exact framework ClearGlassInc uses to lock down AI")
        "Business Systems"  = @("Productize or die: Why service businesses stall at ten thousand per month", "The exact three-tool stack to replace a junior operations manager", "Licensing knowledge vs selling time")
        "Crypto Discipline" = @("The cold math of risk management: Why one percent sizing wins", "Stop trading the five-minute chart. Here is the macro truth.", "How to build an iron stomach for thirty percent drawdowns")
        "Mindset"           = @("Burn your plan B. It is distracting you.", "If you are not tracking it daily, you do not actually care about it.", "The ROI of saying no to almost every opportunity")
        "Operations"        = @("Friction is the enemy of scale. Here is how to kill it.", "The weekly review system that forces execution", "Why your SOPs are useless and how to fix them")
        "Financial Freedom" = @("Cash flow over vanity metrics, always.", "Building digital real estate vs renting algorithms", "The three-year timeline to exit velocity")
    }
    $formats = @("High-Signal Thread", "Raw Metric Screenshot", "Contrarian Opinion", "Tear-down / Analysis")
    $rows = @()

    for ($i = 0; $i -lt 30; $i++) {
        $date = (Get-Date).Date.AddDays($i)
        $pillar = $pillars[$i % $pillars.Count]
        $topicList = $topics[$pillar]
        $topic = $topicList[$i % $topicList.Count]
        $format = $formats[$i % $formats.Count]

        $rows += [pscustomobject]@{
            Date   = $date.ToString("yyyy-MM-dd")
            Pillar = $pillar
            Topic  = $topic
            Format = $format
            Status = "Pending Manual Attack"
        }
    }
    return $rows
}

function Initialize-Workspace {
    Initialize-Folders
    $calendarRows = Get-ContentPlanRows
    $kpiRows = @(
        [pscustomobject]@{ Date = (Get-Date -Format "yyyy-MM-dd"); Followers = 0; Posts = 0; Replies = 0; Likes = 0; Reposts = 0; Impressions = 0; ProfileVisits = 0; Notes = "Ground Zero" }
    )
    $engagementRows = @(
        [pscustomobject]@{ Date = (Get-Date -Format "yyyy-MM-dd"); Creator = ""; CreatorTopic = ""; YourComment = ""; ResponseReceived = ""; FollowUpDate = ""; Outcome = ""; Notes = "Manual replies only" }
    )
    $formatRows = @(
        [pscustomobject]@{ Format = "High-Signal Thread"; ConsecutiveFails = 0; Status = "Active"; DecisionRule = "If a format fails twice, kill it." }
        [pscustomobject]@{ Format = "Raw Metric Screenshot"; ConsecutiveFails = 0; Status = "Active"; DecisionRule = "If a format fails twice, kill it." }
        [pscustomobject]@{ Format = "Contrarian Opinion"; ConsecutiveFails = 0; Status = "Active"; DecisionRule = "If a format fails twice, kill it." }
        [pscustomobject]@{ Format = "Tear-down / Analysis"; ConsecutiveFails = 0; Status = "Active"; DecisionRule = "If a format fails twice, kill it." }
    )
    Write-CsvIfMissing -Path $CalendarPath -Rows $calendarRows
    Write-CsvIfMissing -Path $KpiPath -Rows $kpiRows
    Write-CsvIfMissing -Path $EngagementPath -Rows $engagementRows
    Write-CsvIfMissing -Path $FormatReviewPath -Rows $formatRows
    Write-Status "Aggressive manual workspace initialized: $RootPath" "Green"
}

function New-DailyPlan {
    $today = Get-Date -Format "yyyy-MM-dd"
@"
=========================================
THREAT & GROWTH BRIEF - $today
=========================================
TARGET: $BrandName
SECTOR: $Niche

THE RULES OF HIGH-VELOCITY MANUAL GROWTH:
1. PUBLISH 3X TODAY. Morning, Afternoon, Evening.
2. 40 REPLIES MINIMUM. Target relevant big accounts manually. Be the best reply in their thread.
3. RUTHLESS PRUNING. If yesterday's format tanked twice, kill it and rotate.

EXECUTION BLOCKS:
[ ] 08:00 - Post 1 (High-Signal / Contrarian) + 15 manual replies
[ ] 13:00 - Post 2 (Proof / Screenshot / Result) + 15 manual replies
[ ] 19:00 - Post 3 (Short insight / Lesson) + 10 manual replies

ENGAGEMENT PROTOCOL:
- Never say "Great post!"
- Add missing context, politely disagree, or contribute a sharper useful truth.
- Steal attention ethically by being useful, specific, and manually present.

EVALUATE AND ADAPT:
- What is the Engagement Rate (ER) of yesterday's top post?
- If ER < 2%, the hook was weak. Fix it.
- If the same format fails twice, mark it Killed in Analytics/FormatReview.csv.

COMPLIANCE LINE:
- Zero botting. Zero scraping. Zero fake engagement. Zero mass DMs. No credentials in this folder.
=========================================
"@
}

function Invoke-DailyWorkflow {
    Initialize-Folders
    if (-not (Test-Path -LiteralPath $CalendarPath)) { Initialize-Workspace }

    $today = Get-Date -Format "yyyy-MM-dd"
    $dailyPlanPath = Join-Path $Folders.DailyPlans "DailyPlan_$today.txt"
    New-DailyPlan | Out-File -LiteralPath $dailyPlanPath -Encoding UTF8

    $calendar = Import-Csv -LiteralPath $CalendarPath
    $todayRows = @($calendar | Where-Object { $_.Date -eq $today })
    if ($todayRows.Count -eq 0) { $todayRows = @($calendar | Select-Object -First 3) }

    foreach ($row in $todayRows) {
        $safeTopic = ConvertTo-SafeFileName -Text $row.Topic
        $draftPath = Join-Path $Folders.Drafts "$today`_$safeTopic.txt"
        if (-not (Test-Path -LiteralPath $draftPath)) {
            New-PostDraft -Topic $row.Topic -Pillar $row.Pillar -Format $row.Format | Out-File -LiteralPath $draftPath -Encoding UTF8
        }
    }
    Write-Status "War Room prepared for $today." "Green"
}

function Add-KpiEntry {
    Initialize-Folders
    if (-not (Test-Path -LiteralPath $KpiPath)) { Initialize-Workspace }
    Backup-FileSafe -Path $KpiPath

    $row = [pscustomobject]@{
        Date = Get-Date -Format "yyyy-MM-dd"
        Followers = $Followers
        Posts = $Posts
        Replies = $Replies
        Likes = $Likes
        Reposts = $Reposts
        Impressions = $Impressions
        ProfileVisits = $ProfileVisits
        Notes = $Notes
    }
    Add-CsvRow -Path $KpiPath -Row $row
    Write-Status "Telemetry logged." "Green"
}

function Convert-RowsToHtmlTable {
    param([array]$Rows, [int]$MaxRows = 10)
    if ($null -eq $Rows -or $Rows.Count -eq 0) { return "<p>No data available.</p>" }
    $selectedRows = @($Rows | Select-Object -First $MaxRows)
    $headers = $selectedRows[0].PSObject.Properties.Name
    $html = "<table><thead><tr>"
    foreach ($header in $headers) { $html += "<th>$(Encode-Html $header)</th>" }
    $html += "</tr></thead><tbody>"
    foreach ($row in $selectedRows) {
        $html += "<tr>"
        foreach ($header in $headers) { $html += "<td>$(Encode-Html $row.$header)</td>" }
        $html += "</tr>"
    }
    $html += "</tbody></table>"
    return $html
}

function New-Dashboard {
    param([switch]$Launch)
    Initialize-Folders
    if (-not (Test-Path -LiteralPath $CalendarPath) -or -not (Test-Path -LiteralPath $KpiPath)) { Initialize-Workspace }

    $calendar = @(Import-Csv -LiteralPath $CalendarPath)
    $kpis = @(Import-Csv -LiteralPath $KpiPath)
    $formats = @(Import-Csv -LiteralPath $FormatReviewPath)

    $latestKpi = $kpis | Select-Object -Last 1
    $upcoming = @($calendar | Where-Object { [datetime]$_.Date -ge (Get-Date).Date } | Select-Object -First 10)
    $recentKpis = @($kpis | Select-Object -Last 10)

    $totalPosts = ($kpis | ForEach-Object { [int]$_.Posts } | Measure-Object -Sum).Sum
    $totalReplies = ($kpis | ForEach-Object { [int]$_.Replies } | Measure-Object -Sum).Sum
    $totalImpressions = ($kpis | ForEach-Object { [int]$_.Impressions } | Measure-Object -Sum).Sum

    $calendarTable = Convert-RowsToHtmlTable -Rows $upcoming -MaxRows 10
    $kpiTable = Convert-RowsToHtmlTable -Rows $recentKpis -MaxRows 10
    $formatTable = Convert-RowsToHtmlTable -Rows $formats -MaxRows 10
    $safeBrand = Encode-Html $BrandName
    $safeNiche = Encode-Html $Niche

    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>$safeBrand Command Center V3</title>
    <style>
        :root { --bg: #09090b; --card: #18181b; --accent: #dc2626; --text: #f4f4f5; --muted: #a1a1aa; --border: #27272a; }
        body { font-family: Inter, Arial, sans-serif; background: var(--bg); color: var(--text); padding: 40px; margin: 0; }
        h1, h2 { color: #fff; text-transform: uppercase; letter-spacing: 1px; }
        h1 { border-bottom: 2px solid var(--accent); display: inline-block; padding-bottom: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: var(--card); border: 1px solid var(--border); border-left: 4px solid var(--accent); padding: 24px; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .metric { font-size: 38px; font-weight: 900; margin-top: 10px; color: #fff; }
        .label { color: var(--muted); font-size: 13px; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; background: var(--card); }
        th, td { border: 1px solid var(--border); padding: 12px; text-align: left; }
        th { background: #202024; color: var(--muted); text-transform: uppercase; font-size: 12px; }
        td { color: #e4e4e7; }
        .truth { border-left: 4px solid var(--accent); padding-left: 16px; font-size: 18px; font-weight: bold; color: #fff; font-style: italic; }
        .compliance { color: #fecaca; font-weight: 800; }
    </style>
</head>
<body>
    <h1>SYSTEM V3: $safeBrand</h1>
    <p><strong>Sector:</strong> $safeNiche</p>
    <p class="compliance">Manual-only: zero botting, zero scraping, zero fake engagement, zero mass DMs, zero credential storage.</p>
    <div class="grid">
        <div class="card"><div class="label">Total Followers</div><div class="metric">$(Encode-Html $latestKpi.Followers)</div></div>
        <div class="card"><div class="label">Posts Fired</div><div class="metric">$totalPosts</div></div>
        <div class="card"><div class="label">Replies Deployed</div><div class="metric">$totalReplies</div></div>
        <div class="card"><div class="label">Total Impressions</div><div class="metric">$totalImpressions</div></div>
    </div>
    <h2>The Standard</h2>
    <p class="truth">If it is not generating replies, reposts, saves, or profile visits, it is noise. Kill the format after two failures and try again tomorrow.</p>
    <h2>Upcoming Firepower</h2>
    $calendarTable
    <h2>Telemetry Logs</h2>
    $kpiTable
    <h2>Format Kill List</h2>
    $formatTable
</body>
</html>
"@
    $html | Out-File -LiteralPath $DashboardPath -Encoding UTF8
    Write-Status "Aggressive UI Dashboard compiled: $DashboardPath" "Green"
    if ($Launch) { Start-Process $DashboardPath }
}

switch ($Mode) {
    "Init"      { Initialize-Workspace }
    "Daily"     { Invoke-DailyWorkflow }
    "AddKPI"    { Add-KpiEntry }
    "Dashboard" { New-Dashboard -Launch:$OpenDashboard }
    "All"       { Initialize-Workspace; Invoke-DailyWorkflow; New-Dashboard -Launch:$OpenDashboard }
}
Write-Host ""
Write-Status "V3 Execution Complete. Go to work." "Red"
