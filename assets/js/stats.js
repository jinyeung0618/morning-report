// 모닝 리포트 — 종목 통계 차트 (데모)
// Chart.js 기반. 종목 추가 시 STOCKS 객체에 항목 추가.

(function () {
  if (typeof Chart === 'undefined') return;

  // ---- 데이터: 참조점에서 월별 시계열로 확장 (split-adjusted 근사치) ----
  const STOCKS = {
    AAPL: {
      label: 'AAPL · Apple',
      region: 'us',
      currency: '$',
      // 주요 참조 가격 (대략, 분할 조정 기준)
      refs: [
        ['1985-01', 0.07], ['1990-01', 0.32], ['1995-01', 0.30],
        ['1997-09', 0.20], ['2000-03', 1.30], ['2002-09', 0.25],
        ['2005-01', 1.50], ['2007-06', 3.50], ['2008-12', 3.00],
        ['2012-09', 22.00], ['2013-04', 15.00], ['2015-02', 30.00],
        ['2018-10', 58.00], ['2018-12', 39.00], ['2020-03', 57.00],
        ['2020-12', 132.00], ['2022-01', 182.00], ['2022-12', 125.00],
        ['2024-06', 225.00], ['2026-05', 278.00],
      ],
      events: [
        { date: '1985-09', title: '스티브 잡스 애플 떠남', desc: 'Macintosh 출시 후 경영진 갈등으로 잡스가 사임. 회사는 이후 10여 년 부진.' },
        { date: '1997-09', title: '잡스 임시 CEO 복귀', desc: 'NeXT 인수와 함께 잡스가 돌아옴. iMac, iPod로 이어지는 부활의 시작.' },
        { date: '2001-10', title: 'iPod 출시', desc: '"1,000 songs in your pocket". 음악 산업과 애플의 운명을 바꾼 제품.' },
        { date: '2007-06', title: 'iPhone 출시', desc: '스마트폰 시장 자체를 재정의. 이후 10년간 애플 성장의 중심.' },
        { date: '2008-10', title: '글로벌 금융위기', desc: '리먼 사태로 시장 전반 폭락. 이후 V자 회복.' },
        { date: '2010-04', title: 'iPad 출시', desc: '태블릿 시장 개창. 새로운 기기 카테고리 정착.' },
        { date: '2014-09', title: 'iPhone 6 (대화면)', desc: '대화면 트렌드 수용. 중국 시장 공략 가속.' },
        { date: '2018-08', title: '시가총액 1조 달러 돌파', desc: '미국 상장사 최초 1조달러 진입.' },
        { date: '2020-03', title: 'COVID-19 폭락', desc: '팬데믹 초기 시장 공포로 모든 자산 급락. 빠른 V자 회복.' },
        { date: '2022-01', title: '시총 3조 달러 (일시)', desc: '인플레이션·금리 우려로 이후 조정.' },
        { date: '2024-06', title: 'Apple Intelligence 발표', desc: 'WWDC에서 자체 AI 시스템 공개. 디바이스 기반 AI 통합 노선.' },
      ],
    },
  };

  // ---- 유틸: 참조점 → 월별 series (로그 보간) ----
  function expandToMonthly(refs) {
    // UTC로 일관 처리 (toISOString() 타임존 시프트 방지)
    const points = refs.map(([d, c]) => {
      const [y, m] = d.split('-').map(Number);
      return { date: new Date(Date.UTC(y, m - 1, 1)), close: c };
    });
    points.sort((a, b) => a.date - b.date);

    const result = [];
    for (let i = 0; i < points.length - 1; i++) {
      const a = points[i], b = points[i + 1];
      const months = (b.date.getUTCFullYear() - a.date.getUTCFullYear()) * 12 +
                     (b.date.getUTCMonth() - a.date.getUTCMonth());
      for (let m = 0; m < months; m++) {
        const d = new Date(a.date);
        d.setUTCMonth(d.getUTCMonth() + m);
        const t = m / months;
        const lc = Math.log(a.close) * (1 - t) + Math.log(b.close) * t;
        result.push({
          x: d.toISOString().slice(0, 7),
          y: Math.exp(lc),
        });
      }
    }
    const last = points[points.length - 1];
    result.push({
      x: last.date.toISOString().slice(0, 7),
      y: last.close,
    });
    return result;
  }

  // ---- 차트 ----
  let chart = null;
  let currentTicker = 'AAPL';

  function getThemeColors() {
    const isDark = document.documentElement.dataset.theme === 'dark';
    return {
      isDark,
      line: isDark ? '#2997FF' : '#0071E3',
      fill: isDark ? 'rgba(41,151,255,0.10)' : 'rgba(0,113,227,0.06)',
      grid: isDark ? '#48484A' : '#E8E8ED',
      gridSoft: isDark ? '#2C2C2E' : '#F5F5F7',
      text: isDark ? '#AEAEB2' : '#636366',
      tooltipBg: isDark ? '#1C1C1E' : '#FFFFFF',
      tooltipText: isDark ? '#F5F5F7' : '#1C1C1E',
      tooltipBorder: isDark ? '#48484A' : '#E8E8ED',
    };
  }

  function renderChart(ticker) {
    const stock = STOCKS[ticker];
    if (!stock) return;

    const canvas = document.getElementById('stocksChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const data = expandToMonthly(stock.refs);
    const c = getThemeColors();

    // 이벤트 룩업 — 차트 포인트에 마커·툴팁 표시용
    const eventMap = {};
    (stock.events || []).forEach(e => { eventMap[e.date] = e.title; });

    const pointRadii = data.map(p => eventMap[p.x] ? 5 : 0);
    const pointHoverRadii = data.map(p => eventMap[p.x] ? 8 : 0);
    const pointBgs = data.map(p => eventMap[p.x] ? c.line : 'transparent');
    const pointBorders = data.map(p => eventMap[p.x] ? c.tooltipBg : 'transparent');
    // 변곡점에서만 hover 활성 — 나머지는 hit 0
    const pointHitRadii = data.map(p => eventMap[p.x] ? 20 : 0);

    if (chart) chart.destroy();

    const lastLabel = data[data.length - 1].x;

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(p => p.x),
        datasets: [{
          label: stock.label,
          data: data.map(p => p.y),
          borderColor: c.line,
          backgroundColor: c.fill,
          borderWidth: 1.5,
          fill: true,
          pointRadius: pointRadii,
          pointHoverRadius: pointHoverRadii,
          pointBackgroundColor: pointBgs,
          pointBorderColor: pointBorders,
          pointBorderWidth: 2,
          pointHitRadius: pointHitRadii,
          tension: 0.15,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'nearest', intersect: true },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: c.tooltipBg,
            titleColor: c.tooltipText,
            bodyColor: c.text,
            borderColor: c.tooltipBorder,
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            titleFont: { size: 12, weight: '600' },
            bodyFont: { size: 13 },
            callbacks: {
              title: (items) => items[0] ? items[0].label : '',
              label: (item) => {
                const date = data[item.dataIndex].x;
                const price = `${stock.currency}${item.parsed.y.toFixed(2)}`;
                const ev = eventMap[date];
                return ev ? [price, `📌 ${ev}`] : price;
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: c.text,
              font: { size: 10, family: 'SF Mono, Fira Code, monospace' },
              maxRotation: 0,
              autoSkip: true,
              maxTicksLimit: 9,
              callback: function (val) {
                const label = this.getLabelForValue(val);
                if (label === lastLabel) return '현재';
                return label ? label.split('-')[0] : label;
              },
            },
            grid: { display: false },
          },
          y: {
            type: 'logarithmic',
            // 10의 거듭제곱만 표시 (0.1 / 1 / 10 / 100 / 1000 ...)
            afterBuildTicks: (axis) => {
              axis.ticks = axis.ticks.filter(t => {
                const log = Math.log10(t.value);
                return Math.abs(log - Math.round(log)) < 0.001;
              });
            },
            ticks: {
              color: c.text,
              font: { size: 10, family: 'SF Mono, Fira Code, monospace' },
              callback: (v) => stock.currency + v,
            },
            grid: { color: c.gridSoft },
          },
        },
      },
    });
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function selectTicker(ticker) {
    currentTicker = ticker;
    document.querySelectorAll('.stats-tab').forEach(b => {
      b.classList.toggle('active', b.dataset.ticker === ticker);
    });
    renderChart(ticker);
  }

  function clearChartAndEvents() {
    if (chart) { chart.destroy(); chart = null; }
    currentTicker = null;
  }

  function setStatsBodyVisible(visible) {
    document.querySelectorAll('.stats-chart-wrap, .stats-disclaimer')
      .forEach(el => { el.style.display = visible ? '' : 'none'; });
  }

  function selectRegion(region) {
    document.querySelectorAll('.stats-region-tab').forEach(b => {
      b.classList.toggle('active', b.dataset.region === region);
    });
    const tickerWrap = document.getElementById('statsTickers');
    if (!tickerWrap) return;

    const visibleTickers = Object.entries(STOCKS)
      .filter(([_, s]) => s.region === region)
      .map(([key]) => key);

    if (visibleTickers.length === 0) {
      tickerWrap.innerHTML = '<p class="stats-empty">아직 등록된 종목이 없습니다.</p>';
      clearChartAndEvents();
      setStatsBodyVisible(false);
      return;
    }

    setStatsBodyVisible(true);
    tickerWrap.innerHTML = visibleTickers.map((key, i) => `
      <button class="stats-tab${i === 0 ? ' active' : ''}" data-ticker="${key}" type="button">${escapeHtml(STOCKS[key].label)}</button>
    `).join('');
    selectTicker(visibleTickers[0]);
  }

  // ---- 초기화 ----
  function init() {
    // 종목 탭 클릭
    document.addEventListener('click', (e) => {
      const tab = e.target.closest('.stats-tab');
      if (tab && tab.dataset.ticker) selectTicker(tab.dataset.ticker);
      const region = e.target.closest('.stats-region-tab');
      if (region && region.dataset.region) selectRegion(region.dataset.region);
    });

    // 첫 렌더
    renderChart(currentTicker);

    // 다크모드 변경 감지 → 차트 재렌더 (활성 종목 있을 때만)
    new MutationObserver(() => {
      if (currentTicker) renderChart(currentTicker);
    }).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
