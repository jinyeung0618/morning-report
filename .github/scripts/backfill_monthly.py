"""
Monthly Summary Backfill (2020-01 ~ 2026-04)

워크플로(workflow_dispatch)로 1회 실행. 이미 존재하는 월은 건너뜀.
각 월의 거시·산업·watchlist 흐름을 Google Search 결과로 압축해서
_posts/YYYY-MM-LASTDAY-monthly-summary.md 로 저장.
"""

import os
import sys
import re
import time
import calendar
from datetime import datetime, timezone, timedelta
from pathlib import Path

from google import genai
from google.genai import types

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POSTS_DIR = REPO_ROOT / "_posts"

START_YEAR, START_MONTH = 2020, 1
END_YEAR, END_MONTH = 2026, 4  # inclusive; 5월부터는 일별 리포트가 채움

WATCHLIST_NOTE = """
## 추적 종목 (Watchlist)
존재 기간 주의 — 해당 월에 *이미 상장 되어 있던* 종목만 분위기 표기.
미상장 종목은 분위기를 "—" 로 두고 한 줄에 (예: "미상장. 2024년 상장") 표시.

해외:
- AAPL (애플) — 빅테크 코어. 전기간 존재.
- TSLA (테슬라) — EV + AI 로봇. 전기간 존재 (2010 IPO).
- NVDA (엔비디아) — AI 칩. 전기간 존재.
- UNH (유나이티드헬스) — 헬스케어. 전기간 존재.
- PLTR (팔란티어) — 방산·AI 소프트웨어. **2020년 9월 30일 상장.** 그 이전 월은 미상장.
- CEG (Constellation Energy) — 원전·AI 데이터센터 전력. **2022년 2월 2일 분사 상장.** 그 이전 월은 미상장.

국내:
- 487230 (KODEX 미국AI전력핵심인프라) — **2024년 11월 상장.** 그 이전 월은 미상장.
- 487240 (KODEX AI전력핵심설비) — **2024년 11월 상장.** 그 이전 월은 미상장.
"""


def make_system_prompt(year: int, month: int) -> str:
    month_label = f"{year}년 {month}월"
    return f"""너는 사용자의 주식 리서치 보조다. **{month_label}** 한 달간의 시장 흐름을 회고하는 월간 요약을 작성한다.

## 절대 원칙
1. Google Search 로 직접 검색한 내용만 사용. 추측·픽션 금지.
2. 이 달에 *실제로 일어난* 일만 적을 것. 검색에서 안 잡히면 "큰 사건 없음" 도 정직한 답.
3. 매수·매도 추천 금지.
4. 수치는 꼭 필요한 1-2개만. 평이한 한국어.
5. 출처 URL 본문에 박지 말 것.
6. **시점 인지** — 이 달({month_label}) *이후* 일어난 일은 절대 언급 금지. 회고는 그 달의 시점에서만.

{WATCHLIST_NOTE}

## 작업 절차

### Step 1 — 거시·산업 사건 검색
"{year} {month} stock market major events", "{year} {month} Fed FOMC", "{year} {month} AI industry", "{year} {month} geopolitics", "{year}년 {month}월 코스피".
이 달의 주요 헤드라인 3-5개 식별.

### Step 2 — Watchlist 종목별 검색
"[ticker] {year} {month} news" 또는 "[종목명] {year}년 {month}월".
각 종목의 그 달 분위기 식별. **상장 전 종목은 검색 생략하고 미상장 표기.**

### Step 3 — Markdown 출력

**중요: 아래 형식만. 설명·코드펜스 없이 `---` 부터 시작.**

---
layout: default
title: "월간 요약 — {month_label}"
date: {year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d} 18:00:00 +0900
type: monthly
---

## 이 달의 한 줄
(시장 전체 분위기 1-2 문장)

## 큰 흐름

**1. (제목)**
2-3줄 평이한 설명. 왜 중요했는지 한 줄 포함.

**2. (제목)**
...

**3. (제목)** (있으면)
...

## Watchlist 흐름

| 종목 | 분위기 | 한 줄 |
|---|---|---|
| 🍎 애플 (AAPL) | 🟢/🟡/🔴 | ... |
| 🚗 테슬라 (TSLA) | ... | ... |
| 🤖 엔비디아 (NVDA) | ... | ... |
| 🏥 UNH 유나이티드헬스 | ... | ... |
| 🦅 PLTR 팔란티어 | —/🟢/🟡/🔴 | ... 또는 "미상장 (2020-09 상장)" |
| ⚡ CEG 컨스텔레이션 | —/🟢/🟡/🔴 | ... 또는 "미상장 (2022-02 상장)" |
| 🔌 487230 미국AI전력인프라 | —/🟢/🟡/🔴 | ... 또는 "미상장 (2024-11 상장)" |
| ⚙️ 487240 AI전력핵심설비 | —/🟢/🟡/🔴 | ... 또는 "미상장 (2024-11 상장)" |

## 다음 달로 이어진 이슈
- 1-2개. 그 달 끝 시점에 미해결로 남았던 변수.

## 길이 가이드
한 화면에서 통독 가능한 길이. 검색이 부실하면 무리하지 말고 "큰 사건 없음"으로 정직하게 적을 것.
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


def generate_month(client: genai.Client, year: int, month: int) -> bool:
    out = output_path(year, month)
    if out.exists():
        print(f"  SKIP exists: {out.name}")
        return False

    system_prompt = make_system_prompt(year, month)
    user_prompt = f"{year}년 {month}월 한 달의 월간 요약을 작성해줘. 위 절차대로 Google Search 로 직접 검색한 뒤 markdown 본문만 출력해."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.6,
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

    written = 0
    skipped = 0
    failed = []
    for i, (y, m) in enumerate(months, 1):
        print(f"[{i}/{len(months)}] {y}-{m:02d}")
        try:
            if generate_month(client, y, m):
                written += 1
                time.sleep(2)  # 살짝 호흡
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR {y}-{m:02d}: {e}", file=sys.stderr)
            failed.append((y, m, str(e)))
            time.sleep(5)

    print(f"\nDone. wrote={written} skipped={skipped} failed={len(failed)}")
    if failed:
        for y, m, err in failed:
            print(f"  FAILED {y}-{m:02d}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
