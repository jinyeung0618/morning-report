// 재테크 — 종목 통계 차트 (Custom SVG, 디자인 시스템 100% 적용)
// 종속성 없음. 종목 추가 시 STOCKS 객체에 항목 추가.

(function () {
  // ---- 데이터 ----
  const STOCKS = {
    AAPL: {
      label: 'AAPL · Apple',
      iconSlug: 'apple', iconColor: '000000',
      nameKo: '애플',
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

    TSLA: {
      label: 'TSLA · Tesla',
      iconSlug: 'tesla', iconColor: 'cc0000',
      nameKo: '테슬라',
      region: 'us',
      currency: '$',
      refs: [
        ['2010-06', 1.27], ['2013-04', 5.00], ['2014-09', 19.00],
        ['2016-02', 9.00], ['2017-09', 25.00], ['2019-06', 14.00],
        ['2020-03', 25.00], ['2021-11', 410.00], ['2022-12', 108.00],
        ['2023-07', 290.00], ['2024-04', 145.00], ['2025-01', 400.00],
        ['2026-05', 428.00],
      ],
      events: [
        { date: '2010-06', title: 'IPO — Roadster 시기 직상장' },
        { date: '2014-09', title: 'Model S 슈퍼사이클 1차 정점' },
        { date: '2016-02', title: 'Model 3 발표 직전 저점' },
        { date: '2020-03', title: 'COVID 저점 — 이후 폭등 시작' },
        { date: '2021-11', title: '시총 1조 달러 + Hertz 대량 주문 정점' },
        { date: '2022-12', title: '금리 인상 + 머스크 트위터 인수로 저점' },
        { date: '2024-04', title: '1Q 인도량 미달 — 단기 저점' },
        { date: '2025-01', title: '트럼프 당선 효과로 신고가' },
      ],
    },

    NVDA: {
      label: 'NVDA · NVIDIA',
      iconSlug: 'nvidia', iconColor: '76b900',
      nameKo: '엔비디아',
      region: 'us',
      currency: '$',
      refs: [
        ['2000-03', 1.00], ['2002-10', 0.20], ['2007-10', 1.00],
        ['2008-11', 0.20], ['2015-01', 0.50], ['2016-01', 0.80],
        ['2018-09', 7.00], ['2018-12', 3.30], ['2020-03', 5.50],
        ['2021-11', 33.00], ['2022-10', 11.00], ['2023-01', 14.00],
        ['2024-06', 130.00], ['2025-01', 140.00], ['2026-05', 215.00],
      ],
      events: [
        { date: '2000-03', title: '닷컴 버블 정점' },
        { date: '2008-11', title: '금융위기 저점' },
        { date: '2016-01', title: '딥러닝 부상 — AI 시대 시동' },
        { date: '2018-09', title: '암호화폐 GPU 수요 정점' },
        { date: '2020-03', title: 'COVID 저점' },
        { date: '2022-11', title: 'ChatGPT 출시 — AI 부상 시작' },
        { date: '2024-06', title: '시총 3조 달러 — AI 칩 슈퍼사이클' },
        { date: '2025-01', title: 'DeepSeek 충격으로 일시 조정' },
      ],
    },

    UNH: {
      label: 'UNH · UnitedHealth',
      badge: { cls: 'unh', text: 'UNH' },
      nameKo: '유나이티드헬스',
      region: 'us',
      currency: '$',
      refs: [
        ['1990-01', 0.50], ['2000-01', 5.00], ['2008-03', 35.00],
        ['2008-11', 17.00], ['2015-07', 125.00], ['2020-03', 200.00],
        ['2022-01', 510.00], ['2023-07', 480.00], ['2024-04', 440.00],
        ['2025-04', 310.00], ['2026-05', 384.00],
      ],
      events: [
        { date: '2008-11', title: '금융위기 저점' },
        { date: '2015-07', title: 'ACA(오바마케어) 수혜 — 장기 상승 시작' },
        { date: '2020-03', title: 'COVID 저점' },
        { date: '2022-01', title: '사상 최고 — 이후 헬스케어 섹터 조정' },
        { date: '2024-04', title: 'Change Healthcare 사이버 공격' },
        { date: '2025-04', title: 'CEO 피살 + 규제 우려로 저점' },
        { date: '2026-05', title: '사전승인 60% 폐지 발표 + 반등' },
      ],
    },

    PLTR: {
      label: 'PLTR · Palantir',
      iconSlug: 'palantir', iconColor: '000000',
      nameKo: '팔란티어',
      region: 'us',
      currency: '$',
      refs: [
        ['2020-09', 10.00], ['2021-01', 35.00], ['2022-12', 6.00],
        ['2023-05', 13.00], ['2024-01', 17.00], ['2024-12', 80.00],
        ['2025-02', 125.00], ['2025-05', 100.00], ['2026-05', 100.00],
      ],
      events: [
        { date: '2020-09', title: '직상장 (Direct Listing)' },
        { date: '2021-01', title: '단기 정점 — 메스 마니아 흐름' },
        { date: '2022-12', title: '인플레 + 금리로 저점' },
        { date: '2023-05', title: 'AIP 출시 — AI 모멘텀 시작' },
        { date: '2024-12', title: '펜타곤 + 상업 계약 본격화' },
        { date: '2025-02', title: '사상 최고 — 이후 밸류에이션 부담' },
      ],
    },

    CEG: {
      label: 'CEG · Constellation Energy',
      badge: { cls: 'ceg', text: 'CEG' },
      nameKo: '컨스텔레이션',
      region: 'us',
      currency: '$',
      refs: [
        ['2022-02', 50.00], ['2022-12', 90.00], ['2023-10', 115.00],
        ['2024-03', 235.00], ['2024-09', 270.00], ['2025-02', 350.00],
        ['2026-03', 300.00], ['2026-05', 290.00],
      ],
      events: [
        { date: '2022-02', title: 'Exelon 에서 분사 상장' },
        { date: '2024-03', title: 'AI 데이터센터 전력 수요 본격 부상' },
        { date: '2024-09', title: 'MS와 Three Mile Island 원전 재가동 계약' },
        { date: '2025-02', title: '사상 최고' },
        { date: '2026-03', title: '2026 가이던스 하향 — 단기 조정' },
      ],
    },

    // 국내 ETF
    '487230': {
      label: '487230 · 미국AI전력핵심인프라',
      badge: { cls: 'kodex', text: '230' },
      nameKo: 'KODEX 미국AI전력핵심인프라',
      region: 'kr',
      currency: '₩',
      refs: [
        ['2024-07', 10000], ['2024-10', 11200], ['2024-12', 12000],
        ['2025-04', 10500], ['2025-09', 16000], ['2026-01', 18120],
        ['2026-05', 18500],
      ],
      events: [
        { date: '2024-07', title: 'KODEX 상장 — 미국 AI 전력 인프라 (GE Vernova·Vertiv 중심)' },
        { date: '2025-04', title: '단기 저점' },
        { date: '2025-09', title: 'AI 데이터센터 전력 수요 폭증으로 반등' },
        { date: '2026-01', title: '52주 신고가권 진입' },
      ],
    },

    '487240': {
      label: '487240 · AI전력핵심설비',
      badge: { cls: 'kodex', text: '240' },
      nameKo: 'KODEX AI전력핵심설비',
      region: 'kr',
      currency: '₩',
      refs: [
        ['2024-07', 10000], ['2024-12', 12000], ['2025-03', 14000],
        ['2025-09', 25000], ['2025-12', 40000], ['2026-03', 55000],
        ['2026-05', 61575],
      ],
      events: [
        { date: '2024-07', title: 'KODEX 상장 — 국내 AI 전력 설비 (LS ELECTRIC·효성중공업 중심)' },
        { date: '2025-09', title: 'AI 전력 설비 수요 본격화' },
        { date: '2025-12', title: '국내 AI 데이터센터 발주 가속' },
        { date: '2026-05', title: '52주 신고가 — 1년간 +498%' },
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

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // 스케일 (vanilla)
  function scaleLinear(domain, range) {
    const [d0, d1] = domain, [r0, r1] = range;
    return v => r0 + (v - d0) / (d1 - d0) * (r1 - r0);
  }
  function scaleLog(domain, range) {
    const [d0, d1] = domain, [r0, r1] = range;
    const ld0 = Math.log(d0), ld1 = Math.log(d1);
    return v => r0 + (Math.log(v) - ld0) / (ld1 - ld0) * (r1 - r0);
  }

  // Catmull-Rom → Cubic Bezier (부드러운 곡선)
  function smoothPath(pts) {
    if (!pts.length) return '';
    if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;
    let d = `M ${pts[0].x.toFixed(2)} ${pts[0].y.toFixed(2)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i - 1] || pts[i];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[i + 2] || p2;
      const c1x = p1.x + (p2.x - p0.x) / 6;
      const c1y = p1.y + (p2.y - p0.y) / 6;
      const c2x = p2.x - (p3.x - p1.x) / 6;
      const c2y = p2.y - (p3.y - p1.y) / 6;
      d += ` C ${c1x.toFixed(2)} ${c1y.toFixed(2)}, ${c2x.toFixed(2)} ${c2y.toFixed(2)}, ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`;
    }
    return d;
  }

  function svg(tag, attrs = {}) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    return el;
  }

  // ---- 상태 ----
  let currentTicker = 'AAPL';
  let resizeObs = null;
  const gradientId = 'chart-area-gradient-' + Math.random().toString(36).slice(2, 8);

  // ---- 차트 렌더 ----
  function renderChart(ticker) {
    const container = document.getElementById('stocksChart');
    if (!container) return;
    const svgEl = container.querySelector('.chart-svg');
    if (!svgEl) return;

    const stock = STOCKS[ticker];
    if (!stock) return;

    const data = expandToMonthly(stock.refs);
    const eventMap = {};
    (stock.events || []).forEach(e => { eventMap[e.date] = e.title; });

    const W = container.clientWidth;
    const H = container.clientHeight;
    if (W <= 0 || H <= 0) return;

    const pad = { top: 18, right: 48, bottom: 30, left: 12 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    // 토큰 → 실제 값
    const c = {
      line: cssVar('--color-primary') || '#0071E3',
      text: cssVar('--text-secondary') || '#636366',
      muted: cssVar('--text-tertiary') || '#AEAEB2',
      grid: cssVar('--border-color') || '#E8E8ED',
      bg: cssVar('--bg-secondary') || '#FAFAFA',
    };

    // 스케일
    const xScale = scaleLinear([0, data.length - 1], [pad.left, pad.left + plotW]);
    const yVals = data.map(d => d.value);
    const yMin = Math.min(...yVals);
    const yMax = Math.max(...yVals);
    const yDomain = [yMin * 0.7, yMax * 1.15];
    const yScale = scaleLog(yDomain, [pad.top + plotH, pad.top]);

    // 데이터 포인트
    const pts = data.map((d, i) => ({ x: xScale(i), y: yScale(d.value) }));

    // Y축 눈금 (주요 레벨만, USD~KRW 둘 다 커버)
    const allowedY = [
      0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500,
      1000, 2000, 5000, 10000, 20000, 50000, 100000,
    ];
    const yTicks = allowedY.filter(v => v >= yDomain[0] && v <= yDomain[1]);

    // X축 눈금 (균등 + 마지막)
    const total = data.length - 1;
    const desired = 7;
    const step = Math.max(1, Math.floor(total / (desired - 1)));
    const xTicks = [];
    for (let i = 0; i < total; i += step) {
      if (total - i < step * 0.6) break;
      xTicks.push(i);
    }
    xTicks.push(total);

    // SVG 초기화
    svgEl.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svgEl.setAttribute('preserveAspectRatio', 'none');
    svgEl.innerHTML = '';

    // defs (gradient)
    const defs = svg('defs');
    const grad = svg('linearGradient', { id: gradientId, x1: '0', y1: '0', x2: '0', y2: '1' });
    grad.appendChild(svg('stop', { offset: '0%', 'stop-color': c.line, 'stop-opacity': '0.18' }));
    grad.appendChild(svg('stop', { offset: '100%', 'stop-color': c.line, 'stop-opacity': '0' }));
    defs.appendChild(grad);
    svgEl.appendChild(defs);

    // 그리드 (수평선)
    const gGrid = svg('g');
    yTicks.forEach(v => {
      const y = yScale(v);
      gGrid.appendChild(svg('line', {
        x1: pad.left, x2: pad.left + plotW,
        y1: y, y2: y,
        stroke: c.grid, 'stroke-width': '1', 'stroke-dasharray': '2 4',
      }));
    });
    svgEl.appendChild(gGrid);

    // Area + Line
    const linePath = smoothPath(pts);
    const baseY = pad.top + plotH;
    const areaD = linePath + ` L ${pts[pts.length - 1].x.toFixed(2)} ${baseY} L ${pts[0].x.toFixed(2)} ${baseY} Z`;

    svgEl.appendChild(svg('path', { d: areaD, fill: `url(#${gradientId})`, stroke: 'none' }));
    svgEl.appendChild(svg('path', {
      d: linePath,
      fill: 'none', stroke: c.line, 'stroke-width': '2',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    }));

    // 변곡점 마커
    const gMarkers = svg('g');
    const eventPts = [];
    data.forEach((d, i) => {
      const ym = d.time.slice(0, 7);
      const title = eventMap[ym];
      if (!title) return;
      const x = pts[i].x, y = pts[i].y;
      // halo
      gMarkers.appendChild(svg('circle', {
        cx: x, cy: y, r: 9, fill: c.line, 'fill-opacity': '0.14',
      }));
      // dot with border
      gMarkers.appendChild(svg('circle', {
        cx: x, cy: y, r: 4.5, fill: c.line, stroke: c.bg, 'stroke-width': '2.5',
      }));
      eventPts.push({ x, y, date: ym, title, value: d.value });
    });
    svgEl.appendChild(gMarkers);

    // Y축 라벨 (우측)
    const formatPrice = (v) => v >= 1000
      ? stock.currency + v.toLocaleString('en-US')
      : stock.currency + v;

    const gY = svg('g');
    yTicks.forEach(v => {
      const t = svg('text', {
        x: pad.left + plotW + 10,
        y: yScale(v) + 4,
        fill: c.muted,
        'font-size': '11',
        'font-family': "'SF Mono', 'Fira Code', monospace",
      });
      t.textContent = formatPrice(v);
      gY.appendChild(t);
    });
    svgEl.appendChild(gY);

    // X축 라벨 (하단)
    const gX = svg('g');
    xTicks.forEach(i => {
      const t = svg('text', {
        x: pts[i].x,
        y: baseY + 20,
        fill: c.muted,
        'font-size': '11',
        'font-family': "'SF Mono', 'Fira Code', monospace",
        'text-anchor': 'middle',
      });
      t.textContent = data[i].time.slice(0, 4);
      gX.appendChild(t);
    });
    svgEl.appendChild(gX);

    // 호버 타깃 — 변곡점에만
    const tooltip = document.getElementById('chartTooltip');
    const gHover = svg('g');
    eventPts.forEach(ev => {
      const target = svg('circle', {
        cx: ev.x, cy: ev.y, r: 18,
        fill: 'transparent', style: 'cursor: pointer',
      });
      const show = () => showTooltip(tooltip, ev, container, stock);
      const hide = () => hideTooltip(tooltip);
      target.addEventListener('mouseenter', show);
      target.addEventListener('mouseleave', hide);
      target.addEventListener('touchstart', (e) => { e.preventDefault(); show(); });
      gHover.appendChild(target);
    });
    svgEl.appendChild(gHover);
  }

  function showTooltip(el, ev, container, stock) {
    if (!el) return;
    const priceStr = ev.value >= 1000
      ? stock.currency + Math.round(ev.value).toLocaleString('en-US')
      : stock.currency + ev.value.toFixed(2);
    el.innerHTML = `
      <div class="chart-tooltip__date">${ev.date}</div>
      <div class="chart-tooltip__price">${priceStr}</div>
      <div class="chart-tooltip__event">📌 ${escapeHtml(ev.title)}</div>
    `;
    el.style.opacity = '1';
    const rect = container.getBoundingClientRect();
    const tw = el.offsetWidth, th = el.offsetHeight;
    let left = ev.x - tw / 2;
    let top = ev.y - th - 14;
    left = Math.max(8, Math.min(rect.width - tw - 8, left));
    if (top < 8) top = ev.y + 22;
    el.style.left = left + 'px';
    el.style.top = top + 'px';
  }

  function hideTooltip(el) { if (el) el.style.opacity = '0'; }

  function clearChart() {
    const container = document.getElementById('stocksChart');
    if (!container) return;
    const svgEl = container.querySelector('.chart-svg');
    if (svgEl) svgEl.innerHTML = '';
    hideTooltip(document.getElementById('chartTooltip'));
    currentTicker = null;
    if (resizeObs) { resizeObs.disconnect(); resizeObs = null; }
  }

  function setStatsBodyVisible(visible) {
    document.querySelectorAll('.stats-chart-wrap, .stats-disclaimer, .stats-hint')
      .forEach(el => { el.style.display = visible ? '' : 'none'; });
  }

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
    const wrap = document.getElementById('statsTickers');
    if (!wrap) return;
    const visible = Object.entries(STOCKS).filter(([_, s]) => s.region === region).map(([k]) => k);
    if (!visible.length) {
      wrap.innerHTML = '<p class="chip-empty">아직 등록된 종목이 없습니다.</p>';
      clearChart();
      setStatsBodyVisible(false);
      return;
    }
    setStatsBodyVisible(true);
    wrap.innerHTML = visible.map((k, i) => {
      const s = STOCKS[k];
      const titleAttr = s.nameKo ? ` title="${s.nameKo}"` : '';
      let logo = '';
      if (s.iconSlug) {
        // simple-icons CDN SVG
        logo = `<span class="ticker-logo"${titleAttr}><img src="https://cdn.simpleicons.org/${s.iconSlug}/${s.iconColor || '000000'}" alt=""></span>`;
      } else if (s.badge) {
        // 텍스트 badge
        logo = `<span class="ticker-logo ticker-logo--badge ticker-logo--${s.badge.cls}"${titleAttr}>${s.badge.text}</span>`;
      }
      return `<button class="chip${i === 0 ? ' is-active' : ''}" data-ticker="${k}" type="button" role="tab">${logo}${escapeHtml(STOCKS[k].label)}</button>`;
    }).join('');
    selectTicker(visible[0]);
  }

  function attachResize(container) {
    if (resizeObs) resizeObs.disconnect();
    resizeObs = new ResizeObserver(() => {
      if (currentTicker && container.clientWidth > 0) renderChart(currentTicker);
    });
    resizeObs.observe(container);
  }

  // ---- 초기화 ----
  function init() {
    document.addEventListener('click', (e) => {
      const t = e.target.closest('[data-ticker]');
      if (t) selectTicker(t.dataset.ticker);
      const r = e.target.closest('[data-region]');
      if (r) selectRegion(r.dataset.region);
    });

    const container = document.getElementById('stocksChart');
    if (container && container.offsetParent !== null) {
      renderChart(currentTicker);
      attachResize(container);
    }

    window._statsRender = () => {
      if (currentTicker) {
        renderChart(currentTicker);
        const c = document.getElementById('stocksChart');
        if (c) attachResize(c);
      }
    };

    // 다크모드 재렌더
    new MutationObserver(() => {
      const c = document.getElementById('stocksChart');
      if (currentTicker && c && c.offsetParent !== null) renderChart(currentTicker);
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
