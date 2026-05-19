// Watchlist 표 정렬 — '종목', '분위기' 컬럼만 sortable. '한 줄' 은 X.
(function () {
  const MOOD_RANK = { '🟢': 1, '🟡': 2, '🔴': 3, '—': 4 };

  // 정렬 가능한 헤더만 화살표 + 핸들러 (한 줄 / 그 달 주요 이벤트 같은 free text 는 제외)
  const SORTABLE_HEADERS = new Set(['종목', '분위기']);

  // Lucide SVG icons
  const SVG_INACTIVE = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/></svg>';
  const SVG_ASC      = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>';
  const SVG_DESC     = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>';

  function getTickerSortKey(td) {
    const ko = td.querySelector('.ticker-text__ko');
    if (ko) return ko.textContent.trim();
    return (td.textContent || '').trim();
  }

  function getMoodSortKey(td) {
    const text = (td.textContent || '').trim();
    for (const emoji of Object.keys(MOOD_RANK)) {
      if (text.includes(emoji)) return MOOD_RANK[emoji];
    }
    return 99;
  }

  function sortRows(tbody, colIdx, direction, getKey) {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
      const ka = getKey(a.children[colIdx]);
      const kb = getKey(b.children[colIdx]);
      if (typeof ka === 'number' && typeof kb === 'number') {
        return direction === 'asc' ? ka - kb : kb - ka;
      }
      const cmp = String(ka).localeCompare(String(kb), 'ko');
      return direction === 'asc' ? cmp : -cmp;
    });
    rows.forEach(r => tbody.appendChild(r));
  }

  function updateArrows(ths, activeIdx, direction) {
    ths.forEach((th, i) => {
      const arrow = th.querySelector('.sort-arrow');
      if (!arrow) return;
      if (i === activeIdx) {
        arrow.innerHTML = direction === 'asc' ? SVG_ASC : SVG_DESC;
        arrow.classList.add('is-active');
      } else {
        arrow.innerHTML = SVG_INACTIVE;
        arrow.classList.remove('is-active');
      }
    });
  }

  function makeSortable(table) {
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    if (!thead || !tbody) return;

    const ths = Array.from(thead.querySelectorAll('th'));
    const headers = ths.map(t => (t.textContent || '').trim());
    if (headers[0] !== '종목') return; // watchlist 표만

    // 정렬 가능한 컬럼에만 아이콘 + 클릭
    const sortableIdx = ths.map((_, i) => SORTABLE_HEADERS.has(headers[i]) ? i : -1).filter(i => i !== -1);

    sortableIdx.forEach(idx => {
      const th = ths[idx];
      th.style.cursor = 'pointer';
      th.style.userSelect = 'none';
      const arrow = document.createElement('span');
      arrow.className = 'sort-arrow';
      arrow.innerHTML = SVG_INACTIVE;
      arrow.setAttribute('aria-hidden', 'true');
      th.appendChild(arrow);
    });

    let activeIdx = -1;
    let direction = 'asc';

    sortableIdx.forEach(idx => {
      ths[idx].addEventListener('click', () => {
        if (activeIdx === idx) {
          direction = direction === 'asc' ? 'desc' : 'asc';
        } else {
          activeIdx = idx;
          direction = 'asc';
        }
        const getKey = idx === 0 ? getTickerSortKey : getMoodSortKey;
        sortRows(tbody, idx, direction, getKey);
        updateArrows(ths, activeIdx, direction);
      });
    });
  }

  function init() {
    const tables = document.querySelectorAll('article table, .post-content table, main table');
    tables.forEach(makeSortable);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
