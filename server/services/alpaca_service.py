import os
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest, GetPortfolioHistoryRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

# Initialize Alpaca clients
trading_client = TradingClient(
    api_key=os.getenv('ALPACA_API_KEY'),
    secret_key=os.getenv('ALPACA_API_SECRET'),
    paper=True  # Use paper trading by default
)

data_client = StockHistoricalDataClient(
    api_key=os.getenv('ALPACA_API_KEY'),
    secret_key=os.getenv('ALPACA_API_SECRET')
)


def get_account_info():
    """Fetch account information including balances and equity."""
    account = trading_client.get_account()
    
    return {
        "total_equity": float(account.equity),
        "daily_pnl": float(account.equity) - float(account.last_equity),
        "daily_pnl_pct": ((float(account.equity) - float(account.last_equity)) / float(account.last_equity) * 100) if float(account.last_equity) > 0 else 0,
        "cash_balance": float(account.cash),
        "win_rate": 0.0  # TODO: Calculate from trade history
    }


def get_portfolio_history(days=30):
    # Validate input
    valid_periods = {30: "30D", 60: "60D", 90: "90D"}
    if days not in valid_periods:
        raise ValueError(f"days must be 30, 60, or 90, got {days}")

    period = valid_periods[days]

    try:
        # Fetch portfolio history from Alpaca
        request = GetPortfolioHistoryRequest(
            period=period,
            timeframe="1D"
        )
        history = trading_client.get_portfolio_history(history_filter=request)

        # Validate response
        if not history or not hasattr(history, 'timestamp') or not hasattr(history, 'equity'):
            raise Exception("Invalid response from Alpaca API")

        # Parse response and format for frontend
        labels = []
        values = []

        # history.timestamp is a list of unix timestamps
        # history.equity is a list of equity values
        for timestamp, equity in zip(history.timestamp, history.equity):
            dt = datetime.fromtimestamp(timestamp)
            labels.append(dt.strftime("%b %d"))
            values.append(float(equity))

        if not labels:
            raise Exception("No valid data points received from API")

        return {"labels": labels, "values": values}
    except Exception as e:
        # Re-raise with context
        raise Exception(f"Failed to fetch portfolio history: {str(e)}") from e


def get_positions():
    """Fetch all open positions."""
    positions = trading_client.get_all_positions()
    
    result = []
    for pos in positions:
        avg_price = float(pos.avg_entry_price)
        market_price = float(pos.current_price)
        qty = float(pos.qty)
        pnl = (market_price - avg_price) * qty
        pnl_pct = ((market_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
        
        result.append({
            "ticker": pos.symbol,
            "shares": qty,
            "avg_price": avg_price,
            "market_price": market_price,
            "pnl": pnl,
            "pnl_pct": pnl_pct
        })
    
    return result


def get_trade_history(limit=20):
    """Fetch recent orders for trade history."""
    request_params = GetOrdersRequest(
        limit=limit,
        status='all'
    )
    orders = trading_client.get_orders(request_params)
    
    result = []
    for order in orders:
        result.append({
            "ticker": order.symbol,
            "side": order.side.name if order.side else "UNKNOWN",
            "status": order.status.name if order.status else "UNKNOWN",
            "qty": float(order.qty) if order.qty else 0,
            "price": float(order.filled_avg_price) if order.filled_avg_price else float(order.limit_price) if order.limit_price else 0,
            "time": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else ""
        })
    
    return result
