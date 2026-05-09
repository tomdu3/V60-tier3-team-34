import { cancelOrder, getTradeHistory } from '../api.js';
import { escapeAttribute, escapeHtml, fmt } from '../formatters.js';
import { state } from '../state.js';

let refreshAccountData = async () => {};
let setTradePending = () => {};
let showTradeMessage = () => {};

export function initTradeHistory(options = {}) {
  refreshAccountData = options.refreshAccountData || refreshAccountData;
  setTradePending = options.setTradePending || setTradePending;
  showTradeMessage = options.showTradeMessage || showTradeMessage;
  document.querySelectorAll('[data-trade-filter]').forEach((button) => {
    button.addEventListener('click', () => filterTrades(button.dataset.tradeFilter));
  });
  document.getElementById('trade-history-body')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-cancel-order]');
    if (!button) return;
    cancelOpenOrder(button.dataset.orderId, button.dataset.ticker);
  });
}

export async function loadTradeHistory() {
  try {
    state.allTrades = await getTradeHistory(50);
    renderTrades();
  } catch (e) {
    console.error('Trade history error:', e);
    state.allTrades = [];
    renderTrades();
  }
}

export function filterTrades(status) {
  state.currentFilter = status;
  document.querySelectorAll('[data-trade-filter]').forEach((el) => {
    el.className = 'pb-2 text-sm ' + (el.dataset.tradeFilter === status ? 'tab-active' : 'text-gray-500 hover:text-white');
  });
  renderTrades();
}

function renderTrades() {
  const trades = state.currentFilter === 'All' ? state.allTrades : state.allTrades.filter(t => t.status === state.currentFilter);
  const statusClass = { FILLED: 'badge-filled', NEW: 'badge-pending', PENDING: 'badge-pending', CANCELED: 'badge-cancelled' };
  const tbody = document.getElementById('trade-history-body');
  tbody.innerHTML = trades.length === 0
    ? `<tr><td colspan="7" class="py-6 text-center text-xs text-gray-600">No trades found</td></tr>`
    : trades.map((t) => {
      const canCancel = t.status === 'NEW' && t.id;
      const cancelButton = canCancel
        ? `<button data-cancel-order data-order-id="${escapeAttribute(t.id)}" data-ticker="${escapeAttribute(t.ticker)}" class="px-2 py-1 rounded text-xs font-medium bg-red-900 hover:bg-red-800 text-red-300 transition">Cancel</button>`
        : '<span class="text-xs text-gray-600">—</span>';
      return `<tr class="text-sm hover:bg-gray-800 transition">
        <td class="py-2.5 font-mono font-bold text-white">${escapeHtml(t.ticker)}</td>
        <td class="py-2.5"><span class="px-2 py-0.5 rounded text-xs font-medium ${t.side === 'BUY' ? 'badge-buy' : 'badge-sell'}">${escapeHtml(t.side)}</span></td>
        <td class="py-2.5"><span class="px-2 py-0.5 rounded text-xs ${statusClass[t.status] || ''}">${escapeHtml(t.status)}</span></td>
        <td class="py-2.5 text-right text-gray-300">${escapeHtml(t.qty)}</td>
        <td class="py-2.5 text-right text-gray-300">${fmt(t.price)}</td>
        <td class="py-2.5 text-right text-gray-500 text-xs">${escapeHtml(t.time)}</td>
        <td class="py-2.5 text-right">${cancelButton}</td>
      </tr>`;
    }).join('');
}

async function cancelOpenOrder(orderId, ticker) {
  if (state.tradeRequestPending) return;
  if (!confirm('Cancel open order for ' + ticker + '?')) return;
  setTradePending(true);
  try {
    const d = await cancelOrder(orderId);
    showTradeMessage(d.message || 'Order cancel submitted.');
    await refreshAccountData();
  } catch (e) {
    console.error('Cancel order error:', e);
    showTradeMessage(e.message, true);
  } finally {
    setTradePending(false);
  }
}
