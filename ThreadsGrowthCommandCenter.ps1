<#
.SYNOPSIS
    Builds an ethical, manual Threads growth command center for ClearGlassInc Artemis.
.DESCRIPTION
    Creates local folders, CSV trackers, draft post templates, a daily operating plan,
    and an HTML dashboard for a Threads/Instagram growth workflow. The script is
    intentionally manual-only: it does not log in, scrape, auto-follow, auto-like,
    auto-comment, auto-post, mass-message, or store credentials.
.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File .\ThreadsGrowthCommandCenter.ps1 -OpenDashboard
.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File .\ThreadsGrowthCommandCenter.ps1 -BrandName "MyBrand" -Niche "SaaS security" -RootPath "C:\Growth" -OpenDashboard
#>
[CmdletBinding()]
param(
    [string]$BrandName = 'ClearGlassInc Artemis',
    [string]$Niche = 'AI security, intelligence systems, crypto discipline, and operational sovereignty',
    [string]$RootPath = (Join-Path (Get-Location) 'ThreadsGrowthCommandCenter'),
    [switch]$OpenDashboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-DirectoryIfMissing {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-FileIfMissing {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        $Content | Set-Content -LiteralPath $Path -Encoding UTF8
    }
}

function ConvertTo-HtmlEncodedText {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Net.WebUtility]::HtmlEncode($Value)
}

function New-ThreadsHookLibrary {
    return @(
        'Most brands do not need more noise. They need a system that compounds trust.',
        'The fastest way to look serious online is to show proof of work before opinions.',
        'A clean operating rhythm beats a viral post you cannot repeat.',
        'Security, revenue, and reputation all break when nobody owns the checklist.',
        'If your content cannot survive a compliance review, it is not an asset.',
        'Discipline is the algorithm most people refuse to run.',
        'Crypto rewards patience, records, and risk control more than adrenaline.',
        'AI is only powerful when the workflow around it is measurable.',
        'A founder with a documented system is harder to ignore.',
        'The internet trusts receipts, not declarations.'
    )
}

function New-DraftBody {
    param(
        [Parameter(Mandatory = $true)][string]$Hook,
        [Parameter(Mandatory = $true)][string]$BrandName,
        [Parameter(Mandatory = $true)][string]$Niche,
        [Parameter(Mandatory = $true)][string]$Pillar,
        [Parameter(Mandatory = $true)][int]$Index
    )

    return @"
$Hook

Core point:
$BrandName is building around $Niche. The point is not to post randomly; the point is to publish proof, operating lessons, and decision frameworks that make the brand easier to trust.

Proof:
Today I am documenting pillar $Pillar with a repeatable workflow: idea -> evidence -> useful takeaway -> manual conversation.

Takeaway:
If the content cannot help a real operator think more clearly, it is not ready.

CTA:
If you are building in $Niche, save this and compare it against your own system today.

Manual review checklist:
[ ] No hype claim
[ ] No guaranteed income language
[ ] No spam, scraping, mass DM, or fake engagement tactic
[ ] Includes one proof point or concrete lesson
[ ] Ready to post manually on Threads

Draft ID: THREADS-DRAFT-$('{0:D2}' -f $Index)
"@
}

function Initialize-ThreadsGrowthCommandCenter {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$BrandName,
        [Parameter(Mandatory = $true)][string]$Niche
    )

    foreach ($folder in @('Drafts', 'Calendars', 'Analytics', 'Engagement', 'DailyPlans', 'Reports')) {
        New-DirectoryIfMissing -Path (Join-Path $BasePath $folder)
    }

    $calendarPath = Join-Path $BasePath 'Calendars/ContentCalendar.csv'
    Write-FileIfMissing -Path $calendarPath -Content @'
Date,Pillar,Topic,Format,CTA,Status,Notes
2026-07-06,Authority,AI security operating checklist,Text post,Save this checklist,Draft,Manual post only
2026-07-07,Business,ClearGlassInc proof-of-work update,Mini-thread,Reply with the system you are building,Draft,Add real proof before posting
2026-07-08,Mindset,Discipline as infrastructure,Text post,Bookmark for daily review,Draft,Keep practical
2026-07-09,Crypto,Risk control beats hype,Text post,Track your rules before your wins,Draft,No financial promises
2026-07-10,Operations,Daily command rhythm,Checklist,Steal this operating rhythm,Draft,Manual engagement after posting
'@

    $kpiPath = Join-Path $BasePath 'Analytics/ThreadsKPITracker.csv'
    Write-FileIfMissing -Path $kpiPath -Content 'Date,Followers,Posts,Replies,Likes,Reposts,Impressions,ProfileVisits,Notes'

    $engagementPath = Join-Path $BasePath 'Engagement/EngagementTracker.csv'
    Write-FileIfMissing -Path $engagementPath -Content 'Date,Creator,CreatorTopic,YourComment,ResponseReceived,FollowUpDate,Outcome,Notes'

    $hooks = New-ThreadsHookLibrary
    $pillars = @('Authority', 'Business', 'Mindset', 'Crypto', 'Operations')
    for ($i = 1; $i -le 10; $i++) {
        $hook = $hooks[($i - 1) % $hooks.Count]
        $pillar = $pillars[($i - 1) % $pillars.Count]
        $draftPath = Join-Path $BasePath ("Drafts/THREADS-DRAFT-{0:D2}.txt" -f $i)
        Write-FileIfMissing -Path $draftPath -Content (New-DraftBody -Hook $hook -BrandName $BrandName -Niche $Niche -Pillar $pillar -Index $i)
    }

    $today = (Get-Date).ToString('yyyy-MM-dd')
    $dailyPlanPath = Join-Path $BasePath "DailyPlans/DailyPlan_$today.txt"
    Write-FileIfMissing -Path $dailyPlanPath -Content @"
$BrandName Threads Daily Growth Plan — $today

Niche:
$Niche

Non-negotiables:
[ ] Publish 2 original manual posts from Drafts or Calendar
[ ] Leave 15 thoughtful strategic replies by hand
[ ] Study 5 competitor or peer posts and write one lesson each
[ ] Update Analytics/ThreadsKPITracker.csv
[ ] Update Engagement/EngagementTracker.csv
[ ] Write one improvement note before ending the day

Rules:
- No bots, scraping, follow/unfollow, fake engagement, engagement pods, or mass DMs.
- No passwords, cookies, API keys, or session tokens in this folder.
- Use proof, useful thinking, and real replies. Manual review always wins.
"@

    $safeBrand = ConvertTo-HtmlEncodedText -Value $BrandName
    $safeNiche = ConvertTo-HtmlEncodedText -Value $Niche
    $dashboardPath = Join-Path $BasePath 'Reports/ThreadsGrowthDashboard.html'
    Write-FileIfMissing -Path $dashboardPath -Content @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$safeBrand Threads Growth Dashboard</title>
  <style>
    body { font-family: Inter, Segoe UI, Arial, sans-serif; margin: 0; background: #09090b; color: #f4f4f5; }
    main { max-width: 1100px; margin: 0 auto; padding: 40px 24px; }
    .hero { border: 1px solid #27272a; border-radius: 24px; padding: 28px; background: linear-gradient(135deg, #111827, #18181b); }
    h1 { margin-top: 0; font-size: 2.3rem; }
    .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-top: 22px; }
    .card { border: 1px solid #27272a; border-radius: 18px; padding: 18px; background: #111113; }
    a { color: #67e8f9; }
    code { color: #fde68a; }
    .rule { color: #fca5a5; font-weight: 700; }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>$safeBrand Threads Growth Command Center</h1>
      <p><strong>Brand focus:</strong> $safeNiche</p>
      <p class="rule">Manual-only system: no scraping, spam, fake engagement, credential storage, or automation.</p>
    </section>
    <section class="grid">
      <article class="card"><h2>Drafts</h2><p>10 reusable templates using Hook -> Core point -> Proof -> Takeaway -> CTA.</p><p><code>../Drafts</code></p></article>
      <article class="card"><h2>Calendar</h2><p>5 planned posts across Authority, Business, Mindset, Crypto, and Operations.</p><p><a href="../Calendars/ContentCalendar.csv">Open calendar</a></p></article>
      <article class="card"><h2>Analytics</h2><p>Track followers, posts, replies, likes, reposts, impressions, and profile visits.</p><p><a href="../Analytics/ThreadsKPITracker.csv">Open KPI tracker</a></p></article>
      <article class="card"><h2>Engagement</h2><p>Log manual replies, responses, follow-ups, and outcomes.</p><p><a href="../Engagement/EngagementTracker.csv">Open engagement tracker</a></p></article>
      <article class="card"><h2>Daily Plan</h2><p>Run the daily checklist: 2 posts, 15 replies, 5 analyses, KPI update, improvement note.</p><p><code>../DailyPlans</code></p></article>
      <article class="card"><h2>Operating Principle</h2><p>The script does not grow the account. Consistent proof, relevance, and real conversations do.</p></article>
    </section>
  </main>
</body>
</html>
"@

    return [PSCustomObject]@{
        Root = $BasePath
        Calendar = $calendarPath
        KPITracker = $kpiPath
        EngagementTracker = $engagementPath
        DailyPlan = $dailyPlanPath
        Dashboard = $dashboardPath
    }
}

$result = Initialize-ThreadsGrowthCommandCenter -BasePath $RootPath -BrandName $BrandName -Niche $Niche
$result | Format-List

if ($OpenDashboard) {
    if ($IsWindows) { Invoke-Item -LiteralPath $result.Dashboard }
    elseif ($IsMacOS) { & open $result.Dashboard }
    else { Write-Host "Open dashboard manually: $($result.Dashboard)" -ForegroundColor Yellow }
}
