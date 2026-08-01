import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"


def published_posts() -> list[dict]:
    return [
        post
        for post in json.loads((BLOG / "posts.json").read_text(encoding="utf-8"))["posts"]
        if post.get("status", "published") == "published" and post.get("url")
    ]


def test_blog_artifacts_are_generated_from_real_posts() -> None:
    result = subprocess.run(
        ["python3", "tools/build_blog.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_hub_keeps_every_published_article_in_static_html() -> None:
    index = (BLOG / "index.html").read_text(encoding="utf-8")
    posts = published_posts()
    assert index.count("data-article-card") == len(posts)
    for post in posts:
        assert f'href="{post["url"]}"' in index
    assert 'class="cg-blog-mission"' in index
    assert "INACTIVE — PROVIDER REQUIRED" in index


def test_rss_and_json_feeds_match_the_post_index() -> None:
    posts = published_posts()
    rss_items = ET.parse(BLOG / "feed.xml").getroot().findall("./channel/item")
    json_items = json.loads((BLOG / "feed.json").read_text(encoding="utf-8"))["items"]
    assert len(rss_items) == len(posts)
    assert len(json_items) == len(posts)
    assert {item.findtext("guid") for item in rss_items} == {
        "https://www.clearglassinc.com" + post["url"] for post in posts
    }
    atom = ET.parse(BLOG / "atom.xml").getroot()
    assert len(atom.findall("{http://www.w3.org/2005/Atom}entry")) == len(posts)


def test_new_styles_and_script_are_mission_scoped() -> None:
    import re

    css = re.sub(r"/\*.*?\*/", "", (BLOG / "mission.css").read_text(encoding="utf-8"), flags=re.S)
    selectors = [part.strip() for block in css.split("}") for part in block.split("{")[:1]]
    assert selectors
    assert all(
        selector.startswith((".cg-blog-mission", "@"))
        for selector in selectors
        if selector and not selector.startswith(("to", "from"))
    )
    script = (BLOG / "mission.js").read_text(encoding="utf-8")
    assert "document.querySelector('.cg-blog-mission')" in script
    assert "if (!root) return" in script


def test_hub_exposes_accessible_modes_and_security_boundary() -> None:
    index = (BLOG / "index.html").read_text(encoding="utf-8")
    assert 'Content-Security-Policy' in index
    assert 'data-mission-page="hub"' in index
    assert "ARTEMIS FAWL // KNOWLEDGE LINK ESTABLISHED" in index
    for mode in ("briefing", "signals", "archive", "focus", "graph"):
        assert f'data-view="{mode}"' in index
    assert 'data-graph-rows' in index
    assert '<noscript>' in index


def test_client_rendering_avoids_unsafe_html_sinks() -> None:
    script = (BLOG / "mission.js").read_text(encoding="utf-8")
    assert ".innerHTML" not in script
    assert "replaceChildren" in script
    assert "safeParam" in script
