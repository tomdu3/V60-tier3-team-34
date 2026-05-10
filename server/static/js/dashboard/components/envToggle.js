import { state, envLabel } from '../state.js';

let refreshAccountData = async () => {};

export function initEnvToggle(options = {}) {
  refreshAccountData = options.refreshAccountData || refreshAccountData;
  document.getElementById('env-paper')?.addEventListener('click', () => setTradingEnv('paper'));
  document.getElementById('env-live')?.addEventListener('click', () => setTradingEnv('live'));
  updateTradingEnvUi();
}

export function setTradingEnv(env) {
  if (env === state.currentTradingEnv) return;
  if (env === 'live' && !confirm('Switch to LIVE Alpaca account? Account data and trade actions will use real-money live trading.')) {
    updateTradingEnvUi();
    return;
  }
  state.currentTradingEnv = env;
  localStorage.setItem('tradingEnv', state.currentTradingEnv);
  updateTradingEnvUi();
  refreshAccountData();
}

export function updateTradingEnvUi() {
  const isLive = state.currentTradingEnv === 'live';
  document.getElementById('env-paper').className = 'px-3 py-1.5 rounded-lg text-xs font-semibold transition ' + (!isLive ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400');
  document.getElementById('env-live').className = 'px-3 py-1.5 rounded-lg text-xs font-semibold transition ' + (isLive ? 'bg-red-700 text-white' : 'bg-gray-800 text-gray-400');
  const label = document.getElementById('account-env-label');
  label.textContent = envLabel();
  label.className = 'text-xs font-semibold ' + (isLive ? 'text-red-300' : 'text-blue-300');
}
