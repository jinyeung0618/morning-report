"""
Monthly Summary Backfill (2020-01 ~ 2026-04)

- 최근 12개월 (Finnhub 무료 history 한도) → 거시·산업 + Watchlist 주요 이벤트
- 그 이전 → 거시·산업만 (회고성 종목 단신은 신뢰도 낮음)
"""

import os
import sys
import re
import time
import calendar
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from google import genai
from google.genai import types

import news_fetchers

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POSTS_DIR = REPO_ROOT / "_posts"

START_YEAR, START_MONTH = 2020, 1
END_YEAR, END_MONTH = 2026, 4

# Finnhub 무료 티어는 약 1년 history. 안전하게 11개월로 컷.
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()
FINNHUB_CUTOFF = TODAY - timedelta(days=330)


def make_system_prompt(year: int, month: int, include_stocks: bool) -> str:
    month_label = f"{year}년 {month}월"
    last_day = calendar.monthrange(year, month)[1]

    stocks_section = ""
    if include_stocks:
        stocks_section = """
## Watchlist 주요 이벤트 (사전 수집된 헤드라인 안에서만)
| 종목 | 분위기 | 그 달 주요 이벤트 |
|---|---|---|
| (헤드라인 있는 종목만 — 빈 종목은 빼라.) | 🟢/🟡/🔴 | (수집된 헤드라인 1-2개를 한 줄로 묶음) |

분위기 기준: 그 달 헤드라인 종합 결과. 헤드라인이 PR 류·중립이면 🟡, 호재 다수면 🟢, 악재 다수면 🔴.
"""
    else:
        stocks_section = """
## Watchlist
(이 시기 종목별 헤드라인은 자동 수집하지 않았다. 종목 섹션 생략.)
"""

    return f"""너는 사용자의 주식 리서치 보조다. **{month_label}** 한 달의 시장·산업 흐름을 회고하는 월간 요약을 작성한다.

## 절대 원칙 (어기면 무효)
1. 거시·산업은 Google Search 로 직접 검색해서 명시적으로 잡힌 사실만 사용. 추측·추세 유추 금지.
2. **시점 인지** — {month_label} *이후* 일어난 일은 절대 언급 금지.
3. 검색에서 큰 사건 못 찾으면 "특별한 사건 없음" 도 정직한 답.
{"4. **Watchlist 표는 user prompt 로 넘어오는 사전 수집 헤드라인 안에서만 작성.** 추가·유추 금지." if include_stocks else "4. Watchlist 섹션은 작성하지 않는다."}
5. 매수·매도 추천 금지. 수치는 꼭 필요한 1-2개만.
6. 평이한 한국어. URL 본문에 박지 말 것.

## 작업 절차

### Step 1 — 거시 검색
"{year} {month} Fed FOMC", "{year} {month} CPI", "{year} {month} stock market major events", "{year} {month} geopolitics", "{year}년 {month}월 코스피".

### Step 2 — 산업·테마 검색
"{year} {month} AI industry", "{year} {month} semiconductor", "{year} {month} data center power", "{year}년 {month}월 반도체".

### Step 3 — Markdown 출력

**중요: 아래 형식만. 설명·코드펜스 없이 `---` 부터 시작.**

---
layout: default
title: "월간 요약 — {month_label}"
date: {year}-{month:02d}-{last_day:02d} 18:00:00 +0900
type: monthly
---

## 이 달의 한 줄
(검색·헤드라인 핵심 1-2문장. 빈약하면 정직하게 짧게.)

## 거시 (Google Search)

**1. (제목)**
2-3줄. 왜 중요했나 한 줄.

**2. (제목)** (있으면)

## 산업·테마 (Google Search)

**1. (제목)**

**2. (제목)** (있으면)

{stocks_section}

## 다음 달로 이어진 이슈
- 1-2개. 그 달 끝 시점 미해결 변수. 없으면 섹션 생략.

## 길이·정직성
검색·헤드라인 부실하면 짧게 끝낼 것. 길이 채우려고 채우지 말 것.
"""


def month_iter(y1, m1, y2, m2):
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        yield y, m
        m += 1
        if m == 13:
            m = 1
            y += 1


def output_path(year: int, month: int) -> Path:
    last_day = calendar.monthrange(year, month)[1]
    return POSTS_DIR / f"{year}-{month:02d}-{last_day:02d}-monthly-summary.md"


def should_include_stocks(year: int, month: int) -> bool:
    """Finnhub 무료 history 한도 (~1년) 내인지."""
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return last_day >= FINNHUB_CUTOFF


def generate_month(client: genai.Client, year: int, month: int) -> bool:
    out = output_path(year, month)
    if out.exists():
        print(f"  SKIP exists: {out.name}")
        return False

    include_stocks = should_include_stocks(year, month)
    print(f"  include_stocks={include_stocks}")

    user_prompt_parts = [f"{year}년 {month}월 월간 요약을 작성해줘."]

    if include_stocks:
        us_news = news_fetchers.fetch_us_monthly(year, month)
        # 국내 ETF는 회고성 RSS 매칭 정확도 낮아서 미국만
        empty_kr = {t: [] for t in news_fetchers.KR_TICKERS}
        headlines = news_fetchers.format_block(us_news, empty_kr, include_kr=False)
        us_counts = {t: len(v) for t, v in us_news.items()}
        print(f"  US headlines: {us_counts}")

        user_prompt_parts.append(f"""
## 사전 수집된 종목별 헤드라인 ({year}년 {month}월)
**이 리스트 안에서만 Watchlist 표 작성**. 빈 종목 제외. 외부 정보 추가 금지.

{headlines}
""")

    user_prompt_parts.append("\n위 절차대로 markdown 본문만 출력해.")

    user_prompt = "\n".join(user_prompt_parts)

    response = client.models.generate_content(
        # 2.0 Flash: 무료 등급 1500 RPD (2.5 Flash 의 20 RPD 한도 회피)
        model="gemini-2.0-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=make_system_prompt(year, month, include_stocks),
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.5,
        ),
    )

    full_text = (response.text or "").strip()
    full_text = re.sub(r"^```(?:markdown|md)?\s*\n", "", full_text)
    full_text = re.sub(r"\n```\s*$", "", full_text)

    fm_match = re.search(r"^---\s*$", full_text, re.MULTILINE)
    if not fm_match:
        raise RuntimeError(f"No frontmatter for {year}-{month:02d}:\n{full_text[:400]}")
    markdown = full_text[fm_match.start():]

    out.write_text(markdown, encoding="utf-8")
    print(f"  WROTE {out.name} ({len(markdown)} chars)")
    return True


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    months = list(month_iter(START_YEAR, START_MONTH, END_YEAR, END_MONTH))
    print(f"Backfilling {len(months)} months: {months[0]} → {months[-1]}")
    print(f"Finnhub cutoff: {FINNHUB_CUTOFF} (months on/after include stock headlines)")

    written = 0
    skipped = 0
    failed = []
    for i, (y, m) in enumerate(months, 1):
        print(f"[{i}/{len(months)}] {y}-{m:02d}", flush=True)
        try:
            if generate_month(client, y, m):
                written += 1
                time.sleep(4)  # rate-limit cushion (Gemini Flash free = 10 RPM)
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR {y}-{m:02d}: {e}", file=sys.stderr, flush=True)
            failed.append((y, m, str(e)))
            # 429/quota 류면 더 오래 쉬기
            err_str = str(e).lower()
            if any(k in err_str for k in ("429", "quota", "rate", "resource_exhausted")):
                print("  rate-limit suspected, sleeping 30s...", flush=True)
                time.sleep(30)
            else:
                time.sleep(8)

    print(f"\nDone. wrote={written} skipped={skipped} failed={len(failed)}")
    if failed:
        for y, m, err in failed:
            print(f"  FAILED {y}-{m:02d}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
