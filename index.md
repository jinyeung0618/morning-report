---
layout: default
title: 재테크
charts: true
---

<section class="hero">
  <h1>💰 재테크</h1>
  <p class="subtitle">학습하면서 정리하는 시장·종목 노트.</p>
</section>

<nav class="section-nav" role="tablist" aria-label="섹션 선택">
  <div class="tabset tabset--lg">
    <button class="tabset__btn is-active" data-section="reports" type="button" role="tab">📰 모닝 리포트</button>
    <button class="tabset__btn" data-section="stats" type="button" role="tab">📊 지수·종목 통계</button>
  </div>
</nav>

<section class="section-panel is-active" id="section-reports" role="tabpanel" aria-label="모닝 리포트">
  <p class="stats-meta">매일 평일 오전 10시 자동 발행. 시장 흐름과 watchlist 종목 정리.</p>

  {% assign months = site.posts | group_by_exp: "post", "post.date | date: '%Y-%m'" %}
  {% for month in months %}
    {% assign count = month.items | size %}
    {% assign first_post = month.items | first %}

    {% if count == 1 and first_post.type == "monthly" %}
      <a class="report-month report-month--standalone" href="{{ first_post.url | relative_url }}">
        <span class="month-label">{{ first_post.date | date: "%Y년 %-m월" }}</span>
        <span class="month-tag">월간 요약</span>
        <span class="month-arrow" aria-hidden="true">→</span>
      </a>
    {% else %}
      <details class="report-month"{% if forloop.first %} open{% endif %}>
        <summary>
          <span class="month-label">{{ first_post.date | date: "%Y년 %-m월" }}</span>
          <span class="month-count">{{ count }}건</span>
          <span class="month-chevron" aria-hidden="true">▾</span>
        </summary>
        <ul class="report-list">
          {% for post in month.items %}
            <li>
              <a href="{{ post.url | relative_url }}"{% if post.type == "monthly" %} class="is-monthly"{% endif %}>
                {% if post.type == "monthly" %}
                  <span class="date">월간 요약</span>
                  <span class="weekday">{{ post.date | date: "%Y년 %-m월" }} 회고</span>
                {% else %}
                  <span class="date">{{ post.date | date: "%Y. %-m. %-d" }}</span>
                  <span class="weekday">{{ post.date | date: "%a" | replace: "Mon", "월요일" | replace: "Tue", "화요일" | replace: "Wed", "수요일" | replace: "Thu", "목요일" | replace: "Fri", "금요일" | replace: "Sat", "토요일" | replace: "Sun", "일요일" }}</span>
                {% endif %}
                <span class="arrow" aria-hidden="true">→</span>
              </a>
            </li>
          {% endfor %}
        </ul>
      </details>
    {% endif %}
  {% endfor %}
</section>

<section class="section-panel" id="section-stats" role="tabpanel" aria-label="지수·종목 통계">
  <p class="stats-meta">상장일부터 현재까지의 흐름. 변곡점에 있던 주요 사건 함께 보기.</p>

  <div class="stats-row">
    <div class="tabset" role="tablist" aria-label="지역">
      <button class="tabset__btn is-active" data-region="us" type="button" role="tab">해외</button>
      <button class="tabset__btn" data-region="kr" type="button" role="tab">국내</button>
    </div>
  </div>

  <div class="chip-list" id="statsTickers" role="tablist" aria-label="종목">
    <button class="chip is-active" data-ticker="AAPL" type="button" role="tab">AAPL · Apple</button>
  </div>

  <div class="stats-chart-wrap" id="stocksChart">
    <svg class="chart-svg" aria-label="가격 차트"></svg>
    <div class="chart-tooltip" id="chartTooltip"></div>
  </div>

  <p class="stats-hint">변곡점 마커에 호버·터치하면 그 시점의 사건이 툴팁으로 떠요.</p>
  <p class="stats-disclaimer">차트 데이터는 데모용 근사치입니다. 실시간 데이터 연동은 다음 단계.</p>
</section>
