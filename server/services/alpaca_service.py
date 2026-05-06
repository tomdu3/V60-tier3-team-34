import os
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, GetPortfolioHistoryRequest, MarketOrderRequest, LimitOrderRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

_trading_client = None
_data_client = None

def _get_trading_client():
    global _trading_client
    if _trading_client is None:
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_API_SECRET')
        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET environment variables are required")
        _trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True
        )
    return _trading_client

def _get_data_client():
    global _data_client
    if _data_client is None:
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_API_SECRET')
        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET environment variables are required")
        _data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )
    return _data_client


def get_account_info():
    try:
        account = _get_trading_client().get_account()
        return {
            "total_equity": float(account.equity),
            "daily_pnl": float(account.equity) - float(account.last_equity),
            "daily_pnl_pct": ((float(account.equity) - float(account.last_equity)) / float(account.last_equity) * 100) if float(account.last_equity) > 0 else 0,
            "cash_balance": float(account.cash),
            "win_rate": 0.0
        }
    except Exception as e:
        raise Exception(f"Failed to fetch account info: {str(e)}") from e


def get_portfolio_history(days=30):
    valid_periods = {30: "30D", 60: "60D", 90: "90D"}
    if days not in valid_periods:
        raise ValueError(f"days must be 30, 60, or 90, got {days}")

    period = valid_periods[days]

    try:
        request = GetPortfolioHistoryRequest(
            period=period,
            timeframe="1D"
        )
        history = _get_trading_client().get_portfolio_history(history_filter=request)

        if not history or not hasattr(history, 'timestamp') or not hasattr(history, 'equity'):
            raise Exception("Invalid response from Alpaca API")

        labels = []
        values = []

        for timestamp, equity in zip(history.timestamp, history.equity):
            dt = datetime.fromtimestamp(timestamp)
            labels.append(dt.strftime("%b %d"))
            values.append(float(equity))

        if not labels:
            raise Exception("No valid data points received from API")

        return {"labels": labels, "values": values}
    except Exception as e:
        raise Exception(f"Failed to fetch portfolio history: {str(e)}") from e


def get_positions():
    try:
        positions = _get_trading_client().get_all_positions()

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
    except Exception as e:
        raise Exception(f"Failed to fetch positions: {str(e)}") from e


def get_trade_history(limit=20):
    try:
        request_params = GetOrdersRequest(
            limit=limit,
            status='all'
        )
        orders = _get_trading_client().get_orders(request_params)

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
    except Exception as e:
        raise Exception(f"Failed to fetch trade history: {str(e)}") from e


def submit_stock_order(ticker, side, order_type, qty, limit_price=None):
    try:
        symbol = (ticker or "").strip().upper()
        if not symbol:
            raise ValueError("ticker is required")
        
        normalized_side = (side or "").strip().upper()
        if normalized_side not in ("BUY", "SELL"):
            raise ValueError("side must be 'BUY' or 'SELL'")
        
        try:
            qty_float = float(qty)
        except (TypeError, ValueError):
            raise ValueError("qty must be a positive number")
        
        if qty_float <= 0:
            raise ValueError("qty must be a positive number")
        
        # VALIDATE SELL ORDERS - prevent accidental shorts
        if normalized_side == "SELL":
            positions = get_positions()
            position = next((p for p in positions if p["ticker"] == symbol), None)
            if not position:
                raise ValueError(f"No open position found for {symbol}. Cannot sell without owning shares.")
            if position["shares"] < qty_float:
                raise ValueError(f"Cannot sell {qty_float:g} shares of {symbol}. Only {position['shares']:g} shares owned.")
        
        side_enum = OrderSide.SELL if normalized_side == "SELL" else OrderSide.BUY
        order_type_lower = (order_type or "market").strip().lower()
        
        if order_type_lower == "market":
            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty_float,
                side=side_enum,
                time_in_force=TimeInForce.DAY
            )
        elif order_type_lower == "limit":
            if not limit_price:
                raise ValueError("limit_price is required for limit orders")
            try:
                limit_price_float = float(limit_price)
            except (TypeError, ValueError):
                raise ValueError("limit_price must be a positive number")
            if limit_price_float <= 0:
                raise ValueError("limit_price must be a positive number")
            
            request = LimitOrderRequest(
                symbol=symbol,
                qty=qty_float,
                side=side_enum,
                limit_price=limit_price_float,
                time_in_force=TimeInForce.DAY
            )
        else:
            raise ValueError("order_type must be 'market' or 'limit'")
        
        order = _get_trading_client().submit_order(order_data=request)
        return {
            "success": True,
            "ticker": symbol,
            "side": normalized_side,
            "qty": qty_float,
            "order_type": order_type_lower,
            "status": order.status.name if order.status else "UNKNOWN",
            "message": f"Order submitted: {normalized_side} {qty_float:g} {symbol} @ {order_type_lower}"
        }
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to submit order: {str(e)}") from e


def close_position(ticker):
    try:
        symbol = (ticker or "").strip().upper()
        if not symbol:
            raise ValueError("ticker is required")
        
        order = _get_trading_client().close_position(symbol)
        return {
            "success": True,
            "ticker": symbol,
            "message": f"Position close submitted for {symbol}"
        }
    except Exception as e:
        raise Exception(f"Failed to close position for {ticker}: {str(e)}") from e


def cancel_order(order_id):
    try:
        order_id_str = (order_id or "").strip()
        if not order_id_str:
            raise ValueError("order_id is required")
        
        _get_trading_client().cancel_order_by_id(order_id_str)
        return {
            "success": True,
            "order_id": order_id_str,
            "message": f"Order cancel submitted for {order_id_str}"
        }
    except Exception as e:
        raise Exception(f"Failed to cancel order {order_id}: {str(e)}") from e
