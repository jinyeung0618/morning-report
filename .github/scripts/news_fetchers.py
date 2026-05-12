"""
종목별 뉴스 수집 모듈.

- 미국 6종목 → Finnhub company-news API (무료, 1년 history)
- 국내 ETF 2종목 → Google News RSS (키워드 기반)
"""

import os
import sys
import urllib.parse
from datetime import date, timedelta

import requests
import feedparser

FINNHUB_BASE = "https://finnhub.io/api/v1"

US_TICKERS = ["AAPL", "TSLA", "NVDA", "UNH", "PLTR", "CEG"]

KR_TICKERS = {
    "487230": {
        "name": "KODEX 미국AI전력핵심인프라",
        "queries": ["KODEX 미국AI전력핵심인프라", "GE Vernova 수주", "Vertiv 데이터센터"],
    },
    "487240": {
        "name": "KODEX AI전력핵심설비",
        "queries": ["KODEX AI전력핵심설비", "LS ELECTRIC 데이터센터", "효성중공업 HVDC"],
    },
}

# 종목별 IPO 일자 — 그 이전 백필에서는 빈 결과
IPO_DATES = {
    "PLTR": date(2020, 9, 30),
    "CEG": date(2022, 2, 2),
    "487230": date(2024, 11, 1),
    "487240": date(2024, 11, 1),
}


def _finnhub_news(symbol: str, from_d: date, to_d: date, limit: int = 8) -> list[dict]:
    token = os.environ.get("FINNHUB_API_KEY")
    if not token:
        return []
    try:
        r = requests.get(
            f"{FINNHUB_BASE}/company-news",
            params={
                "symbol": symbol,
                "from": from_d.isoformat(),
                "to": to_d.isoformat(),
                "token": token,
            },
            timeout=15,
        )
        r.raise_for_status()
        items = r.json()
    except Exception as e:
        print(f"  finnhub {symbol} error: {e}", file=sys.stderr)
        return []

    out = []
    seen_headlines = set()
    for item in items:
        h = (item.get("headline") or "").strip()
        if not h or h in seen_headlines:
            continue
        seen_headlines.add(h)
        out.append({
            "headline": h,
            "summary": (item.get("summary") or "").strip()[:240],
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "datetime": item.get("datetime", 0),
        })
        if len(out) >= limit:
            break
    return out


def _google_news_rss(query: str, when_days: int = 2, limit: int = 5) -> list[dict]:
    q = urllib.parse.quote(f"{query} when:{when_days}d")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"  rss {query} error: {e}", file=sys.stderr)
        return []
    out = []
    seen = set()
    for entry in feed.entries[: limit * 2]:
        title = getattr(entry, "title", "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        src_obj = getattr(entry, "source", None)
        src = src_obj.get("title", "") if isinstance(src_obj, dict) else ""
        out.append({
            "headline": title,
            "summary": "",
            "source": src,
            "url": getattr(entry, "link", ""),
            "datetime": 0,
        })
        if len(out) >= limit:
            break
    return out


def fetch_us_daily(target: date) -> dict[str, list[dict]]:
    """24h 내 미국 종목별 헤드라인."""
    from_d = target - timedelta(days=1)
    return {t: _finnhub_news(t, from_d, target, limit=8) for t in US_TICKERS}


def fetch_us_monthly(year: int, month: int) -> dict[str, list[dict]]:
    """한 달 미국 종목별 헤드라인."""
    import calendar
    from_d = date(year, month, 1)
    to_d = date(year, month, calendar.monthrange(year, month)[1])
    result = {}
    for t in US_TICKERS:
        ipo = IPO_DATES.get(t)
        if ipo and to_d < ipo:
            result[t] = []
            continue
        result[t] = _finnhub_news(t, max(from_d, ipo) if ipo else from_d, to_d, limit=10)
    return result


def fetch_kr_daily(target: date) -> dict[str, list[dict]]:
    """24~48h 국내 ETF 키워드 헤드라인."""
    result = {}
    for ticker, meta in KR_TICKERS.items():
        items = []
        for q in meta["queries"]:
            items.extend(_google_news_rss(q, when_days=2, limit=4))
        # dedupe
        seen = set()
        unique = []
        for it in items:
            if it["headline"] not in seen:
                seen.add(it["headline"])
                unique.append(it)
        result[ticker] = unique[:8]
    return result


def format_block(us_news: dict, kr_news: dict, include_kr: bool = True) -> str:
    """LLM 프롬프트에 주입할 헤드라인 블록."""
    lines = []
    lines.append("### 🌐 해외 (Finnhub)")
    for t in US_TICKERS:
        news = us_news.get(t, [])
        if not news:
            lines.append(f"\n**{t}**: (수집된 뉴스 없음 — 표에서 제외)")
            continue
        lines.append(f"\n**{t}**:")
        for n in news:
            src = f" ({n['source']})" if n["source"] else ""
            lines.append(f"- {n['headline']}{src}")
            if n["summary"]:
                lines.append(f"  · {n['summary']}")

    if include_kr:
        lines.append("\n### 🇰🇷 국내 (Google News)")
        for ticker, meta in KR_TICKERS.items():
            news = kr_news.get(ticker, [])
            if not news:
                lines.append(f"\n**{ticker} ({meta['name']})**: (수집된 뉴스 없음 — 표에서 제외)")
                continue
            lines.append(f"\n**{ticker} ({meta['name']})**:")
            for n in news:
                src = f" ({n['source']})" if n["source"] else ""
                lines.append(f"- {n['headline']}{src}")

    return "\n".join(lines)
