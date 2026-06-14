# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "marketing" / "output"
THREADS_JSON = OUTPUT_DIR / "threads_latest.json"
THREADS_MD = OUTPUT_DIR / "threads_latest.md"
THREADS_ARCHIVE_DIR = OUTPUT_DIR / "threads_archive"
SITE_PAGE = ROOT / "threads.html"


@dataclass(frozen=True)
class Tweet:
    text: str


@dataclass(frozen=True)
class ThreadBundle:
    thread_number: int
    app_name: str
    app_category: str
    audience: str
    emotional_benefit: str
    pain_points: list[str]
    tweets: list[Tweet]


@dataclass(frozen=True)
class GrowthRun:
    run_utc: str
    app_name: str
    total_threads: int
    output_dir: str
    site_page: str


def build_threads(app_name: str = "ClearGlassInc Artemis") -> list[ThreadBundle]:
    common = {
        "app_name": app_name,
        "app_category": "productivity",
        "audience": "young professionals and founders",
        "emotional_benefit": "feeling in control under pressure",
        "pain_points": [
            "task overload",
            "context switching fatigue",
            "forgetting high-impact follow-ups",
        ],
    }

    return [
        ThreadBundle(
            thread_number=1,
            tweets=[
                Tweet("I almost missed the one message that could've changed my week. 😵‍💫"),
                Tweet("I had 17 tabs open, 42 unread pings, and zero idea what actually mattered. 📉"),
                Tweet("Then I ran my day through ClearGlassInc Artemis. It flagged one convo as high-stakes in 8 seconds."),
                Tweet("That single reply turned into a signed deal before lunch. Relief hit hard. ⚡"),
                Tweet("Be honest: how often does noise hide your biggest opportunity? 👇"),
            ],
            **common,
        ),
        ThreadBundle(
            thread_number=2,
            tweets=[
                Tweet("I looked productive. I was actually drowning. 🫠"),
                Tweet("Color-coded calendar. Fancy to-do app. Still ended each day feeling behind and guilty."),
                Tweet("What changed? Artemis showed me where my time leaked, not where it looked busy."),
                Tweet("Two weeks later: fewer tasks, better output, calmer brain. That's the part no one tells you. 🧠"),
                Tweet("Are you optimizing for busy… or for peace + results?"),
            ],
            **common,
        ),
        ThreadBundle(
            thread_number=3,
            tweets=[
                Tweet("The worst part of burnout? You don't notice it until you snap. 🔥"),
                Tweet("I stopped sleeping well. Started forgetting small promises. Confidence dropped quietly."),
                Tweet('Artemis started surfacing "promise-risk" moments before they became trust damage.'),
                Tweet("Catching those early gave me my reputation back. And honestly, myself back too. 🙏"),
                Tweet("Who's felt their credibility slip from tiny misses, not big failures?"),
            ],
            **common,
        ),
        ThreadBundle(
            thread_number=4,
            tweets=[
                Tweet("My team said ""we need clarity."" I heard ""you're failing us."" 😶"),
                Tweet("We kept re-explaining priorities in every standup. Same confusion, new day."),
                Tweet("We built a shared Artemis mission board: one truth, live updates, zero guessing."),
                Tweet("Meetings got shorter. Tension dropped. Momentum came back fast. 🚀"),
                Tweet("Team leads: what creates more drag for you—unclear priorities or unclear ownership?"),
            ],
            **common,
        ),
        ThreadBundle(
            thread_number=5,
            tweets=[
                Tweet("I used to panic every Sunday night. No plan felt real. 😬"),
                Tweet("I'd write goals, then spend Monday reacting to everyone else's emergencies."),
                Tweet("Now Artemis prebuilds my week by impact, urgency, and energy level."),
                Tweet("I still work hard. I just don't feel hunted anymore. That shift is everything. 💎"),
                Tweet("Sunday check: are you starting tomorrow with intention or survival mode?"),
            ],
            **common,
        ),
    ]


def render_markdown(threads: list[ThreadBundle]) -> str:
    lines: list[str] = ["# ClearGlassInc Artemis Threads Pack", ""]
    for thread in threads:
        lines.append(f"## Thread {thread.thread_number}")
        lines.append("")
        lines.append(f"- App: {thread.app_name}")
        lines.append(f"- Category: {thread.app_category}")
        lines.append(f"- Audience: {thread.audience}")
        lines.append(f"- Emotional benefit: {thread.emotional_benefit}")
        lines.append("- Pain points: " + ", ".join(thread.pain_points))
        lines.append("")
        for idx, tweet in enumerate(thread.tweets, start=1):
            lines.append(f"{idx}. {tweet.text}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_site_page(threads: list[ThreadBundle]) -> str:
    cards = []
    for thread in threads:
        tweets = "\n".join(
            f'<li><span class="tweet-index">{i}.</span> {tweet.text}</li>'
            for i, tweet in enumerate(thread.tweets, start=1)
        )
        cards.append(
            f"""
      <article class=\"thread-card\">
        <h2>Thread {thread.thread_number}</h2>
        <p class=\"meta\">{thread.app_name} · {thread.app_category} · {thread.emotional_benefit}</p>
        <ul>{tweets}</ul>
      </article>
"""
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>ClearGlassInc Artemis Threads Kit</title>
  <link rel=\"stylesheet\" href=\"/assets/css/glass.css\">
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 0; background: #f7f8fa; color: #0c0e12; }}
    nav.site-nav {{ position: sticky; top: 0; z-index: 200; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(1rem,4vw,3rem); height: 64px; background: rgba(8,11,18,.88); backdrop-filter: blur(24px); border-bottom: 1px solid #1e2d40; }}
    nav.site-nav .brand {{ display: flex; align-items: center; gap: 10px; text-decoration: none; color: #f3f5f9; font-weight: 700; font-size: 15px; }}
    nav.site-nav .links {{ display: flex; gap: 4px; flex-wrap: wrap; }}
    nav.site-nav .links a {{ text-decoration: none; color: rgba(243,245,249,.7); font-size: 13px; font-weight: 600; padding: 7px 12px; border-radius: 999px; transition: color .2s, background .2s; }}
    nav.site-nav .links a:hover {{ color: #fff; background: rgba(255,255,255,.06); }}
    nav.site-nav .links a.active {{ color: #38bdf8; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 48px 20px 64px; }}
    h1 {{ font-size: clamp(2rem, 5vw, 3rem); margin-bottom: 10px; }}
    .sub {{ color: #cbd5e1; margin-bottom: 36px; line-height: 1.6; }}
    .grid {{ display: grid; gap: 16px; }}
    .thread-card {{ border: 1px solid #243043; border-radius: 16px; padding: 20px; background: #101827; }}
    .thread-card h2 {{ margin: 0 0 8px; }}
    .meta {{ font-size: .92rem; color: #93c5fd; margin-bottom: 14px; }}
    ul {{ margin: 0; padding-left: 0; list-style: none; display: grid; gap: 10px; }}
    li {{ line-height: 1.55; color: #e5e7eb; }}
    .tweet-index {{ color: #38bdf8; font-weight: 700; margin-right: 6px; }}
    a {{ color: #93c5fd; }}
  </style>
</head>
<body>
  <nav class=\"site-nav\">
    <a href=\"index.html\" class=\"brand\">ClearGlass <em style=\"font-style:normal;font-weight:300;color:rgba(243,245,249,.45)\">Inc.</em></a>
    <div class=\"links\">
      <a href=\"index.html\">Home</a>
      <a href=\"artemis.html\">Artemis VI</a>
      <a href=\"guardian.html\">Guardian</a>
      <a href=\"threads.html\" class=\"active\">Threads Kit</a>
    </div>
  </nav>
  <main>
    <h1>ClearGlassInc Artemis Threads Kit</h1>
    <p class=\"sub\">Five copy-ready, emotionally driven Threads sequences generated by the Artemis Growth Bot. Use, remix, and post as needed.</p>
    <div class=\"grid\">{''.join(cards)}
    </div>
  </main>
</body>
</html>
"""


def write_outputs(app_name: str = "ClearGlassInc Artemis") -> GrowthRun:
    run = GrowthRun(
        run_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        app_name=app_name,
        total_threads=5,
        output_dir=str(OUTPUT_DIR.relative_to(ROOT)),
        site_page=str(SITE_PAGE.relative_to(ROOT)),
    )
    threads = build_threads(app_name)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    THREADS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "run": asdict(run),
        "threads": [
            {
                **{k: v for k, v in asdict(thread).items() if k != "tweets"},
                "tweets": [asdict(tweet) for tweet in thread.tweets],
            }
            for thread in threads
        ],
    }

    THREADS_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    THREADS_MD.write_text(render_markdown(threads), encoding="utf-8")
    stamp = run.run_utc.replace("+00:00", "Z").replace(":", "")
    (THREADS_ARCHIVE_DIR / f"{stamp}.md").write_text(render_markdown(threads), encoding="utf-8")
    SITE_PAGE.write_text(render_site_page(threads), encoding="utf-8")

    return run


if __name__ == "__main__":
    result = write_outputs()
    print(f"Artemis Growth Bot complete for {result.app_name}")
    print(f"Updated: {result.site_page}")
