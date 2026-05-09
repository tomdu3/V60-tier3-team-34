import { getAccountStats } from '../api.js';
import { fmt } from '../formatters.js';

export async function loadStats() {
  try {
    const d = await getAccountStats();
    document.getElementById('stat-equity').textContent = fmt(d.total_equity);
    const pnlEl = document.getElementById('stat-pnl');
    pnlEl.textContent = fmt(d.daily_pnl);
    pnlEl.className = 'text-xl font-bold ' + (d.daily_pnl >= 0 ? 'text-green-400' : 'text-red-400');
    document.getElementById('stat-pnl-pct').textContent = (d.daily_pnl >= 0 ? '+' : '') + d.daily_pnl_pct.toFixed(2) + '% today';
    document.getElementById('stat-cash').textContent = fmt(d.cash_balance);
    document.getElementById('stat-winrate').textContent = d.win_rate.toFixed(1) + '%';
  } catch (e) {
    console.error('Stats error:', e);
    document.getElementById('stat-equity').textContent = '—';
    document.getElementById('stat-pnl').textContent = '—';
    document.getElementById('stat-pnl-pct').textContent = e.message;
    document.getElementById('stat-cash').textContent = '—';
    document.getElementById('stat-winrate').textContent = '—';
  }
}
