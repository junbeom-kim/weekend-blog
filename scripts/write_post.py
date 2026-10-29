"""2단계: data/YYYYMMDD.json 을 읽어 Claude API로 블로그 글(마크다운)을 작성, posts/YYYY-MM-DD.md 로 저장.

실행 예
  python -m scripts.write_post --date 2026-10-31

환경변수 ANTHROPIC_API_KEY 필요
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from scripts.common import ko_date, upcoming_weekend, ymd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
POSTS_DIR = ROOT / "posts"
PROMPT_FILE = ROOT / "prompts" / "weekly_post.md"

FENCE_RE = re.compile(r"^```[\w-]*\n(.*?)\n```$", re.S)
FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def pick_events(events: list[dict]) -> list[dict]:
    """글에 넣을 행사 고르기. 수도권 우선, 그 안에서 '이번 주말이 마지막' > '이번 주말만' > '개막' 순."""
    def score(ev):
        return (
            ev["ends_this_weekend"] * 3
            + ev["weekend_only"] * 2
            + ev["starts_this_weekend"] * 1
            + (1 if ev.get("image") else 0) * 0.5
        )

    metro = sorted([e for e in events if e.get("metro")], key=score, reverse=True)
    others = sorted([e for e in events if not e.get("metro")], key=score, reverse=True)
    # 수도권 외 행사가 모자라면 남는 자리는 수도권으로 채운다
    n_others = min(config.INCLUDE_NATIONWIDE_PICKS, len(others))
    n_metro = config.MAX_EVENTS_PER_POST - n_others
    return metro[:n_metro] + others[:n_others]


def build_prompt(sat: date, sun: date, events: list[dict]) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    return (
        template.replace("{{SATURDAY}}", ko_date(sat))
        .replace("{{SUNDAY}}", ko_date(sun))
        .replace("{{EVENTS_JSON}}", json.dumps(events, ensure_ascii=False, indent=2))
    )


def call_claude(prompt: str) -> str:
    import anthropic  # 글쓰기 단계에서만 필요하므로 여기서 import

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )
    if msg.stop_reason != "end_turn":
        sys.exit(f"글이 완결되지 않았습니다 (stop_reason={msg.stop_reason}). 발행하지 않습니다.")
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def clean_post(text: str, sat: date) -> str:
    """Claude 출력 정리: 글 전체를 감싼 코드블록 제거, front matter 검사, date 는 토요일로 고정."""
    text = text.replace("\r\n", "\n").strip()
    m = FENCE_RE.match(text)
    if m:
        text = m.group(1).strip()
    m = FRONT_RE.match(text)
    if not m:
        raise ValueError("front matter(---)로 시작하지 않습니다")
    lines = [ln for ln in m.group(1).splitlines() if not ln.startswith("date:")]
    title_idx = next((i for i, ln in enumerate(lines) if ln.startswith("title:")), None)
    if title_idx is None:
        raise ValueError("front matter 에 title 이 없습니다")
    lines.insert(title_idx + 1, f"date: {sat.isoformat()}")
    return "---\n" + "\n".join(lines) + "\n---\n" + text[m.end():]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="기준 토요일 (YYYY-MM-DD)")
    ap.add_argument("--dry-run", action="store_true", help="API 호출 없이 프롬프트만 출력")
    args = ap.parse_args()

    sat, sun = upcoming_weekend(date.fromisoformat(args.date) if args.date else None)
    data = json.loads((DATA_DIR / f"{ymd(sat)}.json").read_text(encoding="utf-8"))
    events = pick_events(data["events"])
    if not events:
        sys.exit("이번 주말 행사 데이터가 없습니다.")

    prompt = build_prompt(sat, sun, events)
    if args.dry_run:
        print(prompt)
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY 환경변수가 없습니다.")

    raw = call_claude(prompt)
    try:
        body = clean_post(raw, sat)
    except ValueError as e:
        print(raw, file=sys.stderr)
        sys.exit(f"글 형식이 올바르지 않습니다: {e}. 발행하지 않습니다.")
    POSTS_DIR.mkdir(exist_ok=True)
    out = POSTS_DIR / f"{sat.isoformat()}.md"
    out.write_text(body + "\n", encoding="utf-8")
    print(f"글 저장: {out}")


if __name__ == "__main__":
    main()
