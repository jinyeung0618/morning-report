---
layout: default
title: 모닝 리포트
---

매일 오전 10시 자동 발행. 시장 흐름과 watchlist 종목 정리.

## 최근 리포트

{% for post in site.posts %}
- **[{{ post.date | date: "%Y-%m-%d" }}]({{ post.url | relative_url }})** — {{ post.title }}
{% endfor %}

---

> 본 리포트는 학습·정보 공유 목적이며 매수·매도 추천이 아닙니다.
> 모든 결정은 본인 판단입니다.
