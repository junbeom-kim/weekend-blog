"""여러 스크립트에서 같이 쓰는 날짜 계산 함수."""
from datetime import date, timedelta


def upcoming_weekend(today: date | None = None) -> tuple[date, date]:
    """오늘 기준 다가오는 토요일과 일요일을 돌려준다. 토/일 당일이면 그 주말."""
    today = today or date.today()
    days_until_sat = (5 - today.weekday()) % 7
    if today.weekday() == 6:  # 일요일이면 오늘이 포함된 주말(어제 토요일)
        sat = today - timedelta(days=1)
    else:
        sat = today + timedelta(days=days_until_sat)
    return sat, sat + timedelta(days=1)


def parse_ymd(s: str) -> date:
    """TourAPI 날짜 문자열 '20261031' -> date"""
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def ymd(d: date) -> str:
    return d.strftime("%Y%m%d")


WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def ko_date(d: date) -> str:
    return f"{d.month}월 {d.day}일({WEEKDAY_KO[d.weekday()]})"
