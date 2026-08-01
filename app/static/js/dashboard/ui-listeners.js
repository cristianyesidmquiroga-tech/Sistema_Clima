// dashboard/ui-listeners.js — tabs, filtros, toggles de unidad/hora, popovers

document.querySelectorAll('.gw-tab').forEach(btn => {
  btn.addEventListener('click', e => {
    if (!puedeClickear('tab-chart')) return;
    document.querySelectorAll('.gw-tab').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    currentTab = e.target.getAttribute('data-target');
    renderMainChart();
  });
});

document.querySelectorAll('.gw-filter-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    if (!puedeClickear('filtro-historico')) return;
    document.querySelectorAll('.gw-filter-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    historyTipo = e.target.getAttribute('data-tipo');
    fetchAnalisisHistorico();
  });
});

// Clic en °C (inline en la temperatura grande)
const unitCEl = document.getElementById('unitC');
const unitFEl = document.getElementById('unitF');
if (unitCEl) unitCEl.addEventListener('click', () => switchTempUnit('C'));
if (unitFEl) unitFEl.addEventListener('click', () => switchTempUnit('F'));

// También los botones del header si existen
document.querySelectorAll('#tempToggle .gw-toggle-btn').forEach(btn => {
  btn.addEventListener('click', e => switchTempUnit(e.target.getAttribute('data-unit')));
});

function switchTempUnit(unit) {
  tempUnit = unit;
  localStorage.setItem('tempUnit', tempUnit);
  if (unitCEl) unitCEl.classList.toggle('active', unit === 'C');
  if (unitFEl) unitFEl.classList.toggle('active', unit === 'F');
  document.querySelectorAll('#tempToggle .gw-toggle-btn').forEach(b =>
    b.classList.toggle('active', b.getAttribute('data-unit') === unit)
  );
  if (lastRawData) renderRealTime(lastRawData);
  renderMainChart();
  fetchForecast();
  fetchAnalisisHistorico();
  fetchResumenSemana();
}

// Clic en el reloj (inline) para cambiar formato de hora
const clockEl = document.getElementById('gwClock');
if (clockEl) clockEl.addEventListener('click', () => {
  timeFmt = timeFmt === '24' ? '12' : '24';
  localStorage.setItem('timeFmt', timeFmt);
  document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(b =>
    b.classList.toggle('active', b.getAttribute('data-fmt') === timeFmt)
  );
  updateClock();
  renderMainChart();
  fetchForecast();
});

// También los botones del header si existen
document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    timeFmt = e.target.getAttribute('data-fmt');
    localStorage.setItem('timeFmt', timeFmt);
    updateClock();
    renderMainChart();
    fetchForecast();
  });
});

function applyStoredPrefs() {
  document.querySelectorAll('#tempToggle .gw-toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-unit') === tempUnit);
  });
  document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-fmt') === timeFmt);
  });
  const unitCEl2 = document.getElementById('unitC');
  const unitFEl2 = document.getElementById('unitF');
  if (unitCEl2) unitCEl2.classList.toggle('active', tempUnit === 'C');
  if (unitFEl2) unitFEl2.classList.toggle('active', tempUnit === 'F');
}

// ─── POPOVER INFO ─────────────────────────────────────────────
document.querySelectorAll('.gw-info-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const wasActive = btn.classList.contains('active');
    document.querySelectorAll('.gw-info-btn.active').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.gw-info-popover.show').forEach(p => p.classList.remove('show'));
    if (!wasActive) {
      btn.classList.add('active');
      btn.closest('.gw-extra-card').querySelector('.gw-info-popover').classList.add('show');
    }
  });
});
document.addEventListener('click', () => {
  document.querySelectorAll('.gw-info-btn.active').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.gw-info-popover.show').forEach(p => p.classList.remove('show'));
});
