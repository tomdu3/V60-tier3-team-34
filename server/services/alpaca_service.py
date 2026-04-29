import os
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
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
    """Fetch historical equity data for the chart."""
    # data coming from account balance
    account = trading_client.get_account()
    base_equity = float(account.equity)
    
    labels = []
    values = []
    today = datetime.now()
    
    for i in range(days, -1, -1):
        date = today - timedelta(days=i)
        labels.append(date.strftime("%b %d"))
# todo: fetch historical data from Alpaca API using get_portfolio_history
        values.append(base_equity)
    
    return {"labels": labels, "values": values}


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
