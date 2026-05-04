import os
from datetime import datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, GetPortfolioHistoryRequest, LimitOrderRequest, MarketOrderRequest
from dotenv import load_dotenv

load_dotenv()

_trading_clients = {}


def _normalize_env(env="paper"):
    normalized = (env or "paper").strip().lower()
    if normalized not in {"paper", "live"}:
        raise ValueError("env must be 'paper' or 'live'")
    return normalized


def _get_credentials(env):
    if env == "live":
        api_key_name = "ALPACA_LIVE_API_KEY"
        secret_key_name = "ALPACA_LIVE_API_SECRET"
    else:
        api_key_name = "ALPACA_API_KEY"
        secret_key_name = "ALPACA_API_SECRET"

    api_key = os.getenv(api_key_name)
    secret_key = os.getenv(secret_key_name)
    if not api_key or not secret_key:
        raise ValueError(f"{api_key_name} and {secret_key_name} environment variables are required")
    return api_key, secret_key


def _get_trading_client(env="paper"):
    normalized_env = _normalize_env(env)
    if normalized_env not in _trading_clients:
        api_key, secret_key = _get_credentials(normalized_env)
        _trading_clients[normalized_env] = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=normalized_env == "paper"
        )
    return _trading_clients[normalized_env]


def _normalize_symbol(ticker):
    symbol = (ticker or "").strip().upper()
    if not symbol:
        raise ValueError("ticker is required")
    if not symbol.replace(".", "").replace("-", "").isalnum():
        raise ValueError("ticker contains invalid characters")
    return symbol


def _normalize_qty(qty):
    try:
        normalized_qty = float(qty)
    except (TypeError, ValueError) as e:
        raise ValueError("qty must be a positive number") from e
    if normalized_qty <= 0:
        raise ValueError("qty must be a positive number")
    return normalized_qty


def _normalize_limit_price(limit_price):
    try:
        normalized_price = float(limit_price)
    except (TypeError, ValueError) as e:
        raise ValueError("limit_price must be a positive number for limit orders") from e
    if normalized_price <= 0:
        raise ValueError("limit_price must be a positive number for limit orders")
    return normalized_price


def _normalize_side(side):
    normalized_side = (side or "").strip().lower()
    if normalized_side == "buy":
        return OrderSide.BUY
    if normalized_side == "sell":
        return OrderSide.SELL
    raise ValueError("side must be 'buy' or 'sell'")


def _normalize_order_id(order_id):
    normalized_id = (order_id or "").strip()
    if not normalized_id:
        raise ValueError("order_id is required")
    return normalized_id


def _enum_name(value, default="UNKNOWN"):
    if value is None:
        return default
    return getattr(value, "name", str(value)).upper()


def _float_or_zero(value):
    return float(value) if value is not None else 0.0


def _format_order(order):
    return {
        "id": str(order.id) if getattr(order, "id", None) else "",
        "ticker": getattr(order, "symbol", ""),
        "side": _enum_name(getattr(order, "side", None)),
        "status": _enum_name(getattr(order, "status", None)),
        "qty": _float_or_zero(getattr(order, "qty", None)),
        "price": _float_or_zero(getattr(order, "filled_avg_price", None)) or _float_or_zero(getattr(order, "limit_price", None)),
        "time": order.created_at.strftime("%Y-%m-%d %H:%M") if getattr(order, "created_at", None) else ""
    }


def get_account_info(env="paper"):
    normalized_env = _normalize_env(env)
    try:
        account = _get_trading_client(normalized_env).get_account()
        equity = float(account.equity)
        last_equity = float(account.last_equity) if account.last_equity else equity
        daily_pnl = equity - last_equity
        return {
            "environment": normalized_env,
            "total_equity": equity,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": (daily_pnl / last_equity * 100) if last_equity > 0 else 0,
            "cash_balance": float(account.cash),
            "win_rate": 0.0
        }
    except Exception as e:
        raise Exception(f"Failed to fetch {normalized_env} account info: {str(e)}") from e


def get_portfolio_history(days=30, env="paper"):
    normalized_env = _normalize_env(env)
    valid_periods = {30: "30D", 60: "60D", 90: "90D"}
    if days not in valid_periods:
        raise ValueError(f"days must be 30, 60, or 90, got {days}")

    period = valid_periods[days]

    try:
        request = GetPortfolioHistoryRequest(
            period=period,
            timeframe="1D"
        )
        history = _get_trading_client(normalized_env).get_portfolio_history(history_filter=request)

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

        return {"environment": normalized_env, "labels": labels, "values": values}
    except Exception as e:
        raise Exception(f"Failed to fetch {normalized_env} portfolio history: {str(e)}") from e


def get_positions(env="paper"):
    normalized_env = _normalize_env(env)
    try:
        positions = _get_trading_client(normalized_env).get_all_positions()

        result = []
        for pos in positions:
            avg_price = float(pos.avg_entry_price)
            market_price = float(pos.current_price)
            qty = float(pos.qty)
            pnl = float(pos.unrealized_pl) if getattr(pos, "unrealized_pl", None) is not None else (market_price - avg_price) * qty
            pnl_pct = float(pos.unrealized_plpc) * 100 if getattr(pos, "unrealized_plpc", None) is not None else ((market_price - avg_price) / avg_price * 100) if avg_price > 0 else 0

            result.append({
                "environment": normalized_env,
                "ticker": pos.symbol,
                "shares": qty,
                "avg_price": avg_price,
                "market_price": market_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            })

        return result
    except Exception as e:
        raise Exception(f"Failed to fetch {normalized_env} positions: {str(e)}") from e


def get_trade_history(limit=20, env="paper"):
    normalized_env = _normalize_env(env)
    try:
        request_params = GetOrdersRequest(
            limit=limit,
            status='all'
        )
        orders = _get_trading_client(normalized_env).get_orders(request_params)

        result = []
        for order in orders:
            formatted_order = _format_order(order)
            formatted_order["environment"] = normalized_env
            result.append(formatted_order)

        return result
    except Exception as e:
        raise Exception(f"Failed to fetch {normalized_env} trade history: {str(e)}") from e


def submit_stock_order(env, ticker, side, order_type, qty, limit_price=None):
    normalized_env = _normalize_env(env)
    symbol = _normalize_symbol(ticker)
    normalized_side = _normalize_side(side)
    normalized_qty = _normalize_qty(qty)
    normalized_order_type = (order_type or "market").strip().lower()

    try:
        if normalized_order_type == "market":
            request = MarketOrderRequest(
                symbol=symbol,
                qty=normalized_qty,
                side=normalized_side,
                time_in_force=TimeInForce.DAY
            )
        elif normalized_order_type == "limit":
            request = LimitOrderRequest(
                symbol=symbol,
                qty=normalized_qty,
                side=normalized_side,
                time_in_force=TimeInForce.DAY,
                limit_price=_normalize_limit_price(limit_price)
            )
        else:
            raise ValueError("order_type must be 'market' or 'limit'")

        order = _get_trading_client(normalized_env).submit_order(order_data=request)
        return {
            "success": True,
            "environment": normalized_env,
            "order": _format_order(order),
            "message": f"{normalized_env.upper()} {normalized_order_type} order submitted for {normalized_qty:g} {symbol}"
        }
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to submit {normalized_env} order: {str(e)}") from e


def close_alpaca_position(env, ticker):
    normalized_env = _normalize_env(env)
    symbol = _normalize_symbol(ticker)
    try:
        order = _get_trading_client(normalized_env).close_position(symbol)
        return {
            "success": True,
            "environment": normalized_env,
            "order": _format_order(order),
            "message": f"{normalized_env.upper()} position close submitted for {symbol}"
        }
    except Exception as e:
        raise Exception(f"Failed to close {normalized_env} position for {symbol}: {str(e)}") from e


def close_all_alpaca_positions(env):
    normalized_env = _normalize_env(env)
    try:
        responses = _get_trading_client(normalized_env).close_all_positions(cancel_orders=False)
        return {
            "success": True,
            "environment": normalized_env,
            "closed_count": len(responses) if responses else 0,
            "message": f"{normalized_env.upper()} close-all request submitted"
        }
    except Exception as e:
        raise Exception(f"Failed to close all {normalized_env} positions: {str(e)}") from e


def cancel_alpaca_order(env, order_id):
    normalized_env = _normalize_env(env)
    normalized_order_id = _normalize_order_id(order_id)
    try:
        _get_trading_client(normalized_env).cancel_order_by_id(normalized_order_id)
        return {
            "success": True,
            "environment": normalized_env,
            "order_id": normalized_order_id,
            "message": f"{normalized_env.upper()} order cancel submitted"
        }
    except Exception as e:
        raise Exception(f"Failed to cancel {normalized_env} order {normalized_order_id}: {str(e)}") from e
