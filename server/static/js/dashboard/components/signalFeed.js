import { getSignalFeed } from '../api.js';
import { escapeAttribute, escapeHtml } from '../formatters.js';

let signalTimer = null;
let tradeFromSignal = () => {};

export function initSignalFeed(options = {}) {
  tradeFromSignal = options.tradeFromSignal || tradeFromSignal;
  document.getElementById('ticker-filter')?.addEventListener('input', debounceLoadSignals);
  document.getElementById('signal-feed')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-signal-trade]');
    if (!button) return;
    tradeFromSignal(button.dataset.ticker, button.dataset.side);
  });
}

export function debounceLoadSignals() {
  clearTimeout(signalTimer);
  signalTimer = setTimeout(loadSignals, 400);
}

export async function loadSignals() {
  const ticker = document.getElementById('ticker-filter').value.trim();
  try {
    const tweets = await getSignalFeed(ticker);
    document.getElementById('signal-count').textContent = tweets.length + ' signals';
    const feed = document.getElementById('signal-feed');
    feed.innerHTML = tweets.length === 0
      ? '<p class="text-xs text-gray-600 text-center mt-8">No signals found</p>'
      : tweets.map(renderSignal).join('');
  } catch (e) {
    console.error('Signal feed error:', e);
    document.getElementById('signal-count').textContent = '0 signals';
    document.getElementById('signal-feed').innerHTML = '<p class="text-xs text-red-400 text-center mt-8">Signal feed unavailable</p>';
  }
}

function renderSignal(t) {
  const tickers = Array.isArray(t.stock_tickers) ? t.stock_tickers.slice(0, 3) : [];
  const isBearish = t.sentiment === 'bearish';
  const isBullish = t.sentiment === 'bullish';
  const badgeClass = isBearish ? 'badge-buy' : isBullish ? 'badge-sell' : 'bg-gray-700 text-gray-300 border border-gray-500';
  const badgeText = isBearish ? 'BEARISH' : isBullish ? 'BULLISH' : 'NEUTRAL';
  const tickerBadges = tickers.map(tk => `<span class="text-xs font-mono font-bold text-blue-300">${escapeHtml(tk)}</span>`).join(' ');
  const primaryTicker = tickers.length > 0 ? tickers[0] : '';
  const confidenceScore = Number(t.confidence_score) || 0;
  const confidencePercent = (confidenceScore * 100).toFixed(1);
  const actionText = t.inverse_action || 'HOLD';
  const actionClass = actionText === 'BUY' ? 'text-green-400' : actionText === 'SELL' ? 'text-red-400' : 'text-gray-400';
  const tradeButton = primaryTicker && t.inverse_action
    ? `<button data-signal-trade data-ticker="${escapeAttribute(primaryTicker)}" data-side="${escapeAttribute(t.inverse_action)}" class="flex-1 py-1.5 rounded text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition">Trade</button>`
    : '';
  const viewLink = t.tweet_link
    ? `<a href="${escapeAttribute(t.tweet_link)}" target="_blank" class="flex-1 py-1.5 rounded text-xs font-medium bg-gray-700 hover:bg-gray-600 text-gray-300 transition text-center">View</a>`
    : '';
  return `<div class="signal-item">
    <div class="flex items-center justify-between mb-1">
      <div class="flex gap-1">${tickerBadges || '<span class="text-xs text-gray-600">General</span>'}</div>
      <span class="text-xs px-1.5 py-0.5 rounded font-medium ${badgeClass}">${badgeText}</span>
    </div>
    <p class="text-xs text-gray-400 leading-relaxed line-clamp-3 mb-2">${escapeHtml(t.tweet_text || '')}</p>
    <div class="flex items-center justify-between mb-2">
      <span class="text-xs text-gray-500">Confidence: ${confidencePercent}%</span>
      <span class="text-xs font-bold ${actionClass}">→ ${escapeHtml(actionText)}</span>
    </div>
    <div class="flex gap-1.5">
      ${tradeButton}
      ${viewLink}
    </div>
  </div>`;
}
