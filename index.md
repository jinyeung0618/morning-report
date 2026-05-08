---
layout: default
title: 모닝 리포트
charts: true
---

<section class="hero">
  <h1>📰 모닝 리포트</h1>
  <p class="subtitle">매일 오전 10시 자동 발행. 시장 흐름과 watchlist 종목 정리.</p>
</section>

<section class="stats-section">
  <h2>지수·종목 별 통계 보기</h2>
  <p class="stats-meta">상장일부터 현재까지의 흐름. 변곡점에 있던 주요 사건 함께 보기.</p>

  <div class="stats-region-tabs" role="tablist">
    <button class="stats-region-tab active" data-region="us" type="button">해외</button>
    <button class="stats-region-tab" data-region="kr" type="button">국내</button>
  </div>

  <div class="stats-tabs" role="tablist" id="statsTickers">
    <button class="stats-tab active" data-ticker="AAPL" type="button">AAPL · Apple</button>
  </div>

  <div class="stats-chart-wrap">
    <canvas id="stocksChart"></canvas>
  </div>

  <h3 class="stats-events-heading">주요 변곡점</h3>
  <ul class="stats-events" id="statsEvents"></ul>

  <p class="stats-disclaimer">차트 데이터는 데모용 근사치입니다. 실시간 데이터 연동은 다음 단계.</p>
</section>

<h2>최근 리포트</h2>

<ul class="report-list">
{% for post in site.posts %}
  <li>
    <a href="{{ post.url | relative_url }}">
      <span class="date">{{ post.date | date: "%Y. %-m. %-d" }}</span>
      <span class="weekday">{{ post.date | date: "%a" | replace: "Mon", "월요일" | replace: "Tue", "화요일" | replace: "Wed", "수요일" | replace: "Thu", "목요일" | replace: "Fri", "금요일" | replace: "Sat", "토요일" | replace: "Sun", "일요일" }}</span>
      <span class="arrow" aria-hidden="true">→</span>
    </a>
  </li>
{% endfor %}
</ul>
