from __future__ import annotations

import argparse
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
class AppContext:
    app_name: str
    app_category: str
    audience: str
    emotional_benefit: str
    pain_points: list[str]


@dataclass(frozen=True)
class Tweet:
    text: str


@dataclass(frozen=True)
class ThreadBundle:
    thread_number: int
    tweets: list[Tweet]


@dataclass(frozen=True)
class GrowthRun:
    run_utc: str
    context: AppContext
    total_threads: int
    output_dir: str
    site_page: str


def default_context(app_name: str = "ClearGlassInc Artemis") -> AppContext:
    return AppContext(
        app_name=app_name,
        app_category="AI-driven productivity",
        audience="founders, operators, and high-output teams",
        emotional_benefit="deep control under high-stakes chaos",
        pain_points=[
            "task overload with real-world consequences",
            "context switching fatigue in multi-stakeholder environments",
            "forgetting high-impact follow-ups that cost momentum",
        ],
    )


def _fallback_pain_points(points: list[str]) -> tuple[str, str, str]:
    normalized = [p.strip() for p in points if p.strip()]
    while len(normalized) < 3:
        normalized.append(
            [
                "task overload and fragmented focus",
                "losing context across conversations",
                "missing high-impact follow-ups",
            ][len(normalized)]
        )
    return normalized[0], normalized[1], normalized[2]


def build_threads(context: AppContext) -> list[ThreadBundle]:
    p1, p2, p3 = _fallback_pain_points(context.pain_points)
    app = context.app_name
    aud = context.audience
    benefit = context.emotional_benefit

    threads_text = [
        [
            f"I almost dropped a key message this week, and it shook me. 😵‍💫",
            f"I was buried in {p1} and my brain went numb at the worst moment.",
            f"We ran everything through {app}, and one high-stakes thread surfaced instantly.",
            f"That single reply flipped panic into relief. Real {benefit}. ⚡",
            f"{aud}: when did noise almost cost you something important?",
        ],
        [
            "I looked organized from the outside. Inside? Complete chaos. 🫠",
            f"I kept bouncing through {p2}, pretending the stress was normal.",
            f"After using {app}, I finally saw what was signal vs. distraction.",
            "I finished the day with energy left, not guilt. That felt new. 🧠",
            "Do you optimize for looking busy, or actually feeling in control?",
        ],
        [
            "The scariest part of burnout is how quietly it sneaks in. 🔥",
            f"For me, it started with {p3} and tiny broken promises.",
            f"{app} started flagging risk moments before they turned into trust damage.",
            "I stopped apologizing for avoidable misses. Confidence came back. 🙏",
            "Who else has had small misses hit harder than one big failure?",
        ],
        [
            "My team said, ‘we need clarity.’ I heard, ‘you’re dropping the ball.’ 😶",
            f"We were stuck in {p1} and re-explaining priorities every day.",
            f"Then we shared one live board in {app}. Same truth, same priorities.",
            "Tension dropped fast. Execution got boring again (in a good way). 🚀",
            "Leads: what hurts more right now, unclear priorities or unclear ownership?",
        ],
        [
            "Sunday nights used to feel like a countdown clock. 😬",
            f"I’d plan hard, then Monday disappeared into {p2}.",
            f"Now {app} prebuilds my week around impact, urgency, and headspace.",
            f"I still work hard, but I don’t feel hunted. {benefit}. 💎",
            "Tomorrow check-in: starting with intention or pure survival mode?",
        ],
    ]

    return [
        ThreadBundle(thread_number=index + 1, tweets=[Tweet(text=tweet) for tweet in tweets])
        for index, tweets in enumerate(threads_text)
    ]


def render_markdown(context: AppContext, threads: list[ThreadBundle]) -> str:
    lines = [
        "# ClearGlassInc Artemis Threads Pack",
        "",
        f"- App: {context.app_name}",
        f"- Category: {context.app_category}",
        f"- Audience: {context.audience}",
        f"- Emotional benefit: {context.emotional_benefit}",
        "- Pain points: " + ", ".join(context.pain_points),
        "",
    ]
    for bundle in threads:
        lines.append(f"## Thread {bundle.thread_number}")
        lines.append("")
        for idx, tweet in enumerate(bundle.tweets, start=1):
            lines.append(f"{idx}. {tweet.text}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_js_data(run: GrowthRun, threads: list[ThreadBundle]) -> str:
    payload = {
        "version": "2026.q2",
        "run": asdict(run),
        "threads": [
            {
                "thread_number": bundle.thread_number,
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
  <title>ClearGlassInc Artemis · Threads Prompt Generator</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\" />
  <style>{render_css()}</style>
</head>
<body>
  <header class=\"topbar\">
    <div class=\"container\">
      <strong>ClearGlassInc Artemis · Threads Engine</strong>
      <a href=\"index.html\">← Home</a>
    </div>
  </header>

  <main class=\"container\">
    <section class=\"panel reveal\">
      <h1>2026 Threads Prompt Generator</h1>
      <p>Build 5 emotion-first Threads with one click. Designed for reply-heavy, conversational engagement.</p>
      <div id=\"runMeta\" class=\"pill\">Loading run metadata…</div>
    </section>

    <section class=\"panel reveal\">
      <h2>App Inputs</h2>
      <form id=\"contextForm\" class=\"form-grid\">
        <label>App name<input id=\"appName\" required /></label>
        <label>Category<input id=\"appCategory\" required /></label>
        <label>Audience<input id=\"audience\" required /></label>
        <label>Emotional benefit<input id=\"benefit\" required /></label>
        <label>Pain point 1<input id=\"pain1\" required /></label>
        <label>Pain point 2<input id=\"pain2\" required /></label>
        <label>Pain point 3<input id=\"pain3\" required /></label>
        <div class=\"actions\">
          <button type=\"submit\">Generate 5 Threads</button>
          <button id=\"copyAllBtn\" type=\"button\">Copy all</button>
          <button id=\"downloadBtn\" type=\"button\">Download JSON</button>
        </div>
      </form>
    </section>

    <section class=\"panel reveal\">
      <h2>Generated Threads</h2>
      <div id=\"threadGrid\" class=\"thread-grid\"></div>
    </section>
  </main>

  <script src=\"marketing/output/threads_data.js\"></script>
  <script>{render_js_inline()}</script>
</body>
</html>
"""


def render_css() -> str:
    return """
:root { --bg:#070b13; --panel:#111827; --line:#334155; --txt:#f8fafc; --muted:#cbd5e1; --acc:#38bdf8; }
* { box-sizing:border-box; }
body { margin:0; font-family:'Inter',system-ui,sans-serif; background:radial-gradient(circle at 10% 10%, #152640, var(--bg)); color:var(--txt); }
.topbar { position:sticky; top:0; background:rgba(7,11,19,.84); backdrop-filter:blur(8px); border-bottom:1px solid var(--line); }
.container { width:min(1040px,92vw); margin:0 auto; }
.topbar .container { display:flex; justify-content:space-between; padding:14px 0; }
.topbar a { color:var(--muted); text-decoration:none; }
.panel { margin:20px 0; background:rgba(17,24,39,.92); border:1px solid var(--line); border-radius:16px; padding:18px; }
.pill { margin-top:10px; color:var(--muted); font-size:.92rem; }
.form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
label { display:grid; gap:6px; color:var(--muted); font-size:.9rem; }
input { padding:10px; border-radius:10px; border:1px solid var(--line); background:#0b1220; color:var(--txt); }
.actions { grid-column:1/-1; display:flex; gap:10px; flex-wrap:wrap; }
button { border:1px solid var(--line); background:#0f172a; color:var(--txt); border-radius:10px; padding:10px 12px; cursor:pointer; }
button:hover { border-color:var(--acc); }
.thread-grid { display:grid; gap:12px; }
.thread-card { border:1px solid var(--line); border-radius:14px; background:#0f172a; padding:14px; }
.thread-card h3 { margin:0 0 10px; }
.thread-card ul { list-style:none; margin:0; padding:0; display:grid; gap:8px; }
.tweet-index { color:var(--acc); margin-right:6px; font-weight:700; }
.reveal { opacity:0; transform:translateY(16px); transition:all .5s ease; }
.reveal.visible { opacity:1; transform:translateY(0); }
@media (max-width: 760px) { .form-grid { grid-template-columns:1fr; } }
"""


def render_js_inline() -> str:
    return r"""
(() => {
  const data = window.ART_THREADS_DATA || {};
  const runMeta = document.getElementById('runMeta');
  const form = document.getElementById('contextForm');
  const grid = document.getElementById('threadGrid');
  const copyAllBtn = document.getElementById('copyAllBtn');
  const downloadBtn = document.getElementById('downloadBtn');

  const defaults = {
    app_name: data?.run?.context?.app_name || 'ClearGlassInc Artemis',
    app_category: data?.run?.context?.app_category || 'AI-driven productivity',
    audience: data?.run?.context?.audience || 'founders, operators, and high-output teams',
    emotional_benefit: data?.run?.context?.emotional_benefit || 'deep control under high-stakes chaos',
    pain_points: data?.run?.context?.pain_points || [
      'task overload with real-world consequences',
      'context switching fatigue in multi-stakeholder environments',
      'forgetting high-impact follow-ups that cost momentum'
    ]
  };

  const hooks = [
    'I almost dropped a key message this week, and it shook me. 😵‍💫',
    'I looked organized from the outside. Inside? Complete chaos. 🫠',
    'The scariest part of burnout is how quietly it sneaks in. 🔥',
    'My team said, “we need clarity.” I heard, “you’re dropping the ball.” 😶',
    'Sunday nights used to feel like a countdown clock. 😬'
  ];

  function buildThreads(ctx) {
    const [p1, p2, p3] = ctx.pain_points;
    const app = ctx.app_name;
    const aud = ctx.audience;
    const benefit = ctx.emotional_benefit;
    return [
      [hooks[0], `I was buried in ${p1} and my brain went numb at the worst moment.`, `We ran everything through ${app}, and one high-stakes thread surfaced instantly.`, `That single reply flipped panic into relief. Real ${benefit}. ⚡`, `${aud}: when did noise almost cost you something important?`],
      [hooks[1], `I kept bouncing through ${p2}, pretending the stress was normal.`, `After using ${app}, I finally saw what was signal vs. distraction.`, 'I finished the day with energy left, not guilt. That felt new. 🧠', 'Do you optimize for looking busy, or actually feeling in control?'],
      [hooks[2], `For me, it started with ${p3} and tiny broken promises.`, `${app} started flagging risk moments before they turned into trust damage.`, 'I stopped apologizing for avoidable misses. Confidence came back. 🙏', 'Who else has had small misses hit harder than one big failure?'],
      [hooks[3], `We were stuck in ${p1} and re-explaining priorities every day.`, `Then we shared one live board in ${app}. Same truth, same priorities.`, 'Tension dropped fast. Execution got boring again (in a good way). 🚀', 'Leads: what hurts more right now, unclear priorities or unclear ownership?'],
      [hooks[4], `I’d plan hard, then Monday disappeared into ${p2}.`, `${app} prebuilds my week around impact, urgency, and headspace.`, `I still work hard, but I don’t feel hunted. ${benefit}. 💎`, 'Tomorrow check-in: starting with intention or pure survival mode?']
    ];
  }

  function renderThreads(threads) {
    grid.innerHTML = threads.map((thread, idx) => `
      <article class="thread-card">
        <h3>Thread ${idx + 1}</h3>
        <ul>${thread.map((tweet, i) => `<li><span class="tweet-index">${i + 1}.</span>${tweet}</li>`).join('')}</ul>
      </article>
    `).join('');
  }

  function currentContext() {
    return {
      app_name: document.getElementById('appName').value.trim(),
      app_category: document.getElementById('appCategory').value.trim(),
      audience: document.getElementById('audience').value.trim(),
      emotional_benefit: document.getElementById('benefit').value.trim(),
      pain_points: [
        document.getElementById('pain1').value.trim(),
        document.getElementById('pain2').value.trim(),
        document.getElementById('pain3').value.trim()
      ]
    };
  }

  function fillDefaults() {
    document.getElementById('appName').value = defaults.app_name;
    document.getElementById('appCategory').value = defaults.app_category;
    document.getElementById('audience').value = defaults.audience;
    document.getElementById('benefit').value = defaults.emotional_benefit;
    document.getElementById('pain1').value = defaults.pain_points[0];
    document.getElementById('pain2').value = defaults.pain_points[1];
    document.getElementById('pain3').value = defaults.pain_points[2];
  }

  function copyAll() {
    const threads = buildThreads(currentContext());
    const text = threads.map((thread, idx) => `Thread ${idx + 1}\n` + thread.map((t, i) => `${i + 1}. ${t}`).join('\n')).join('\n\n');
    navigator.clipboard.writeText(text).then(() => {
      copyAllBtn.textContent = 'Copied ✓';
      setTimeout(() => (copyAllBtn.textContent = 'Copy all'), 1000);
    });
  }

  function downloadJson() {
    const payload = { context: currentContext(), threads: buildThreads(currentContext()) };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'threads-generator-output.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    renderThreads(buildThreads(currentContext()));
  });
  copyAllBtn.addEventListener('click', copyAll);
  downloadBtn.addEventListener('click', downloadJson);

  fillDefaults();
  renderThreads(buildThreads(defaults));
  runMeta.textContent = data?.run?.run_utc
    ? `Latest bot run: ${data.run.run_utc} UTC`
    : 'Local generator mode';

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add('visible');
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach((node) => observer.observe(node));
})();
"""


def write_outputs(context: AppContext | None = None) -> GrowthRun:
    resolved_context = context or default_context()
    threads = build_threads(resolved_context)
    run = GrowthRun(
        run_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        context=resolved_context,
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
                "thread_number": bundle.thread_number,
                "tweets": [asdict(tweet) for tweet in bundle.tweets],
            }
            for bundle in threads
        ],
    }

    markdown = render_markdown(resolved_context, threads)
    THREADS_JSON.write_text(json.dumps(json_payload, indent=2) + "\n", encoding="utf-8")
    THREADS_MD.write_text(markdown, encoding="utf-8")
    THREADS_JS.write_text(render_js_data(run, threads), encoding="utf-8")

    stamp = run.run_utc.replace("+00:00", "Z").replace(":", "")
    (THREADS_ARCHIVE_DIR / f"{stamp}.md").write_text(markdown, encoding="utf-8")
    SITE_PAGE.write_text(render_site_page_html(), encoding="utf-8")
    return run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Threads assets for ClearGlassInc Artemis")
    parser.add_argument("--app-name", default="ClearGlassInc Artemis")
    parser.add_argument("--category", default="AI-driven productivity")
    parser.add_argument("--audience", default="founders, operators, and high-output teams")
    parser.add_argument("--benefit", default="deep control under high-stakes chaos")
    parser.add_argument(
        "--pain-points",
        default="task overload with real-world consequences|context switching fatigue in multi-stakeholder environments|forgetting high-impact follow-ups that cost momentum",
        help="Pipe-delimited list of three pain points.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    context = AppContext(
        app_name=args.app_name,
        app_category=args.category,
        audience=args.audience,
        emotional_benefit=args.benefit,
        pain_points=[chunk.strip() for chunk in args.pain_points.split("|") if chunk.strip()],
    )
    result = write_outputs(context)
    print(f"Artemis Growth Bot complete for {result.context.app_name}")
    print(f"Updated: {result.site_page}")
