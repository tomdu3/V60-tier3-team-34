import { submitOrder } from '../api.js';
import { state } from '../state.js';

let refreshAccountData = async () => {};

export function initTradePanel(options = {}) {
  refreshAccountData = options.refreshAccountData || refreshAccountData;
  document.querySelectorAll('[data-mode]').forEach((button) => {
    button.addEventListener('click', () => setMode(button.dataset.mode));
  });
  document.querySelectorAll('[data-side]').forEach((button) => {
    button.addEventListener('click', () => setSide(button.dataset.side));
  });
  document.querySelectorAll('[data-order-type]').forEach((button) => {
    button.addEventListener('click', () => setOrderType(button.dataset.orderType));
  });
  document.getElementById('trade-confirm-button')?.addEventListener('click', confirmTrade);
  document.getElementById('trade-dismiss-button')?.addEventListener('click', dismissTrade);
  document.getElementById('auto-toggle')?.addEventListener('click', toggleAutoBot);
  document.getElementById('auto-save-button')?.addEventListener('click', saveAutoSettings);
}

export function setTradePending(isPending) {
  state.tradeRequestPending = isPending;
  const tradeConfirmButton = document.getElementById('trade-confirm-button');
  const closeAllButton = document.getElementById('close-all-button');
  if (tradeConfirmButton) {
    tradeConfirmButton.disabled = isPending;
    tradeConfirmButton.classList.toggle('opacity-60', isPending);
  }
  if (closeAllButton) {
    closeAllButton.disabled = isPending;
    closeAllButton.classList.toggle('opacity-60', isPending);
  }
}

export function showTradeMessage(message, isError = false) {
  const msg = document.getElementById('trade-msg');
  msg.textContent = message;
  msg.className = 'text-xs text-center mt-2 ' + (isError ? 'text-red-400' : 'text-green-400');
}

export function setMode(mode) {
  state.currentMode = mode;
  const isManual = mode === 'manual';
  document.getElementById('panel-manual').classList.toggle('hidden', !isManual);
  document.getElementById('panel-auto').classList.toggle('hidden', isManual);
  document.getElementById('mode-manual').className = 'py-2 rounded-lg text-sm font-medium transition ' + (isManual ? 'mode-tab-active' : 'mode-tab-inactive');
  document.getElementById('mode-auto').className = 'py-2 rounded-lg text-sm font-medium transition ' + (!isManual ? 'mode-tab-active' : 'mode-tab-inactive');
}

export function setSide(side) {
  state.tradeSide = side;
  document.getElementById('side-buy').className = 'py-2 rounded-lg text-sm font-medium ' + (side === 'BUY' ? 'bg-green-700 text-green-100' : 'bg-gray-700 text-gray-400');
  document.getElementById('side-sell').className = 'py-2 rounded-lg text-sm font-medium ' + (side === 'SELL' ? 'bg-red-700 text-red-100' : 'bg-gray-700 text-gray-400');
}

export function setOrderType(type) {
  state.tradeType = type;
  document.getElementById('type-market').className = 'py-2 rounded-lg text-sm ' + (type === 'Market' ? 'bg-blue-700 text-white' : 'bg-gray-700 text-gray-400');
  document.getElementById('type-limit').className = 'py-2 rounded-lg text-sm ' + (type === 'Limit' ? 'bg-blue-700 text-white' : 'bg-gray-700 text-gray-400');
  document.getElementById('limit-price-row').classList.toggle('hidden', type !== 'Limit');
}

export function tradeFromSignal(ticker, side) {
  document.getElementById('trade-ticker').value = ticker.toUpperCase();
  setSide(side);
  setMode('manual');
  document.getElementById('trade-ticker').focus();
}

async function confirmTrade() {
  if (state.tradeRequestPending) return;
  const ticker = document.getElementById('trade-ticker').value.trim().toUpperCase();
  const shares = document.getElementById('trade-shares').value;
  const limitPrice = document.getElementById('trade-limit-price').value;
  if (!ticker || !shares) {
    showTradeMessage('Fill in ticker and shares.', true);
    return;
  }
  if (state.tradeType === 'Limit' && !limitPrice) {
    showTradeMessage('Fill in limit price for limit orders.', true);
    return;
  }
  setTradePending(true);
  showTradeMessage('Submitting order...');
  try {
    const d = await submitOrder({
      ticker,
      side: state.tradeSide,
      orderType: state.tradeType,
      qty: shares,
      limitPrice,
    });
    showTradeMessage(d.message || `Order submitted: ${state.tradeSide} ${shares} ${ticker} @ ${state.tradeType}`);
    await refreshAccountData();
  } catch (e) {
    console.error('Order error:', e);
    showTradeMessage(e.message, true);
  } finally {
    setTradePending(false);
  }
}

function dismissTrade() {
  document.getElementById('trade-ticker').value = '';
  document.getElementById('trade-shares').value = '';
  document.getElementById('trade-limit-price').value = '';
  document.getElementById('trade-msg').textContent = '';
  state.tradeSide = 'BUY';
  state.tradeType = 'Market';
  setSide('BUY');
  setOrderType('Market');
}

function toggleAutoBot() {
  state.autoEnabled = !state.autoEnabled;
  const toggle = document.getElementById('auto-toggle');
  const knob = document.getElementById('auto-knob');
  const label = document.getElementById('auto-status-label');
  if (state.autoEnabled) {
    toggle.classList.replace('toggle-off', 'toggle-on');
    knob.style.transform = 'translateX(20px)';
    label.textContent = 'Bot is active';
    label.className = 'text-xs text-green-400 mt-0.5';
  } else {
    toggle.classList.replace('toggle-on', 'toggle-off');
    knob.style.transform = 'translateX(0)';
    label.textContent = 'Bot is paused';
    label.className = 'text-xs text-gray-500 mt-0.5';
  }
}

function saveAutoSettings() {
  const tp = document.getElementById('auto-tp').value;
  const sl = document.getElementById('auto-sl').value;
  const max = document.getElementById('auto-maxshares').value;
  const msg = document.getElementById('auto-msg');
  msg.textContent = `Rules saved: TP ${tp}% / SL ${sl}% / Max ${max} shares`;
  msg.className = 'text-xs text-center text-green-400';
  setTimeout(() => { msg.textContent = ''; }, 3000);
}
