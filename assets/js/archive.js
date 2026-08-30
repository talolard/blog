const rows = [...document.querySelectorAll('[data-archive-row]')];
const groups = [...document.querySelectorAll('[data-archive-year]')];
const buttons = [...document.querySelectorAll('.filter-button[data-thread]')];
const search = document.querySelector('[data-archive-search]');
const result = document.querySelector('[data-archive-result]');

if (rows.length && search instanceof HTMLInputElement && result instanceof HTMLElement) {
  let activeThread = new URL(window.location.href).searchParams.get('thread') || 'all';

  const applyFilters = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const row of rows) {
      const threadMatches = activeThread === 'all' || row.dataset.thread === activeThread;
      const searchMatches = !query || (row.dataset.search || '').includes(query);
      row.hidden = !(threadMatches && searchMatches);
      if (!row.hidden) visible += 1;
    }
    for (const group of groups) {
      group.hidden = !group.querySelector('[data-archive-row]:not([hidden])');
    }
    result.textContent = `${visible} ${visible === 1 ? 'entry' : 'entries'}`;
  };

  for (const button of buttons) {
    if (!(button instanceof HTMLButtonElement)) continue;
    const selected = button.dataset.thread === activeThread;
    button.classList.toggle('is-active', selected);
    button.setAttribute('aria-pressed', String(selected));
    button.addEventListener('click', () => {
      activeThread = button.dataset.thread || 'all';
      for (const candidate of buttons) {
        const pressed = candidate === button;
        candidate.classList.toggle('is-active', pressed);
        candidate.setAttribute('aria-pressed', String(pressed));
      }
      applyFilters();
    });
  }
  search.addEventListener('input', applyFilters);
  applyFilters();
}
