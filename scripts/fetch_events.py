"""1단계: TourAPI(searchFestival2)로 이번 주말에 열리는 행사를 수집해 data/YYYYMMDD.json 으로 저장.

실행 예
  python -m scripts.fetch_events            # 다가오는 주말
  python -m scripts.fetch_events --date 2026-10-31

환경변수 TOURAPI_SERVICE_KEY 필요 (공공데이터포털 '한국관광공사_국문 관광정보 서비스_GW' 인증키, Decoding 키)
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from scripts.common import parse_ymd, upcoming_weekend, ymd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def call_festival_api(service_key: str, start: date, end: date, area_code: str | None, page: int = 1) -> list[dict]:
    """searchFestival2: [eventStartDate, eventEndDate] 기간과 겹치는 행사(진행 중 포함)를 돌려준다."""
    params = {
        "serviceKey": service_key,
        "MobileOS": "ETC",
        "MobileApp": "weekend-blog",
        "_type": "json",
        "numOfRows": 100,
        "pageNo": page,
        "arrange": "Q",  # 대표이미지 있는 것 우선, 수정일순
        "eventStartDate": ymd(start),
        "eventEndDate": ymd(end),
    }
    if area_code:
        params["lDongRegnCd"] = area_code
    r = requests.get(f"{config.TOURAPI_BASE}/searchFestival2", params=params, timeout=30)
    # raise_for_status() 메시지에는 인증키가 든 URL이 찍히므로 직접 검사한다
    if r.status_code != 200:
        sys.exit(f"TourAPI HTTP {r.status_code}: {r.text[:300]}")
    try:
        body = r.json()["response"]["body"]
    except (ValueError, KeyError):
        # 인증키 오류, 호출 한도 초과 등은 200 + XML 로 오는 경우가 많다
        sys.exit(f"TourAPI 응답을 해석할 수 없습니다 (인증키/호출 한도 확인): {r.text[:300]}")
    items = body.get("items") or {}
    if not items:
        return []
    item = items["item"]
    return item if isinstance(item, list) else [item]


def overlaps_weekend(ev: dict, sat: date, sun: date) -> bool:
    try:
        s, e = parse_ymd(ev["eventstartdate"]), parse_ymd(ev["eventenddate"])
    except (KeyError, ValueError):
        return False
    return s <= sun and e >= sat


def normalize(ev: dict, region_name: str, sat: date, sun: date) -> dict:
    """글쓰기 단계에서 쓰기 좋은 형태로 필드 정리 + 해석용 파생값 추가"""
    s, e = parse_ymd(ev["eventstartdate"]), parse_ymd(ev["eventenddate"])
    return {
        "contentid": ev.get("contentid"),
        "title": ev.get("title", "").strip(),
        "region": region_name,
        "addr": (ev.get("addr1", "") + " " + ev.get("addr2", "")).strip(),
        "start": s.isoformat(),
        "end": e.isoformat(),
        "tel": ev.get("tel", ""),
        "image": ev.get("firstimage", ""),
        "mapx": ev.get("mapx"),
        "mapy": ev.get("mapy"),
        # 파생값: 해석 문장을 쓸 때 근거가 되는 사실들
        "ends_this_weekend": e <= sun,          # 이번 주말이 마지막
        "starts_this_weekend": s >= sat,        # 이번 주말 개막
        "weekend_only": s >= sat and e <= sun,  # 이번 주말에만
        "duration_days": (e - s).days + 1,
    }


def collect(service_key: str, sat: date, sun: date) -> list[dict]:
    events: dict[str, dict] = {}
    targets = list(config.REGIONS.items())
    if config.INCLUDE_NATIONWIDE_PICKS:
        targets.append((None, "전국"))

    for code, name in targets:
        page = 1
        while True:
            items = call_festival_api(service_key, sat, sun, code, page)
            for ev in items:
                if not overlaps_weekend(ev, sat, sun):
                    continue
                cid = ev.get("contentid")
                if cid in events:
                    continue
                region = name if code else _area_name_from_addr(ev.get("addr1", ""))
                events[cid] = normalize(ev, region, sat, sun) | {"metro": bool(code)}
            if len(items) < 100:
                break
            page += 1
    return list(events.values())


def _area_name_from_addr(addr: str) -> str:
    return addr.split(" ")[0] if addr else "기타"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="기준 토요일 (YYYY-MM-DD). 생략하면 다가오는 주말")
    args = ap.parse_args()

    key = os.environ.get("TOURAPI_SERVICE_KEY")
    if not key:
        sys.exit("TOURAPI_SERVICE_KEY 환경변수가 없습니다.")

    sat, sun = upcoming_weekend(date.fromisoformat(args.date) if args.date else None)
    events = collect(key, sat, sun)

    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / f"{ymd(sat)}.json"
    out.write_text(
        json.dumps({"saturday": sat.isoformat(), "sunday": sun.isoformat(), "source": "TourAPI searchFestival2", "events": events},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(events)}건 저장: {out}")


if __name__ == "__main__":
    main()
