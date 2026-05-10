import { getAccountEquity } from '../api.js';
import { fmt } from '../formatters.js';
import { state } from '../state.js';

export function initEquityChart() {
  document.querySelectorAll('[data-chart-days]').forEach((button) => {
    button.addEventListener('click', () => loadChart(Number(button.dataset.chartDays)));
  });
  document.querySelectorAll('[data-chart-toggle]').forEach((button) => {
    button.addEventListener('click', toggleChartExpand);
  });
}

export function toggleChartExpand() {
  state.chartExpanded = !state.chartExpanded;
  const modal = document.getElementById('chart-modal');
  if (state.chartExpanded) {
    modal.classList.remove('hidden');
    setTimeout(() => { loadChartExpanded(state.currentChartDays); }, 100);
  } else {
    modal.classList.add('hidden');
  }
}

function setChartRangeButtons(days) {
  ['30', '60', '90'].forEach((d) => {
    const active = Number(d) === Number(days);
    const className = 'px-3 py-1 text-xs rounded-lg ' + (active ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600');
    const regularButton = document.getElementById('btn-' + d);
    const expandedButton = document.getElementById('btn-' + d + '-exp');
    if (regularButton) regularButton.className = className;
    if (expandedButton) expandedButton.className = className;
  });
}

function renderChange(data, targetId) {
  const first = data.values[0];
  const last = data.values[data.values.length - 1];
  const change = last - first;
  const changePct = ((change / first) * 100).toFixed(2);
  const isPositive = change >= 0;
  document.getElementById(targetId).innerHTML = `<span class="${isPositive ? 'text-green-400' : 'text-red-400'}">${isPositive ? '+' : ''}${fmt(change)} (${changePct}%)</span>`;
}

function createEquityChart(canvasId, data) {
  const first = data.values[0];
  const last = data.values[data.values.length - 1];
  const change = last - first;
  const isPositive = change >= 0;
  const color = isPositive ? '#34d399' : '#f87171';
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  const existingChart = canvasId === 'equityChart' ? state.equityChart : state.equityChartExpanded;
  if (existingChart) existingChart.destroy();
  return new window.Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.values,
        borderColor: color,
        backgroundColor: color + '22',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: canvasId === 'equityChart',
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#1e2330' }, ticks: { color: '#6b7280', maxTicksLimit: 8 } },
        y: { grid: { color: '#1e2330' }, ticks: { color: '#6b7280', callback: v => '$' + (v / 1000).toFixed(0) + 'k' } }
      }
    }
  });
}

export async function loadChart(days) {
  state.currentChartDays = days;
  setChartRangeButtons(days);
  try {
    const data = await getAccountEquity(days);
    renderChange(data, 'equity-change');
    if (document.getElementById('equity-change-expanded')) {
      renderChange(data, 'equity-change-expanded');
    }
    state.equityChart = createEquityChart('equityChart', data);
    if (state.chartExpanded) {
      state.equityChartExpanded = createEquityChart('equityChartExpanded', data);
    }
  } catch (e) {
    console.error('Chart error:', e);
    document.getElementById('equity-change').textContent = e.message;
  }
}

export async function loadChartExpanded(days) {
  try {
    const data = await getAccountEquity(days);
    renderChange(data, 'equity-change-expanded');
    state.equityChartExpanded = createEquityChart('equityChartExpanded', data);
  } catch (e) {
    console.error('Expanded chart error:', e);
    document.getElementById('equity-change-expanded').textContent = e.message;
  }
}
