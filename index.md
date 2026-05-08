---
layout: default
title: 모닝 리포트
---

<section class="hero">
  <h1>📰 모닝 리포트</h1>
  <p class="subtitle">매일 오전 10시 자동 발행. 시장 흐름과 watchlist 종목 정리.</p>
</section>

<h2>최근 리포트</h2>

<ul class="report-list">
{% for post in site.posts %}
  <li>
    <a href="{{ post.url | relative_url }}">
      <span class="date">{{ post.date | date: "%Y-%m-%d" }}</span>
      <span class="title-text">{{ post.title | replace: "모닝 리포트 — ", "" | replace: "모닝 리포트 ", "" }}</span>
    </a>
  </li>
{% endfor %}
</ul>
