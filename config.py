"""블로그 전역 설정. 여기만 고치면 지역, 글 개수, 사이트 정보가 바뀝니다."""

SITE = {
    "title": "이번 주말 어디",
    "tagline": "공공데이터로 고르는 이번 주말 행사와 축제",
    "base_url": "https://junbeom-kim.github.io/weekend-blog",
    "author": "JB",
}

# TourAPI 지역코드 (KorService2 lDongRegnCd = 법정동 시도코드 기준). 필요하면 추가/삭제
# 11 서울, 28 인천, 41 경기, 26 부산, 31 울산, 44 충남 ...
# 옛 areaCode(1, 2, 31 ...)는 KorService2 에서 결과가 0건이다.
REGIONS = {
    "11": "서울",
    "28": "인천",
    "41": "경기",
}

# 수도권 외 지역에서 "멀어도 가볼 만한" 행사를 몇 개까지 넣을지
INCLUDE_NATIONWIDE_PICKS = 3

# 글 하나에 담을 최대 행사 수
MAX_EVENTS_PER_POST = 12

# 글쓰기에 사용할 Claude 모델
CLAUDE_MODEL = "claude-sonnet-5-5"

TOURAPI_BASE = "https://apis.data.go.kr/B551011/KorService2"
