// 재테크 — 종목 통계 차트 (TradingView Lightweight Charts 기반)
// 종목 추가 시 STOCKS 객체에 항목 추가.

(function () {
  if (typeof LightweightCharts === 'undefined') return;

  // ---- 데이터 ----
  const STOCKS = {
    AAPL: {
      label: 'AAPL · Apple',
      region: 'us',
      currency: '$',
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
        { date: '1997-09', title: '잡스 복귀 — 부활의 시작 (저점)' },
        { date: '2000-03', title: '닷컴 버블 정점' },
        { date: '2002-09', title: '닷컴 버블 저점 — 회복 시작' },
        { date: '2007-06', title: 'iPhone 출시 — 슈퍼사이클 가속' },
        { date: '2008-12', title: '글로벌 금융위기 저점' },
        { date: '2012-09', title: '1차 정점 — 차세대 우려로 조정' },
        { date: '2018-10', title: '2차 정점 — 매출 둔화 우려' },
        { date: '2020-03', title: 'COVID-19 저점 — 빠른 V자 회복' },
        { date: '2022-01', title: '시총 3조 달러 정점' },
        { date: '2022-12', title: '인플레·금리 우려 저점' },
        { date: '2024-06', title: 'Apple Intelligence 발표' },
      ],
    },
  };

  // ---- 유틸 ----
  function expandToMonthly(refs) {
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
        result.push({ time: d.toISOString().slice(0, 10), value: Math.exp(lc) });
      }
    }
    const last = points[points.length - 1];
    result.push({ time: last.date.toISOString().slice(0, 10), value: last.close });
    return result;
  }

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function getThemeColors() {
    return {
      text: cssVar('--text-secondary') || '#636366',
      grid: cssVar('--border-color') || '#E8E8ED',
      gridSoft: cssVar('--bg-tertiary') || '#F5F5F7',
      line: cssVar('--color-primary') || '#0071E3',
      fillTop: 'rgba(0, 113, 227, 0.18)',
      fillBottom: 'rgba(0, 113, 227, 0.00)',
    };
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // ---- 차트 상태 ----
  let chart = null;
  let series = null;
  let currentTicker = 'AAPL';
  let currentEventMap = {};
  let tooltipEl = null;

  // ---- 차트 렌더 ----
  function renderChart(ticker) {
    const stock = STOCKS[ticker];
    if (!stock) return;
    const container = document.getElementById('stocksChart');
    if (!container) return;

    const data = expandToMonthly(stock.refs);
    const colors = getThemeColors();

    // 이벤트 룩업 (YYYY-MM 단위)
    currentEventMap = {};
    (stock.events || []).forEach(e => { currentEventMap[e.date] = e.title; });

    // 기존 차트 제거
    if (chart) {
      chart.remove();
      chart = null;
      series = null;
    }

    chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 300,
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: colors.text,
        fontSize: 11,
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Mono", monospace',
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: colors.gridSoft, style: 0 },
      },
      rightPriceScale: {
        mode: LightweightCharts.PriceScaleMode.Logarithmic,
        borderVisible: false,
        scaleMargins: { top: 0.1, bottom: 0.08 },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: false,
        secondsVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Magnet,
        vertLine: { color: colors.grid, width: 1, style: 2, labelVisible: false },
        horzLine: { color: colors.grid, width: 1, style: 2, labelVisible: false },
      },
      handleScale: { mouseWheel: true, pinch: true, axisPressedMouseMove: false },
      handleScroll: { mouseWheel: false, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
    });

    series = chart.addAreaSeries({
      lineColor: colors.line,
      topColor: colors.fillTop,
      bottomColor: colors.fillBottom,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      crosshairMarkerBorderColor: colors.line,
      crosshairMarkerBackgroundColor: cssVar('--bg-primary') || '#FFFFFF',
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    });

    series.setData(data);

    // 변곡점 마커
    series.setMarkers((stock.events || []).map(e => ({
      time: e.date + '-01',
      position: 'aboveBar',
      color: colors.line,
      shape: 'circle',
      size: 1.2,
    })));

    chart.timeScale().fitContent();

    // ---- 툴팁 ----
    tooltipEl = document.getElementById('chartTooltip');
    if (!tooltipEl) return;

    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time || !param.point) {
        tooltipEl.style.opacity = '0';
        return;
      }
      const ts = typeof param.time === 'string' ? param.time : '';
      const ym = ts.slice(0, 7); // YYYY-MM
      const eventTitle = currentEventMap[ym];

      const dataPoint = param.seriesData.get(series);
      if (!dataPoint) {
        tooltipEl.style.opacity = '0';
        return;
      }

      // 변곡점 근처에서만 툴팁 표시 (이벤트 dates만)
      if (!eventTitle) {
        tooltipEl.style.opacity = '0';
        return;
      }

      const price = stock.currency + dataPoint.value.toFixed(2);
      tooltipEl.innerHTML = `
        <div class="chart-tooltip__date">${escapeHtml(ym)}</div>
        <div class="chart-tooltip__price">${escapeHtml(price)}</div>
        <div class="chart-tooltip__event">📌 ${escapeHtml(eventTitle)}</div>
      `;
      tooltipEl.style.opacity = '1';

      // 위치 — 마커 위쪽에 떠 있게
      const rect = container.getBoundingClientRect();
      const tooltipW = tooltipEl.offsetWidth;
      const tooltipH = tooltipEl.offsetHeight;
      let left = param.point.x - tooltipW / 2;
      let top = param.point.y - tooltipH - 12;
      // boundary 클램프
      left = Math.max(8, Math.min(rect.width - tooltipW - 8, left));
      if (top < 8) top = param.point.y + 16;
      tooltipEl.style.left = left + 'px';
      tooltipEl.style.top = top + 'px';
    });

    // 리사이즈 대응
    const ro = new ResizeObserver(() => {
      if (chart && container.clientWidth > 0) {
        chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
      }
    });
    ro.observe(container);
    chart._ro = ro;
  }

  // ---- 빈 상태 / 가시성 ----
  function clearChart() {
    if (chart) {
      if (chart._ro) chart._ro.disconnect();
      chart.remove();
      chart = null;
      series = null;
    }
    if (tooltipEl) tooltipEl.style.opacity = '0';
    currentTicker = null;
  }

  function setStatsBodyVisible(visible) {
    document.querySelectorAll('.stats-chart-wrap, .stats-disclaimer, .stats-hint')
      .forEach(el => { el.style.display = visible ? '' : 'none'; });
  }

  // ---- 종목/지역 선택 ----
  function selectTicker(ticker) {
    currentTicker = ticker;
    document.querySelectorAll('[data-ticker]').forEach(b => {
      b.classList.toggle('is-active', b.dataset.ticker === ticker);
    });
    renderChart(ticker);
  }

  function selectRegion(region) {
    document.querySelectorAll('[data-region]').forEach(b => {
      b.classList.toggle('is-active', b.dataset.region === region);
    });
    const tickerWrap = document.getElementById('statsTickers');
    if (!tickerWrap) return;

    const visibleTickers = Object.entries(STOCKS)
      .filter(([_, s]) => s.region === region)
      .map(([key]) => key);

    if (visibleTickers.length === 0) {
      tickerWrap.innerHTML = '<p class="chip-empty">아직 등록된 종목이 없습니다.</p>';
      clearChart();
      setStatsBodyVisible(false);
      return;
    }

    setStatsBodyVisible(true);
    tickerWrap.innerHTML = visibleTickers.map((key, i) => `
      <button class="chip${i === 0 ? ' is-active' : ''}" data-ticker="${key}" type="button" role="tab">${escapeHtml(STOCKS[key].label)}</button>
    `).join('');
    selectTicker(visibleTickers[0]);
  }

  // ---- 초기화 ----
  function init() {
    // 이벤트 위임
    document.addEventListener('click', (e) => {
      const ticker = e.target.closest('[data-ticker]');
      if (ticker) selectTicker(ticker.dataset.ticker);
      const region = e.target.closest('[data-region]');
      if (region) selectRegion(region.dataset.region);
    });

    // 첫 렌더 — 컨테이너가 보이는 경우만
    const container = document.getElementById('stocksChart');
    if (container && container.offsetParent !== null) {
      renderChart(currentTicker);
    }

    // 탭 스위처에서 호출
    window._statsRender = () => {
      if (currentTicker) renderChart(currentTicker);
    };

    // 다크모드 변경 → 차트 재렌더
    new MutationObserver(() => {
      const c = document.getElementById('stocksChart');
      if (currentTicker && c && c.offsetParent !== null) renderChart(currentTicker);
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
