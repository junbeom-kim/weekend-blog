# 이번 주말 어디

공공데이터(TourAPI)로 매주 "이번 주말 행사" 글을 자동으로 쓰고 발행하는 개인 블로그.

## 구조

```
config.py                  사이트 이름, 대상 지역, 글당 행사 수, 모델 (여기만 고치면 됨)
scripts/
  common.py                주말 날짜 계산 등 공용 함수
  fetch_events.py    1단계  TourAPI searchFestival2 호출 -> data/YYYYMMDD.json
  write_post.py      2단계  행사 선별(pick_events) -> 프롬프트 조립 -> Claude API -> posts/YYYY-MM-DD.md
  build_site.py      3단계  posts/*.md -> site/ (HTML, sitemap.xml)
prompts/weekly_post.md     글쓰기 규칙. 글 품질은 대부분 여기서 결정됨
templates/                 HTML 템플릿과 CSS
.github/workflows/weekly.yml  매주 목요일 19:47(KST) 1~3단계 실행 후 GitHub Pages 배포
```

흐름: fetch_events -> (data json) -> write_post -> (post md) -> build_site -> (site html) -> 배포

fetch_events.normalize() 가 만드는 파생값(ends_this_weekend, weekend_only, starts_this_weekend, duration_days)이 이 블로그의 핵심이다. 단순 목록이 아니라 "이번 주말이 마지막", "하루만"이라는 해석을 붙이는 근거가 된다.

## 처음 설정

1. 공공데이터포털에서 "한국관광공사_국문 관광정보 서비스_GW" 활용신청, 일반 인증키(Decoding) 복사
2. Anthropic Console에서 API 키 발급
3. GitHub에 저장소 만들고 이 폴더 push
4. 저장소 Settings > Secrets and variables > Actions 에 TOURAPI_SERVICE_KEY, ANTHROPIC_API_KEY 등록
5. Settings > Pages > Source 를 "GitHub Actions" 로 지정
6. config.py 의 base_url 을 실제 주소로 수정
7. Actions 탭 > weekly-post > Run workflow 로 첫 실행

## 로컬 실행

Python 3.10 이상이 필요하다 (workflow 는 3.12). macOS 기본 python3(3.9)로는 실행되지 않는다.

```
pip install -r requirements.txt
export TOURAPI_SERVICE_KEY=...
export ANTHROPIC_API_KEY=...
python -m scripts.fetch_events
python -m scripts.write_post --dry-run   # 프롬프트만 확인
python -m scripts.write_post
python -m scripts.build_site
open site/index.html
```

## 참고

- data/20261031.json, posts/2026-10-31.md 는 샘플이다. 웹 검색으로 확인한 실제 일정을 TourAPI 형식으로 옮긴 것이라, 실제 API로 돌리면 행사 구성이 달라진다.
- 개발계정은 일일 호출 한도가 있다(보통 1,000건). 주 1회 실행이면 충분하다.
- 처음 몇 주는 자동 발행 대신 글을 확인하고 프롬프트를 다듬는 걸 권장. workflow 에서 deploy 잡을 빼고 posts 만 커밋하게 바꾸면 검수 모드가 된다.
