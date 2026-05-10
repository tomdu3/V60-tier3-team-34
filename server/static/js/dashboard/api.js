import { state } from './state.js';

export function apiUrl(path, params = {}) {
  const query = new URLSearchParams({ ...params, env: state.currentTradingEnv });
  return path + '?' + query.toString();
}

export async function readApiResponse(res) {
  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    const detail = typeof data === 'string' ? data : data.detail || data.message || JSON.stringify(data);
    throw new Error(detail);
  }
  return data;
}

export async function getAccountStats() {
  const res = await fetch(apiUrl('/api/account-stats'));
  return readApiResponse(res);
}

export async function getAccountEquity(days) {
  const res = await fetch(apiUrl('/api/account-equity', { days }));
  return readApiResponse(res);
}

export async function getSignalFeed(ticker) {
  const url = '/api/signal-feed?limit=30' + (ticker ? '&ticker=' + encodeURIComponent(ticker) : '');
  const res = await fetch(url);
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || 'Signal feed request failed');
  }
  return res.json();
}

export async function getTradeHistory(limit = 50) {
  const res = await fetch(apiUrl('/api/trade-history', { limit }));
  return readApiResponse(res);
}

export async function cancelOrder(orderId) {
  const res = await fetch('/api/orders/cancel', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_id: orderId, env: state.currentTradingEnv }),
  });
  return readApiResponse(res);
}

export async function getPositions() {
  const res = await fetch(apiUrl('/api/positions'));
  return readApiResponse(res);
}

export async function closePosition(ticker, reason) {
  const body = { ticker, env: state.currentTradingEnv };
  if (reason) body.reason = reason;
  const res = await fetch('/api/positions/close', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return readApiResponse(res);
}

export async function closeAllPositions() {
  const res = await fetch('/api/positions/close-all', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ env: state.currentTradingEnv }),
  });
  return readApiResponse(res);
}

export async function submitOrder({ ticker, side, orderType, qty, limitPrice }) {
  const res = await fetch('/api/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      env: state.currentTradingEnv,
      ticker,
      side,
      order_type: orderType,
      qty,
      limit_price: orderType === 'Limit' ? limitPrice : null,
    }),
  });
  return readApiResponse(res);
}
