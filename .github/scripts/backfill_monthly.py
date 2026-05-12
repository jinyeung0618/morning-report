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
import subprocess
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from google import genai
from google.genai import types

import news_fetchers

# 무료 등급 한도 (검증: 2026-05-12)
#   gemini-2.5-flash-lite: 15 RPM, 1000 RPD
#   gemini-2.0-flash: RETIRED 2026-03-03, 쓰면 limit:0
MODEL = "gemini-2.5-flash-lite"
MAX_RETRIES = 3
MIN_SLEEP_BETWEEN_CALLS = 5  # 분당 15 RPM 에 여유 둠

# 짧은 한도 (분당 RPM/TPM): retryDelay 이만큼 이하면 자리에서 대기
# 긴 한도 (일일 RPD/TPD): 이상이면 graceful exit → 다음 워크플로 트리거 때 이어서
SHORT_QUOTA_THRESHOLD_SEC = 300  # 5분


class DailyQuotaExhausted(Exception):
    """retryDelay 가 길어서 (>5min) 일일 한도 도달로 판단. 깔끔하게 종료해야 함."""


def _extract_retry_delay(err_str: str) -> float:
    """429 응답에서 retryDelay 초 추출. 없으면 60s 기본 (per-minute 추정)."""
    m = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str)
    if m:
        return float(m.group(1)) + 2
    m = re.search(r"'retryDelay':\s*'(\d+)s'", err_str)
    if m:
        return float(m.group(1)) + 2
    return 60.0

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POSTS_DIR = REPO_ROOT / "_posts"

DEFAULT_START = (2020, 1)
DEFAULT_END = (2026, 4)


def _parse_ym_env(var: str, fallback: tuple[int, int]) -> tuple[int, int]:
    raw = os.environ.get(var, "").strip()
    if not raw:
        return fallback
    m = re.match(r"^(\d{4})-(\d{1,2})$", raw)
    if not m:
        print(f"warning: {var}={raw!r} 형식 이상, 기본값 사용", file=sys.stderr)
        return fallback
    return (int(m.group(1)), int(m.group(2)))


START_YEAR, START_MONTH = _parse_ym_env("BACKFILL_FROM", DEFAULT_START)
END_YEAR, END_MONTH = _parse_ym_env("BACKFILL_TO", DEFAULT_END)

# from > to 면 자동 교정 (입력 순서 실수 보호)
if (START_YEAR, START_MONTH) > (END_YEAR, END_MONTH):
    print(
        f"warning: from ({START_YEAR}-{START_MONTH:02d}) > to ({END_YEAR}-{END_MONTH:02d}). 자동 교환.",
        file=sys.stderr,
    )
    (START_YEAR, START_MONTH), (END_YEAR, END_MONTH) = (END_YEAR, END_MONTH), (START_YEAR, START_MONTH)

print(f"Resolved range: {START_YEAR}-{START_MONTH:02d} → {END_YEAR}-{END_MONTH:02d}")

COMMIT_PER_MONTH = os.environ.get("BACKFILL_COMMIT_PER_MONTH", "true").lower() == "true"

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
## Watchlist 주요 이벤트

### 🌐 해외

| 종목 | 분위기 | 그 달 주요 이벤트 |
|---|---|---|
| <span title="애플"><span class="ticker-logo"><img src="https://cdn.simpleicons.org/apple/000000" alt=""></span> AAPL</span> | 🟢/🟡/🔴 또는 — | 헤드라인 있으면 1-2개 한 줄로 묶기. 없으면 `🤷 뚜렷한 기사 없음` |
| <span title="테슬라"><span class="ticker-logo"><img src="https://cdn.simpleicons.org/tesla/cc0000" alt=""></span> TSLA</span> | ... | ... |
| <span title="엔비디아"><span class="ticker-logo"><img src="https://cdn.simpleicons.org/nvidia/76b900" alt=""></span> NVDA</span> | ... | ... |
| <span title="유나이티드헬스"><span class="ticker-logo ticker-logo--badge ticker-logo--unh">UNH</span> UNH</span> | ... | ... |
| <span title="팔란티어"><span class="ticker-logo"><img src="https://cdn.simpleicons.org/palantir/000000" alt=""></span> PLTR</span> | ... | ... |
| <span title="컨스텔레이션"><span class="ticker-logo ticker-logo--badge ticker-logo--ceg">CEG</span> CEG</span> | ... | ... |

(국내 ETF 회고 뉴스는 자동 수집하지 않아 국내 섹션 생략.)

**중요**: 모든 헤딩과 표 사이, 표와 다음 단락 사이에 *빈 줄* 반드시 포함 (markdown 표 파싱 조건).

분위기 기준: 그 달 헤드라인 종합 결과. 헤드라인이 PR 류·중립이면 🟡, 호재 다수면 🟢, 악재 다수면 🔴.
뉴스 없는 종목: 분위기 칸 `—`, 내용 칸 `🤷 뚜렷한 기사 없음`. 행을 빼지 말 것.
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
5. 매수·매도 추천 금지.
6. URL 본문에 박지 말 것.

## 글쓰기 톤 — 위반 시 리포트 무효, 절대 절대 지킬 것

독자는 **친구**. 분석가 보고서 톤 절대 금지. 카톡으로 시장 얘기해주는 톤.

### 🚫 금지 표현 (보이면 즉시 다시 써)
- "~를 기록했어요/기록했고/기록했답니다", "~를 경신했어요"
- "~선을 돌파하며", "~선을 넘어서며"
- "~를 견인했어요", "~를 주도했어요"
- "뚜렷한 상승세/하락세", "강세/약세 흐름"
- "견조한 / 양호한 / 탄탄한 / 가파른"
- "~로 풀이돼요", "~로 해석돼요", "~로 작용해요"
- "전망/우려/관측이 제기" 같은 명사형
- "~에 힘입어", "~를 바탕으로"

### ✅ 이렇게 바꿔쓸 것 (필수)
- "사상 최고치를 기록했어요" → "역대 가장 높았어요"
- "S&P 500이 7,200선 돌파" → "S&P 500 7,200 넘었어요"
- "뚜렷한 상승세를 보였어요" → "쭉 올랐어요"
- "빅테크 호실적에 힘입어" → "빅테크 실적 잘 나온 덕분에"
- "견조한 소비 심리" → "소비는 그래도 괜찮은 상태"
- "AI 투자 심리 회복으로 풀이돼요" → "AI 투자 분위기가 다시 살아난 거죠"
- "FOMC dissent 4명" → "연준 회의에서 4명이 반대"
- "EPS $2.56, +21% YoY" → "실적이 작년보다 21% 늘었음"
- "매수 의견 / 목표 주가 상향" → "사도 될 것 같다 의견 / 목표가 더 높게 잡음"
- "1분기 실적 시장 예상 상회" → "1분기 실적이 시장 예상보다 잘 나옴"
- "칼핀(Calpine) 인수 효과" → "칼핀 회사를 사들인 효과"

### 좋은 예 (직접 따라써)

> 4월 미국 증시 분위기 좋았어요. 나스닥은 한 달간 진짜 많이 올랐어요 — 2020년 4월 코로나 직후 이후로 제일 좋았던 달.
> AI 회사들 실적이 잘 나온 게 컸음. 중동 긴장도 잠깐 풀린 듯한 분위기라 유가도 좀 안정됐고요.

### 나쁜 예 (절대 이렇게 쓰지 말 것)

> 4월 미국 증시는 빅테크 기업들의 호실적에 힘입어 뚜렷한 상승세를 보였어요. S&P 500 지수는 7,200선을 돌파하며 사상 최고치를 기록했고, 나스닥은 가장 좋은 월간 상승률을 기록하며 시장을 주도했어요.

### Watchlist 셀 톤
Finnhub 헤드라인은 영문 분석가 톤. 의미만 살리고 *친구 톤으로 다시 써라*. 헤드라인 그대로 번역 ❌.
- 헤드라인: "Apple beats Q1 EPS estimates" → ✅ "1분기 실적이 시장 예상보다 잘 나옴"
- 헤드라인: "Tesla downgraded to Hold by Morgan Stanley" → ✅ "모건스탠리에서 평가 한 단계 내림 (관망 쪽)"

### 기타
- 일반 시사 용어 (연준, 호르무즈, FOMC, 코스피)는 풀어쓰지 마.
- 매출·EPS·P/E·자본지출 같은 분석가 숫자 빼.
- 한 문장 짧게, 한 아이디어당.

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

    # 429 시 retryDelay 만큼 대기 후 같은 월 재시도
    # retryDelay 가 SHORT_QUOTA_THRESHOLD_SEC 초과면 일일 한도 → graceful exit
    response = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=make_system_prompt(year, month, include_stocks),
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.5,
                ),
            )
            break
        except Exception as e:
            err_str = str(e)
            err_lower = err_str.lower()
            is_rate = any(k in err_lower for k in ("429", "quota", "rate", "resource_exhausted"))
            is_transient = any(k in err_lower for k in ("503", "500", "502", "504", "unavailable", "deadline", "internal"))
            if is_rate:
                delay = _extract_retry_delay(err_str)
                if delay > SHORT_QUOTA_THRESHOLD_SEC:
                    raise DailyQuotaExhausted(f"retry in {delay:.0f}s (~{delay/3600:.1f}h)")
                if attempt < MAX_RETRIES - 1:
                    print(f"  rate-limited (short), retrying same month in {delay:.0f}s (attempt {attempt+1}/{MAX_RETRIES})", flush=True)
                    time.sleep(delay)
                    continue
                raise
            if is_transient:
                # 5xx, 일시 서버 장애 — 지수 backoff 로 재시도
                if attempt < MAX_RETRIES - 1:
                    backoff = 5 * (2 ** attempt)  # 5s, 10s, 20s
                    print(f"  transient error ({err_str[:80]}), retrying in {backoff}s (attempt {attempt+1}/{MAX_RETRIES})", flush=True)
                    time.sleep(backoff)
                    continue
                raise
            raise

    full_text = (response.text or "").strip()
    # 코드펜스 + Google Search 인용 마커 제거
    full_text = re.sub(r"^```(?:markdown|md)?\s*\n", "", full_text)
    full_text = re.sub(r"\n```\s*$", "", full_text)
    full_text = re.sub(r"\s*\[cite:\s*[\d,\s]+\]", "", full_text)
    full_text = full_text.strip()

    fm_match = re.search(r"^---\s*$", full_text, re.MULTILINE)
    if fm_match:
        markdown = full_text[fm_match.start():]
    else:
        last_day = calendar.monthrange(year, month)[1]
        front = f'---\nlayout: default\ntitle: "월간 요약 — {year}년 {month}월"\ndate: {year}-{month:02d}-{last_day:02d} 18:00:00 +0900\ntype: monthly\n---\n\n'
        markdown = front + full_text
        print(f"  Note: model skipped frontmatter for {year}-{month:02d}, inserted programmatically.", flush=True)

    out.write_text(markdown, encoding="utf-8")
    print(f"  WROTE {out.name} ({len(markdown)} chars)")
    return True


def _git(*args: str) -> int:
    """git 명령 실행. 실패해도 죽지 않음 (워크플로 commit 단계가 안전망)."""
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=REPO_ROOT)
        if r.returncode != 0:
            print(f"  git {' '.join(args)} -> {r.returncode}: {r.stderr.strip()}", flush=True)
        return r.returncode
    except Exception as e:
        print(f"  git {' '.join(args)} failed: {e}", flush=True)
        return 1


def commit_and_push_one(year: int, month: int, path: Path) -> bool:
    """한 월의 파일을 add → commit → push. 실패해도 다음 월 진행."""
    if _git("add", str(path)) != 0:
        return False
    if _git("commit", "-m", f"Monthly summary {year}-{month:02d}") != 0:
        return False
    if _git("push") != 0:
        return False
    print(f"  PUSHED {path.name}", flush=True)
    return True


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    months = list(month_iter(START_YEAR, START_MONTH, END_YEAR, END_MONTH))
    months.reverse()  # 최근부터 거꾸로 — 가치 큰 거 먼저, quota 막혀도 최근은 살아있음
    print(f"Backfilling {len(months)} months (recent→old): {months[0]} → {months[-1]}")
    print(f"Finnhub cutoff: {FINNHUB_CUTOFF} (months on/after include stock headlines)")
    print(f"Commit-per-month: {COMMIT_PER_MONTH}")

    written = 0
    skipped = 0
    failed = []
    quota_exhausted_at = None
    for i, (y, m) in enumerate(months, 1):
        print(f"[{i}/{len(months)}] {y}-{m:02d}", flush=True)
        try:
            if generate_month(client, y, m):
                written += 1
                if COMMIT_PER_MONTH:
                    commit_and_push_one(y, m, output_path(y, m))
                time.sleep(MIN_SLEEP_BETWEEN_CALLS)
            else:
                skipped += 1
        except DailyQuotaExhausted as e:
            quota_exhausted_at = (y, m, str(e), months[i-1:])
            print(f"  DAILY QUOTA EXHAUSTED at {y}-{m:02d}: {e}", file=sys.stderr, flush=True)
            break
        except Exception as e:
            print(f"  ERROR {y}-{m:02d}: {e}", file=sys.stderr, flush=True)
            failed.append((y, m, str(e)))
            time.sleep(8)

    print(f"\nDone. wrote={written} skipped={skipped} failed={len(failed)}")

    if quota_exhausted_at:
        y, m, err_msg, remaining = quota_exhausted_at
        print(f"\nDaily quota exhausted at {y}-{m:02d}: {err_msg}")
        print(f"Remaining {len(remaining)} months will retry on next workflow run:")
        for ry, rm in remaining[:10]:
            print(f"  - {ry}-{rm:02d}")
        if len(remaining) > 10:
            print(f"  ... ({len(remaining)-10} more)")
        print("(Cron 으로 매일 자동 재시도되거나 수동 트리거 가능. 종료 코드 0 로 정상 종료.)")
        return  # exit 0 — 일일 한도는 예상된 종료

    if failed:
        for y, m, err in failed:
            print(f"  FAILED {y}-{m:02d}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
