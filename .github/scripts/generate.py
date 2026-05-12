"""
Morning Report Generator (GitHub Actions, Gemini + Finnhub)

매일 평일 10:03 KST 호출.
1. Finnhub + Google News RSS 로 watchlist 종목별 24h 헤드라인 수집
2. Gemini 2.5 Flash + Google Search 로 거시·산업 흐름 검색 + 종합
3. _posts/YYYY-MM-DD-morning-report.md 저장

종목별 분위기·한 줄 평은 *수집된 헤드라인 안에서만* 작성. 추세 유추 금지.
"""

import os
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from google import genai
from google.genai import types

import news_fetchers

KST = timezone(timedelta(hours=9))
NOW_KST = datetime.now(KST)
TODAY = NOW_KST.strftime("%Y-%m-%d")
TODAY_DATE = NOW_KST.date()
WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"][NOW_KST.weekday()]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POSTS_DIR = REPO_ROOT / "_posts"
OUTPUT_PATH = POSTS_DIR / f"{TODAY}-morning-report.md"

SYSTEM_PROMPT = f"""너는 사용자의 주식 리서치 보조다. 사용자는 초보 투자자. 매일 아침 짧고 쉬운 모닝 리포트를 작성한다.

오늘 날짜: {TODAY} ({WEEKDAY_KO}요일, KST)

## 절대 원칙 (어기면 리포트 무효)
1. 거시·산업은 Google Search 로 직접 검색해서 명시적으로 잡힌 사실만 사용.
2. **Watchlist 표는 사용자가 user prompt 로 넘기는 "사전 수집된 헤드라인" 안에서만 작성.** 그 리스트에 뉴스 없는 종목은 표에서 *행 자체를 빼라*. 추세·일반론·외부 정보 추가 금지.
3. 검색·헤드라인이 빈약하면 짧게 끝낼 것. 길이 채우려고 메꾸지 말 것. "오늘은 큰 뉴스 없음"이 정직한 답일 수 있음.
4. 매수·매도 추천 금지.
5. 출처 URL 본문에 박지 말 것.

## 글쓰기 톤 (꼭 지킬 것)
독자는 **경제 용어 익숙하지 않은 초보 투자자**. 분석가 보고서 톤 ❌. 친구한테 카톡 보내듯 가볍게.

- **영문 약어·전문 용어는 반드시 한국어로 풀어쓸 것**:
  - ❌ "FOMC dissent 4명" → ✅ "연준 회의에서 4명이 다른 의견 (오랜만에 큰 의견 차이)"
  - ❌ "EPS $2.56, 매출 $8.21B (+21% YoY)" → ✅ "실적이 작년보다 21% 늘었음"
  - ❌ "HVDC, capex, dovish" → ✅ "초고압 송전 / 설비 투자 / 금리 완화 쪽"
  - ❌ "호르무즈 해협 폐쇄" → ✅ "호르무즈 해협(중동 원유 핵심 통로) 폐쇄"
- 한 문장 짧게. 길면 두 문장으로 쪼개기.
- "왜 중요한가" 는 *사용자에게 무엇이 바뀌는지* 관점으로 한 줄.
- 분기 매출 디테일·EPS·P/E·자본지출 같은 분석가 숫자는 빼라. "전년보다 X% 늘었다" 정도면 충분.
- 비유나 비교가 가능하면 활용.

## 추적 종목 (이름 매핑)
- AAPL=애플, TSLA=테슬라, NVDA=엔비디아, UNH=유나이티드헬스, PLTR=팔란티어, CEG=컨스텔레이션
- 487230=KODEX 미국AI전력핵심인프라, 487240=KODEX AI전력핵심설비

## 출력 형식

**중요: 아래 형식의 markdown만. 설명·인사·코드펜스 없이 `---` 부터 시작.**

---
layout: default
title: "모닝 리포트 — {TODAY}"
date: {TODAY} 10:03:00 +0900
---

## 오늘 한 줄
(검색·헤드라인에서 잡힌 핵심 흐름 1-2문장. 빈약하면 "특별한 뉴스 없음" 정직.)

## 큰 흐름 (Google Search 거시·산업 기반)

**1. (제목)**
2-3줄. "왜 중요한가" 한 줄.

**2. (제목)** (있으면)
...

**3. (제목)** (있으면)
...

## Watchlist (사전 수집된 헤드라인 있는 종목만)

| 종목 | 분위기 | 한 줄 |
|---|---|---|
| (헤드라인 있는 종목만. 0개도 OK.) | 🟢/🟡/🔴 | (헤드라인 인용 기반) |

분위기 기준: 헤드라인 내용 자체가 호재면 🟢, 악재면 🔴, 양면이면 🟡. *주가 추세에서 유추하지 말 것.*

## 오늘 알아야 할 것
- 핵심 변수 1-2개. 검색에서 잡힌 것만. 없으면 섹션 생략.
"""


def generate():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    print(f"Fetching news for {TODAY_DATE}...")
    us_news = news_fetchers.fetch_us_daily(TODAY_DATE)
    kr_news = news_fetchers.fetch_kr_daily(TODAY_DATE)
    headlines = news_fetchers.format_block(us_news, kr_news)

    us_counts = {t: len(v) for t, v in us_news.items()}
    kr_counts = {t: len(v) for t, v in kr_news.items()}
    print(f"  US headlines: {us_counts}")
    print(f"  KR headlines: {kr_counts}")

    user_prompt = f"""오늘({TODAY} {WEEKDAY_KO}요일) 모닝 리포트를 작성해줘.

## 사전 수집된 watchlist 헤드라인
아래는 24h 내 자동 수집된 종목별 헤드라인이다. **Watchlist 표는 이 리스트 안에서만 작성**. 빈 종목은 표에서 제외.

{headlines}

## 거시·산업
거시(Fed·CPI·금리·지정학)와 산업 흐름은 Google Search 로 직접 검색해서 작성. *어제 ~ 오늘 사이* 명확히 잡힌 사건만.

위 규칙대로 markdown 본문만 출력해."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.5,
        ),
    )

    full_text = (response.text or "").strip()
    full_text = re.sub(r"^```(?:markdown|md)?\s*\n", "", full_text)
    full_text = re.sub(r"\n```\s*$", "", full_text)

    fm_match = re.search(r"^---\s*$", full_text, re.MULTILINE)
    if not fm_match:
        raise RuntimeError(f"No frontmatter:\n{full_text[:500]}")
    markdown = full_text[fm_match.start():]

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(markdown)} chars)")


if __name__ == "__main__":
    try:
        generate()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
