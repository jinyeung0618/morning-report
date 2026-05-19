// Watchlist 표 정렬 — 헤더 클릭 시 정렬, 화살표 표시
// 첫 컬럼 헤더가 '종목' 인 표만 sortable 로 인식
(function () {
  // 분위기 이모지 순위 (좋음 → 나쁨)
  const MOOD_RANK = { '🟢': 1, '🟡': 2, '🔴': 3, '—': 4 };

  function getCellText(td) {
    return (td.textContent || '').trim();
  }

  // 종목 컬럼: 한글명 (있으면) > ticker symbol
  function getTickerSortKey(td) {
    const ko = td.querySelector('.ticker-text__ko');
    if (ko) return ko.textContent.trim();
    return getCellText(td);
  }

  // 분위기 컬럼: 이모지 추출 후 순위로 변환
  function getMoodSortKey(td) {
    const text = getCellText(td);
    for (const emoji of Object.keys(MOOD_RANK)) {
      if (text.includes(emoji)) return MOOD_RANK[emoji];
    }
    return 99; // unknown
  }

  // 일반 셀: 텍스트 비교
  function getDefaultSortKey(td) {
    return getCellText(td);
  }

  function sortRows(tbody, colIdx, direction, getKey) {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
      const ka = getKey(a.children[colIdx]);
      const kb = getKey(b.children[colIdx]);
      if (typeof ka === 'number' && typeof kb === 'number') {
        return direction === 'asc' ? ka - kb : kb - ka;
      }
      // 한글·영문 모두 localeCompare ('ko' 가나다 + 영문 처리)
      const cmp = String(ka).localeCompare(String(kb), 'ko');
      return direction === 'asc' ? cmp : -cmp;
    });
    rows.forEach(r => tbody.appendChild(r));
  }

  function updateArrows(thead, activeIdx, direction) {
    const ths = thead.querySelectorAll('th');
    ths.forEach((th, i) => {
      const arrow = th.querySelector('.sort-arrow');
      if (!arrow) return;
      if (i === activeIdx) {
        arrow.textContent = direction === 'asc' ? '▲' : '▼';
        arrow.classList.add('is-active');
      } else {
        arrow.textContent = '↕';
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

    // 각 th 에 sort 아이콘 + cursor + click handler
    ths.forEach((th, idx) => {
      th.style.cursor = 'pointer';
      th.style.userSelect = 'none';
      const arrow = document.createElement('span');
      arrow.className = 'sort-arrow';
      arrow.textContent = '↕';
      arrow.setAttribute('aria-hidden', 'true');
      th.appendChild(arrow);
    });

    // 현재 정렬 상태
    let activeIdx = -1;
    let direction = 'asc';

    ths.forEach((th, idx) => {
      th.addEventListener('click', () => {
        if (activeIdx === idx) {
          direction = direction === 'asc' ? 'desc' : 'asc';
        } else {
          activeIdx = idx;
          direction = 'asc';
        }

        const getKey =
          idx === 0 ? getTickerSortKey :
          idx === 1 ? getMoodSortKey :
          getDefaultSortKey;

        sortRows(tbody, idx, direction, getKey);
        updateArrows(thead, activeIdx, direction);
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
