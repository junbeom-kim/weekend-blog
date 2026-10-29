"""3단계: posts/*.md 를 정적 HTML 사이트(site/)로 빌드.

실행 예
  python -m scripts.build_site
생성물: site/index.html, site/posts/YYYY-MM-DD.html, site/style.css, site/sitemap.xml
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from scripts.common import ko_date  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
OUT = ROOT / "site"
TEMPLATES = ROOT / "templates"


def parse_post(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip().strip('"')
                if v.startswith("[") and v.endswith("]"):
                    v = [t.strip().strip('"') for t in v[1:-1].split(",") if t.strip()]
                meta[k.strip()] = v
        body = m.group(2)
    try:
        d = date.fromisoformat(meta.get("date", path.stem))
    except ValueError:  # front matter 날짜가 이상하면 파일명(토요일)을 쓴다
        d = date.fromisoformat(path.stem)
    html = markdown.markdown(body, extensions=["extra"])
    return {
        "slug": path.stem,
        "title": meta.get("title", path.stem),
        "summary": meta.get("summary", ""),
        "tags": meta.get("tags", []),
        "date": d,
        "date_ko": ko_date(d),
        "html": html,
    }


def main():
    posts = sorted((parse_post(p) for p in POSTS_DIR.glob("*.md")), key=lambda p: p["date"], reverse=True)
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    shutil.copy(TEMPLATES / "style.css", OUT / "style.css")

    ctx = {"site": config.SITE}
    (OUT / "index.html").write_text(env.get_template("index.html").render(posts=posts, root=".", **ctx), encoding="utf-8")
    for p in posts:
        (OUT / "posts" / f"{p['slug']}.html").write_text(
            env.get_template("post.html").render(post=p, root="..", **ctx), encoding="utf-8"
        )

    base = config.SITE["base_url"].rstrip("/")
    urls = [f"{base}/"] + [f"{base}/posts/{p['slug']}.html" for p in posts]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"{len(posts)}개 글 빌드 완료: {OUT}")


if __name__ == "__main__":
    main()
