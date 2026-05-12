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

# REPORT_DATE 환경변수가 있으면 그 날짜로 생성 (재생성용). 없으면 오늘.
_override = os.environ.get("REPORT_DATE", "").strip()
if _override:
    NOW_KST = datetime.strptime(_override, "%Y-%m-%d").replace(tzinfo=KST)
else:
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
2. **Watchlist 표는 사용자가 user prompt 로 넘기는 "사전 수집된 헤드라인" 안에서만 작성.** 추세·일반론·외부 정보 추가 금지.
3. **모든 watchlist 8종목은 표에 항상 포함.** 헤드라인 없는 종목은 행을 빼지 말고: 분위기 칸 `—`, 내용 칸 `🤷 뚜렷한 기사 없음` 으로 표기.
4. 검색·헤드라인이 빈약하면 큰 흐름 섹션은 짧게. 길이 채우려고 메꾸지 말 것.
5. 매수·매도 추천 금지.
6. 출처 URL 본문에 박지 말 것.

## 글쓰기 톤 — 위반 시 리포트 무효, 절대 절대 지킬 것

독자는 **친구**. 분석가 보고서 톤 절대 금지. 카톡으로 시장 얘기해주는 톤.

### 🚫 금지 표현 (보이면 즉시 다시 써)
- "~를 기록했어요/기록했고/기록했답니다", "~를 경신했어요"
- "~선을 돌파하며", "~선을 넘어서며"
- "~를 견인했어요", "~를 주도했어요"
- "뚜렷한 상승세/하락세", "강세/약세 흐름"
- "견조한 / 양호한 / 탄탄한 / 가파른"
- "~로 풀이돼요", "~로 해석돼요", "~로 작용해요"
- "전망/우려/관측이 제기" 같은 명사형 표현
- "~에 힘입어", "~를 바탕으로"

### ✅ 이렇게 바꿔쓸 것
| 분석가 톤 (❌) | 친구 톤 (✅) |
|---|---|
| 사상 최고치를 기록했어요 | 역대 가장 높았어요 |
| S&P 500이 7,200선 돌파 | S&P 500 7,200 넘었어요 |
| 뚜렷한 상승세를 보였어요 | 쭉 올랐어요 |
| 빅테크 호실적에 힘입어 | 빅테크 실적 잘 나온 덕분에 |
| 견조한 소비 심리 | 소비는 그래도 괜찮은 상태 |
| AI 투자 심리 회복으로 풀이돼요 | AI 투자 분위기가 다시 살아난 거죠 |
| 공급 부족 우려 제기 | 공급 부족할 수 있어 걱정 |
| FOMC dissent 4명 | 연준 회의에서 4명이 반대 |
| EPS $2.56, +21% YoY | 실적이 작년보다 21% 늘었음 |
| 매수 의견 / 목표 주가 상향 | "사도 될 것 같다" 의견 / 목표가 더 높게 잡음 |

### 좋은 예 (직접 따라써)

> 4월 미국 증시 분위기 좋았어요. 나스닥은 한 달간 진짜 많이 올랐어요 — 2020년 4월 코로나 직후 이후로 제일 좋았던 달.
> AI 회사들 실적이 잘 나온 게 컸음. 중동 긴장도 잠깐 풀린 듯한 분위기라 유가도 좀 안정됐고요.

### 나쁜 예 (절대 이렇게 쓰지 말 것)

> 4월 미국 증시는 빅테크 기업들의 호실적에 힘입어 뚜렷한 상승세를 보였어요. S&P 500 지수는 7,200선을 돌파하며 사상 최고치를 기록했고, 나스닥은 가장 좋은 월간 상승률을 기록하며 시장을 주도했어요.

### Watchlist 셀 톤
Finnhub 헤드라인은 영문 분석가 톤. 의미만 살리고 *친구 톤으로 다시 써라*. 헤드라인 그대로 번역 ❌.
- 헤드라인: "Apple beats Q1 EPS estimates" → ✅ 셀: "1분기 실적이 시장 예상보다 잘 나옴"
- 헤드라인: "Tesla downgraded to Hold by Morgan Stanley" → ✅ 셀: "모건스탠리에서 평가 한 단계 내림 (관망 쪽)"
- 헤드라인: "NVDA stock surges on AI demand" → ✅ 셀: "AI 수요로 주가 많이 뛰었음"

### 기타
- 일반 시사 용어 (연준, 호르무즈, FOMC, 코스피)는 풀어쓰지 마. 잔소리.
- 매출·EPS·P/E·자본지출 같은 분석가 숫자 빼. "X% 늘었다" 정도.
- 한 문장 짧게, 한 아이디어당.
- "왜 중요한가" 는 *사용자한테 뭐가 바뀌는지* 관점.

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

## Watchlist

### 🌐 해외

| 종목 | 분위기 | 한 줄 |
|---|---|---|
| <span class="ticker-logo"><img src="https://cdn.simpleicons.org/apple/000000" alt=""></span> AAPL (애플) | 🟢/🟡/🔴 또는 — | 헤드라인 있으면 인용. 없으면 `🤷 뚜렷한 기사 없음` |
| <span class="ticker-logo"><img src="https://cdn.simpleicons.org/tesla/cc0000" alt=""></span> TSLA (테슬라) | ... | ... |
| <span class="ticker-logo"><img src="https://cdn.simpleicons.org/nvidia/76b900" alt=""></span> NVDA (엔비디아) | ... | ... |
| <span class="ticker-logo ticker-logo--badge ticker-logo--unh">UNH</span> UNH (유나이티드헬스) | ... | ... |
| <span class="ticker-logo"><img src="https://cdn.simpleicons.org/palantir/000000" alt=""></span> PLTR (팔란티어) | ... | ... |
| <span class="ticker-logo ticker-logo--badge ticker-logo--ceg">CEG</span> CEG (컨스텔레이션) | ... | ... |

### 🇰🇷 국내

| 종목 | 분위기 | 한 줄 |
|---|---|---|
| <span class="ticker-logo ticker-logo--badge ticker-logo--kodex">230</span> 487230 (미국AI전력) | 🟢/🟡/🔴 또는 — | 헤드라인 있으면 인용. 없으면 `🤷 뚜렷한 기사 없음` |
| <span class="ticker-logo ticker-logo--badge ticker-logo--kodex">240</span> 487240 (AI전력설비) | ... | ... |

분위기 기준: 헤드라인 내용 자체가 호재면 🟢, 악재면 🔴, 양면이면 🟡. *주가 추세에서 유추하지 말 것.*
뉴스 없는 종목: 분위기 칸 `—`, 한 줄 칸 `🤷 뚜렷한 기사 없음`.
**각 표 위·아래에 빈 줄 반드시 둘 것** (markdown 파싱 조건).

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

    import time as _time
    response = None
    full_text = ""
    for attempt in range(3):
        response = client.models.generate_content(
            # flash-lite: 무료 1000 RPD (flash 의 20 RPD 한도 회피 + 백필과 통일)
            model="gemini-2.5-flash-lite",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.5,
            ),
        )
        full_text = (response.text or "").strip()
        # 일부 케이스: .text 가 비어도 parts 안에 text 있음
        if not full_text and response.candidates:
            parts_text = []
            for c in response.candidates:
                content = getattr(c, "content", None)
                for p in getattr(content, "parts", []) or []:
                    t = getattr(p, "text", None)
                    if t:
                        parts_text.append(t)
            full_text = "\n".join(parts_text).strip()
        if full_text:
            break
        # 빈 응답 — 재시도
        diag = []
        try:
            for i, c in enumerate(response.candidates or []):
                diag.append(f"cand[{i}].finish_reason={getattr(c, 'finish_reason', None)}")
            if hasattr(response, "prompt_feedback"):
                diag.append(f"feedback={response.prompt_feedback}")
        except Exception:
            pass
        print(f"Empty response (attempt {attempt+1}/3). {' | '.join(diag)}", flush=True)
        _time.sleep(5)

    if not full_text:
        raise RuntimeError("Gemini returned empty text after 3 attempts.")

    # 코드펜스 / Google Search 인용 마커 제거
    full_text = re.sub(r"^```(?:markdown|md)?\s*\n", "", full_text)
    full_text = re.sub(r"\n```\s*$", "", full_text)
    full_text = re.sub(r"\s*\[cite:\s*[\d,\s]+\]", "", full_text)
    full_text = full_text.strip()

    # 프론트매터 있으면 거기서부터, 없으면 우리가 붙임
    fm_match = re.search(r"^---\s*$", full_text, re.MULTILINE)
    if fm_match:
        markdown = full_text[fm_match.start():]
    else:
        front = f'---\nlayout: default\ntitle: "모닝 리포트 — {TODAY}"\ndate: {TODAY} 10:03:00 +0900\n---\n\n'
        markdown = front + full_text
        print("  Note: model skipped frontmatter, inserted programmatically.", flush=True)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(markdown)} chars)")


if __name__ == "__main__":
    try:
        generate()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
