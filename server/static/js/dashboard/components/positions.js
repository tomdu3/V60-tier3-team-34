import { closeAllPositions as closeAllPositionsRequest, closePosition as closePositionRequest, getPositions } from '../api.js';
import { escapeAttribute, escapeHtml, fmt } from '../formatters.js';
import { envLabel, state } from '../state.js';

let refreshAccountData = async () => {};
let setTradePending = () => {};
let showTradeMessage = () => {};

export function initPositions(options = {}) {
  refreshAccountData = options.refreshAccountData || refreshAccountData;
  setTradePending = options.setTradePending || setTradePending;
  showTradeMessage = options.showTradeMessage || showTradeMessage;
  document.getElementById('close-all-button')?.addEventListener('click', closeAllPositions);
  document.getElementById('positions-list')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-close-position]');
    if (!button) return;
    closePosition(button.dataset.ticker);
  });
  document.getElementById('auto-positions-list')?.addEventListener('click', (event) => {
    const takeProfitButton = event.target.closest('[data-take-profit-position]');
    if (takeProfitButton) {
      takeProfitPosition(takeProfitButton.dataset.ticker);
      return;
    }
    const dismissButton = event.target.closest('[data-dismiss-position]');
    if (dismissButton) loadPositions();
  });
}

export async function loadPositions() {
  try {
    const positions = await getPositions();
    renderPositions(positions);
    renderAutoPositions(positions);
  } catch (e) {
    console.error('Positions error:', e);
    document.getElementById('positions-list').innerHTML = '<p class="text-xs text-red-400 text-center">' + escapeHtml(e.message) + '</p>';
    document.getElementById('auto-positions-list').innerHTML = '<p class="text-xs text-red-400 text-center">' + escapeHtml(e.message) + '</p>';
  }
}

function renderPositions(positions) {
  const list = document.getElementById('positions-list');
  list.innerHTML = positions.length === 0
    ? '<p class="text-xs text-gray-600 text-center">No open positions</p>'
    : positions.map((p) => {
      const isPos = p.pnl >= 0;
      return `<div class="rounded-lg border border-gray-700 p-3" style="background:#0f1117">
        <div class="flex items-center justify-between mb-2">
          <span class="font-mono font-bold text-white">${escapeHtml(p.ticker)}</span>
          <span class="text-xs px-2 py-0.5 rounded font-medium ${isPos ? 'badge-buy' : 'badge-sell'}">${isPos ? '+' : ''}${Number(p.pnl_pct).toFixed(2)}%</span>
        </div>
        <div class="grid grid-cols-2 gap-1 text-xs text-gray-400 mb-2">
          <span>${escapeHtml(p.shares)} shares</span>
          <span class="text-right">${isPos ? '+' : ''}${fmt(p.pnl)}</span>
          <span>Avg ${fmt(p.avg_price)}</span>
          <span class="text-right">Mkt ${fmt(p.market_price)}</span>
        </div>
        <button data-close-position data-ticker="${escapeAttribute(p.ticker)}" class="w-full py-1.5 rounded text-xs font-medium bg-red-900 hover:bg-red-800 text-red-300 transition">
          Close Position
        </button>
      </div>`;
    }).join('');
}

function renderAutoPositions(positions) {
  const autoList = document.getElementById('auto-positions-list');
  autoList.innerHTML = positions.length === 0
    ? '<p class="text-xs text-gray-600 text-center">No open positions</p>'
    : positions.map((p) => {
      const isPos = p.pnl >= 0;
      return `<div class="rounded-lg border border-gray-700 p-3 flex flex-col gap-2" style="background:#13161f">
        <div class="flex items-center justify-between">
          <span class="font-mono font-bold text-sm text-white">${escapeHtml(p.ticker)}</span>
          <span class="text-xs font-medium ${isPos ? 'text-green-400' : 'text-red-400'}">${isPos ? '+' : ''}${Number(p.pnl_pct).toFixed(2)}%</span>
        </div>
        <p class="text-xs text-gray-500">${escapeHtml(p.shares)} shares &middot; P&L: <span class="${isPos ? 'text-green-400' : 'text-red-400'}">${isPos ? '+' : ''}${fmt(p.pnl)}</span></p>
        <div class="grid grid-cols-2 gap-2">
          <button data-take-profit-position data-ticker="${escapeAttribute(p.ticker)}" class="py-1.5 rounded text-xs font-medium bg-green-900 hover:bg-green-800 text-green-300 transition">
            Take Profit
          </button>
          <button data-dismiss-position data-ticker="${escapeAttribute(p.ticker)}" class="py-1.5 rounded text-xs font-medium bg-gray-700 hover:bg-gray-600 text-gray-300 transition">
            Dismiss
          </button>
        </div>
      </div>`;
    }).join('');
}

async function closePosition(ticker) {
  if (state.tradeRequestPending) return;
  if (!confirm('Close position for ' + ticker + '?')) return;
  setTradePending(true);
  try {
    const d = await closePositionRequest(ticker);
    showTradeMessage(d.message || 'Position close submitted.');
    await refreshAccountData();
  } catch (e) {
    console.error('Close error:', e);
    showTradeMessage(e.message, true);
  } finally {
    setTradePending(false);
  }
}

async function closeAllPositions() {
  if (state.tradeRequestPending) return;
  if (!confirm('Close all open positions in ' + envLabel() + '?')) return;
  setTradePending(true);
  try {
    const d = await closeAllPositionsRequest();
    showTradeMessage(d.message || 'Close-all request submitted.');
    await refreshAccountData();
  } catch (e) {
    console.error('Close all error:', e);
    showTradeMessage(e.message, true);
  } finally {
    setTradePending(false);
  }
}

async function takeProfitPosition(ticker) {
  if (state.tradeRequestPending) return;
  if (!confirm('Take profit on ' + ticker + '?')) return;
  setTradePending(true);
  try {
    const d = await closePositionRequest(ticker, 'take_profit');
    showTradeMessage(d.message || 'Take-profit close submitted.');
    await refreshAccountData();
  } catch (e) {
    console.error('Take profit error:', e);
    showTradeMessage(e.message, true);
  } finally {
    setTradePending(false);
  }
}
