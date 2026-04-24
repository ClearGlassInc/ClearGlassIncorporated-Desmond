from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "marketing" / "output"
THREADS_JSON = OUTPUT_DIR / "threads_latest.json"
THREADS_MD = OUTPUT_DIR / "threads_latest.md"
THREADS_JS = OUTPUT_DIR / "threads_data.js"
THREADS_ARCHIVE_DIR = OUTPUT_DIR / "threads_archive"
SITE_PAGE = ROOT / "threads.html"


@dataclass(frozen=True)
class Tweet:
    text: str


@dataclass(frozen=True)
class ThreadMeta:
    thread_number: int
    app_name: str
    app_category: str
    audience: str
    emotional_benefit: str
    pain_points: list[str]


@dataclass(frozen=True)
class ThreadBundle:
    meta: ThreadMeta
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
        "app_category": "AI-driven productivity",
        "audience": "founders, operators, and high-output teams",
        "emotional_benefit": "deep control under high-stakes chaos",
        "pain_points": [
            "task overload with real-world consequences",
            "context switching fatigue in multi-stakeholder environments",
            "forgetting high-impact follow-ups that cost momentum",
        ],
    }

    return [
        ThreadBundle(
            meta=ThreadMeta(thread_number=1, **common),
            tweets=[
                Tweet("I almost missed the one message that could've changed my week. 😵‍💫"),
                Tweet("I had 17 tabs open, 42 unread pings, and zero idea what actually mattered. 📉"),
                Tweet("Then I ran my day through ClearGlassInc Artemis. It flagged one convo as high-stakes in 8 seconds."),
                Tweet("That single reply turned into a signed deal before lunch. Relief hit hard. ⚡"),
                Tweet("Be honest: how often does noise hide your biggest opportunity? 👇"),
            ],
        ),
        ThreadBundle(
            meta=ThreadMeta(thread_number=2, **common),
            tweets=[
                Tweet("I looked productive. I was actually drowning. 🫠"),
                Tweet("Color-coded calendar. Fancy to-do app. Still ended each day feeling behind and guilty."),
                Tweet("What changed? Artemis showed me where my time leaked, not where it looked busy."),
                Tweet("Two weeks later: fewer tasks, better output, calmer brain. That's the part no one tells you. 🧠"),
                Tweet("Are you optimizing for busy… or for peace + results?"),
            ],
        ),
        ThreadBundle(
            meta=ThreadMeta(thread_number=3, **common),
            tweets=[
                Tweet("The worst part of burnout? You don't notice it until you snap. 🔥"),
                Tweet("I stopped sleeping well. Started forgetting small promises. Confidence dropped quietly."),
                Tweet("Artemis started surfacing promise-risk moments before they became trust damage."),
                Tweet("Catching those early gave me my reputation back. And honestly, myself back too. 🙏"),
                Tweet("Who's felt their credibility slip from tiny misses, not big failures?"),
            ],
        ),
        ThreadBundle(
            meta=ThreadMeta(thread_number=4, **common),
            tweets=[
                Tweet("My team said 'we need clarity.' I heard 'you're failing us.' 😶"),
                Tweet("We kept re-explaining priorities in every standup. Same confusion, new day."),
                Tweet("We built a shared Artemis mission board: one truth, live updates, zero guessing."),
                Tweet("Meetings got shorter. Tension dropped. Momentum came back fast. 🚀"),
                Tweet("Team leads: what creates more drag for you—unclear priorities or unclear ownership?"),
            ],
        ),
        ThreadBundle(
            meta=ThreadMeta(thread_number=5, **common),
            tweets=[
                Tweet("I used to panic every Sunday night. No plan felt real. 😬"),
                Tweet("I'd write goals, then spend Monday reacting to everyone else's emergencies."),
                Tweet("Now Artemis prebuilds my week by impact, urgency, and energy level."),
                Tweet("I still work hard. I just don't feel hunted anymore. That shift is everything. 💎"),
                Tweet("Sunday check: are you starting tomorrow with intention or survival mode?"),
            ],
        ),
    ]


def render_markdown(threads: list[ThreadBundle]) -> str:
    lines = ["# ClearGlassInc Artemis Threads Pack", ""]
    for bundle in threads:
        m = bundle.meta
        lines.extend(
            [
                f"## Thread {m.thread_number}",
                "",
                f"- App: {m.app_name}",
                f"- Category: {m.app_category}",
                f"- Audience: {m.audience}",
                f"- Emotional benefit: {m.emotional_benefit}",
                "- Pain points: " + ", ".join(m.pain_points),
                "",
            ]
        )
        for idx, tweet in enumerate(bundle.tweets, start=1):
            lines.append(f"{idx}. {tweet.text}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_js_data(threads: list[ThreadBundle], run: GrowthRun) -> str:
    payload = {
        "version": "2026.q2",
        "run": asdict(run),
        "threads": [
            {
                **asdict(bundle.meta),
                "tweets": [asdict(tweet) for tweet in bundle.tweets],
            }
            for bundle in threads
        ],
    }
    return "window.ART_THREADS_DATA = " + json.dumps(payload, indent=2) + ";\n"


def render_site_page_html() -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>ClearGlassInc Artemis Threads Kit</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\" />
  <style>{render_css()}</style>
</head>
<body>
  <div class=\"background-aura\"></div>
  <div id=\"cursorGlow\" class=\"cursor-glow\"></div>
  <header class=\"topbar\">
    <div class=\"topbar-inner\">
      <div class=\"brand\">ClearGlassInc Artemis</div>
      <a class=\"home-link\" href=\"index.html\">← Home</a>
    </div>
  </header>
  <main class=\"layout\">
    <section class=\"hero reveal\">
      <p class=\"eyebrow\">Threads Publishing System</p>
      <h1>Emotion-first Thread Gallery</h1>
      <p class=\"sub\">Copy-ready sequences with interaction controls, export actions, and motion-driven storytelling.</p>
      <div class=\"meta-pill\" id=\"runMeta\">Loading latest run…</div>
    </section>

    <section class=\"controls reveal\">
      <button id=\"prevBtn\" class=\"btn\">← Prev</button>
      <span id=\"counter\" class=\"counter\">1 / 5</span>
      <button id=\"nextBtn\" class=\"btn\">Next →</button>
      <button id=\"shuffleBtn\" class=\"btn accent\">⚡ Shuffle</button>
      <button id=\"copyAllBtn\" class=\"btn\">Copy all</button>
      <button id=\"downloadBtn\" class=\"btn\">Download JSON</button>
    </section>

    <section id=\"threadGrid\" class=\"thread-grid\"></section>
  </main>

  <script src=\"marketing/output/threads_data.js\"></script>
  <script>{render_js_inline()}</script>
</body>
</html>
"""


def render_css() -> str:
    return """
:root {
  --bg: #060911;
  --bg-soft: #0f172a;
  --panel: rgba(15, 23, 42, 0.86);
  --text: #f8fafc;
  --muted: #cbd5e1;
  --line: rgba(148, 163, 184, 0.3);
  --accent: #38bdf8;
  --accent-2: #a78bfa;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: 'Inter', system-ui, sans-serif;
  background: radial-gradient(circle at 10% 10%, #0f1f38, var(--bg));
  color: var(--text);
  min-height: 100vh;
}
.background-aura {
  position: fixed;
  inset: -20vh;
  background: conic-gradient(from 0deg at 50% 50%, rgba(56,189,248,.24), transparent, rgba(167,139,250,.2), transparent, rgba(56,189,248,.24));
  filter: blur(60px);
  animation: spin 28s linear infinite;
  z-index: -2;
}
@keyframes spin { to { transform: rotate(360deg); } }
.cursor-glow {
  position: fixed;
  width: 30px;
  height: 30px;
  pointer-events: none;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(56,189,248,.8), transparent 70%);
  transform: translate(-50%, -50%);
  mix-blend-mode: screen;
  z-index: 100;
}
.topbar {
  position: sticky;
  top: 0;
  backdrop-filter: blur(10px);
  background: rgba(6, 9, 17, .75);
  border-bottom: 1px solid var(--line);
  z-index: 50;
}
.topbar-inner, .layout { width: min(1120px, 92vw); margin: 0 auto; }
.topbar-inner { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; }
.brand { font-weight: 700; letter-spacing: .02em; }
.home-link { color: var(--muted); text-decoration: none; }
.layout { padding: 36px 0 60px; }
.hero h1 { margin: 8px 0 10px; font-size: clamp(2rem, 4.5vw, 3.6rem); }
.eyebrow { color: var(--accent); text-transform: uppercase; letter-spacing: .1em; font-size: .75rem; }
.sub { color: var(--muted); max-width: 760px; line-height: 1.7; }
.meta-pill { margin-top: 18px; display: inline-block; padding: 8px 14px; border-radius: 999px; border: 1px solid var(--line); background: rgba(15,23,42,.7); color: var(--muted); }
.controls { margin: 28px 0 18px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.btn { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: 12px; padding: 10px 14px; cursor: pointer; }
.btn:hover { transform: translateY(-1px); border-color: rgba(56,189,248,.6); }
.btn.accent { background: linear-gradient(120deg, rgba(56,189,248,.2), rgba(167,139,250,.24)); }
.counter { color: var(--muted); font-weight: 600; }
.thread-grid { display: grid; gap: 14px; }
.thread-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--panel);
  padding: 18px;
  transition: transform .28s ease, border-color .28s ease, box-shadow .28s ease;
}
.thread-card.active { border-color: rgba(56,189,248,.8); box-shadow: 0 14px 40px rgba(56,189,248,.12); }
.thread-card:hover { transform: translateY(-2px); }
.thread-card h2 { margin: 0 0 10px; font-size: 1.1rem; }
.thread-meta { color: var(--muted); font-size: .9rem; margin-bottom: 10px; }
.thread-card ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.thread-card li { line-height: 1.55; color: #e2e8f0; }
.tweet-index { color: var(--accent); font-weight: 700; margin-right: 6px; }
.reveal { opacity: 0; transform: translateY(16px); transition: opacity .6s ease, transform .6s ease; }
.reveal.visible { opacity: 1; transform: translateY(0); }
@media (max-width: 720px) { .controls { gap: 8px; } .btn { width: calc(50% - 4px); } }
"""


def render_js_inline() -> str:
    return """
(() => {
  const data = window.ART_THREADS_DATA;
  const grid = document.getElementById('threadGrid');
  const counter = document.getElementById('counter');
  const runMeta = document.getElementById('runMeta');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const shuffleBtn = document.getElementById('shuffleBtn');
  const copyAllBtn = document.getElementById('copyAllBtn');
  const downloadBtn = document.getElementById('downloadBtn');

  if (!data || !Array.isArray(data.threads)) {
    runMeta.textContent = 'Unable to load thread data.';
    return;
  }

  let active = 0;
  const threads = data.threads;

  function renderCards() {
    grid.innerHTML = threads.map((thread, idx) => {
      const tweets = thread.tweets.map((tweet, i) => `<li><span class=\"tweet-index\">${i + 1}.</span>${tweet.text}</li>`).join('');
      return `
        <article class=\"thread-card ${idx === active ? 'active' : ''}\" data-index=\"${idx}\">
          <h2>Thread ${thread.thread_number}</h2>
          <p class=\"thread-meta\">${thread.app_name} · ${thread.app_category} · ${thread.emotional_benefit}</p>
          <ul>${tweets}</ul>
        </article>
      `;
    }).join('');

    counter.textContent = `${active + 1} / ${threads.length}`;

    grid.querySelectorAll('.thread-card').forEach((card) => {
      card.addEventListener('click', () => {
        active = Number(card.dataset.index);
        renderCards();
      });
    });
  }

  function copyAllThreads() {
    const lines = [];
    for (const thread of threads) {
      lines.push(`Thread ${thread.thread_number}`);
      for (const [i, tweet] of thread.tweets.entries()) {
        lines.push(`${i + 1}. ${tweet.text}`);
      }
      lines.push('');
    }
    navigator.clipboard.writeText(lines.join('\\\\n')).then(() => {
      copyAllBtn.textContent = 'Copied ✓';
      setTimeout(() => (copyAllBtn.textContent = 'Copy all'), 1100);
    });
  }

  function downloadJson() {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'clearglassinc-artemis-threads.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  prevBtn.addEventListener('click', () => { active = (active - 1 + threads.length) % threads.length; renderCards(); });
  nextBtn.addEventListener('click', () => { active = (active + 1) % threads.length; renderCards(); });
  shuffleBtn.addEventListener('click', () => { active = Math.floor(Math.random() * threads.length); renderCards(); });
  copyAllBtn.addEventListener('click', copyAllThreads);
  downloadBtn.addEventListener('click', downloadJson);

  runMeta.textContent = `Run UTC: ${data.run.run_utc} · Threads: ${threads.length} · Version: ${data.version}`;
  renderCards();

  const cursor = document.getElementById('cursorGlow');
  if (window.matchMedia('(pointer:fine)').matches) {
    window.addEventListener('mousemove', (event) => {
      cursor.style.left = `${event.clientX}px`;
      cursor.style.top = `${event.clientY}px`;
    });
  } else {
    cursor.style.display = 'none';
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add('visible');
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach((node) => observer.observe(node));
})();
"""


def write_outputs(app_name: str = "ClearGlassInc Artemis") -> GrowthRun:
    threads = build_threads(app_name)
    run = GrowthRun(
        run_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        app_name=app_name,
        total_threads=len(threads),
        output_dir=str(OUTPUT_DIR.relative_to(ROOT)),
        site_page=str(SITE_PAGE.relative_to(ROOT)),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    THREADS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    json_payload = {
        "run": asdict(run),
        "threads": [
            {
                **asdict(bundle.meta),
                "tweets": [asdict(tweet) for tweet in bundle.tweets],
            }
            for bundle in threads
        ],
    }

    markdown = render_markdown(threads)
    THREADS_JSON.write_text(json.dumps(json_payload, indent=2) + "\n", encoding="utf-8")
    THREADS_MD.write_text(markdown, encoding="utf-8")
    THREADS_JS.write_text(render_js_data(threads, run), encoding="utf-8")

    stamp = run.run_utc.replace("+00:00", "Z").replace(":", "")
    (THREADS_ARCHIVE_DIR / f"{stamp}.md").write_text(markdown, encoding="utf-8")
    SITE_PAGE.write_text(render_site_page_html(), encoding="utf-8")

    return run


if __name__ == "__main__":
    result = write_outputs()
    print(f"Artemis Growth Bot complete for {result.app_name}")
    print(f"Updated: {result.site_page}")
