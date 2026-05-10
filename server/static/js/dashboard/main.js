import { state } from './state.js';
import { initEnvToggle } from './components/envToggle.js';
import { initEquityChart, loadChart } from './components/equityChart.js';
import { initPositions, loadPositions } from './components/positions.js';
import { initSignalFeed, loadSignals } from './components/signalFeed.js';
import { loadStats } from './components/stats.js';
import { initTradeHistory, loadTradeHistory } from './components/tradeHistory.js';
import { initTradePanel, setTradePending, showTradeMessage, tradeFromSignal } from './components/tradePanel.js';

async function refreshAccountData() {
  await Promise.all([
    loadStats(),
    loadChart(state.currentChartDays),
    loadTradeHistory(),
    loadPositions(),
  ]);
}

function initDashboard() {
  initTradePanel({ refreshAccountData });
  initEnvToggle({ refreshAccountData });
  initEquityChart();
  initSignalFeed({ tradeFromSignal });
  initTradeHistory({ refreshAccountData, setTradePending, showTradeMessage });
  initPositions({ refreshAccountData, setTradePending, showTradeMessage });
  refreshAccountData();
  loadSignals();
  setInterval(loadSignals, 60000);
  setInterval(loadStats, 30000);
  setInterval(loadPositions, 30000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}
