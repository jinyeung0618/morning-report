"""
Morning Report Generator (GitHub Actions)

매일 평일 10:03 KST에 GitHub Actions가 호출.
Claude Opus 4.7 + web_search 로 어제~오늘 뉴스 검색 후 markdown 생성.
_posts/YYYY-MM-DD-morning-report.md 로 저장.
"""

import os
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import anthropic

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")
WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"][datetime.now(KST).weekday()]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POSTS_DIR = REPO_ROOT / "_posts"
OUTPUT_PATH = POSTS_DIR / f"{TODAY}-morning-report.md"

SYSTEM_PROMPT = f"""너는 사용자의 주식 리서치 보조다. 사용자는 초보 투자자. 매일 아침 짧고 쉬운 모닝 리포트를 작성한다.

오늘 날짜: {TODAY} ({WEEKDAY_KO}요일, KST)

## 절대 원칙
1. web_search 도구로 직접 검색한 내용만 사용. 추측·예측·"~할 가능성이 높다" 금지.
2. 매수·매도 추천 금지.
3. 수치는 꼭 필요한 1-2개만. 매출 디테일·EPS·capex 같은 분석가용 숫자 제외.
4. 출처 URL은 본문에 박지 말 것.
5. 평이한 한국어. 전문용어는 풀어서 설명.

## 추적 종목 (Watchlist) — 8종목

해외:
- AAPL (애플) — 빅테크 코어
- TSLA (테슬라) — EV + AI 로봇 (Optimus)
- NVDA (엔비디아) — AI 칩·로봇 두뇌
- UNH (유나이티드헬스) — 헬스케어 (고령화 베팅)
- PLTR (팔란티어) — 방산·AI 소프트웨어
- CEG (Constellation Energy) — 원전·AI 데이터센터 전력

국내:
- 487230 (KODEX 미국AI전력핵심인프라) — 미국 AI 전력 인프라 ETF (GE Vernova·Vertiv 중심)
- 487240 (KODEX AI전력핵심설비) — 국내 AI 전력 설비 ETF (LS ELECTRIC·효성중공업 중심)

## 작업 절차

### Step 1 — 거시 뉴스 검색 (web_search 3-4회)
검색어: "stock market news today", "Fed policy news", "AI chip industry news", "geopolitics economy news"

### Step 2 — Watchlist 종목별 검색 (각 1회)
"[종목명] news today" 또는 "[ticker] news today"

### Step 3 — 정보 압축
- 큰 흐름 3가지 (거시 1-2 + 산업 1-2)
- 각 watchlist 종목 분위기 🟢좋음 / 🟡혼조·양면 / 🔴악재 분류

### Step 4 — Markdown 출력

**중요: 아래 형식의 markdown만 출력. 설명·전제·주석 없이 `---` 부터 시작.**

---
layout: default
title: "모닝 리포트 — {TODAY}"
date: {TODAY} 10:03:00 +0900
---

## 오늘 한 줄
(시장 전체 분위기 1-2문장)

## 큰 흐름 3가지

**1. (제목)**
2-3줄 평이한 설명. "왜 중요한가" 한 줄 포함.

**2. (제목)**
...

**3. (제목)**
...

## Watchlist 8종목

### 🌐 해외

| 종목 | 분위기 | 한 줄 |
|---|---|---|
| 🍎 애플 (AAPL) | 🟢/🟡/🔴 | ... |
| 🚗 테슬라 (TSLA) | ... | ... |
| 🤖 엔비디아 (NVDA) | ... | ... |
| 🏥 UNH 유나이티드헬스 | ... | ... |
| 🦅 PLTR 팔란티어 | ... | ... |
| ⚡ CEG 컨스텔레이션 | ... | ... |

### 🇰🇷 국내

| 종목 | 분위기 | 한 줄 |
|---|---|---|
| 🔌 487230 미국AI전력인프라 | ... | ... |
| ⚙️ 487240 AI전력핵심설비 | ... | ... |

## 오늘 알아야 할 것
- 핵심 변수 1-2개. 너무 많이 쓰지 말 것.

## 길이 가이드
출근길 5분 내 통독 가능한 길이. 검색 결과 부실하면 "오늘은 큰 뉴스 없음"도 정직한 답.
"""

USER_PROMPT = f"오늘({TODAY} {WEEKDAY_KO}요일) 모닝 리포트를 작성해줘. 위 절차대로 web_search 도구로 직접 뉴스를 검색한 뒤 markdown 본문만 출력해."


def generate():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [{"role": "user", "content": USER_PROMPT}]

    # 한 번 호출 후 pause_turn 이면 이어서 호출
    for attempt in range(5):
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 12}],
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        # assistant turn 을 history 에 추가
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "pause_turn":
            # 그대로 이어서 호출
            continue
        break
    else:
        raise RuntimeError("Too many pause_turn loops")

    # text 블록만 추출
    text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    full_text = "\n".join(text_parts).strip()

    # 첫 `---` 부터가 jekyll frontmatter
    fm_match = re.search(r"^---\s*$", full_text, re.MULTILINE)
    if not fm_match:
        raise RuntimeError(f"Could not find frontmatter in response:\n{full_text[:500]}")
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
