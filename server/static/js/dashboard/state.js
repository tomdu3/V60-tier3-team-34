export const state = {
  equityChart: null,
  equityChartExpanded: null,
  allTrades: [],
  currentFilter: 'All',
  tradeSide: 'BUY',
  tradeType: 'Market',
  autoEnabled: false,
  currentMode: 'manual',
  chartExpanded: false,
  currentChartDays: 30,
  currentTradingEnv: localStorage.getItem('tradingEnv') === 'live' ? 'live' : 'paper',
  tradeRequestPending: false,
};

export function envLabel() {
  return state.currentTradingEnv.toUpperCase();
}
