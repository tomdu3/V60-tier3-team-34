from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
from services.alpaca_service import cancel_alpaca_order, close_all_alpaca_positions, close_alpaca_position, get_account_info, get_portfolio_history, get_positions, get_trade_history, submit_stock_order
from services.supabase_signal_service import read_sentiments_from_supabase, read_signal_feed_from_supabase

app = FastAPI()

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

def validate_trading_env(env: str):
    normalized = (env or "paper").strip().lower()
    if normalized not in {"paper", "live"}:
        raise HTTPException(status_code=400, detail="env must be 'paper' or 'live'")
    return normalized

def alpaca_error_response(error: Exception):
    status_code = 400 if isinstance(error, ValueError) else 502
    raise HTTPException(status_code=status_code, detail=str(error)) from error

@app.get("/", response_class=HTMLResponse)
async def root():
    html_file = BASE_DIR / "templates" / "dashboard.html"
    return HTMLResponse(content=html_file.read_text())

@app.get("/api/signal-feed")
async def get_signal_feed(limit: int = Query(default=20, ge=1, le=100), ticker: str = Query(default="")):
    return read_signal_feed_from_supabase(limit, ticker)

@app.get("/api/debug/sentiments")
async def debug_sentiments(limit: int = Query(default=10, ge=1, le=100)):
    return read_sentiments_from_supabase(limit)

@app.get("/api/debug/tweets-with-sentiments")
async def debug_tweets_with_sentiments(limit: int = Query(default=10, ge=1, le=100)):
    signals = read_signal_feed_from_supabase(limit)
    return [
        {
            "tweet_timestamp": s.get("tweet_timestamp"),
            "tweet_text": s.get("tweet_text")[:50] if s.get("tweet_text") else None,
            "has_sentiment": True,
            "sentiment": s.get("sentiment"),
            "stock_tickers": s.get("stock_tickers"),
        }
        for s in signals
    ]

@app.get("/api/account-equity")
async def get_account_equity(days: int = Query(default=30, ge=1, le=365), env: str = Query(default="paper")):
    trading_env = validate_trading_env(env)
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, get_portfolio_history, days, trading_env)
    except Exception as e:
        alpaca_error_response(e)

@app.get("/api/account-stats")
async def get_account_stats(env: str = Query(default="paper")):
    trading_env = validate_trading_env(env)
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, get_account_info, trading_env)
    except Exception as e:
        alpaca_error_response(e)

@app.get("/api/positions")
async def get_positions_endpoint(env: str = Query(default="paper")):
    trading_env = validate_trading_env(env)
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, get_positions, trading_env)
    except Exception as e:
        alpaca_error_response(e)

@app.post("/api/positions/close")
async def close_position(data: dict):
    trading_env = validate_trading_env(data.get("env", "paper"))
    ticker = data.get("ticker", "")
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, close_alpaca_position, trading_env, ticker)
    except Exception as e:
        alpaca_error_response(e)

@app.post("/api/positions/close-all")
async def close_all_positions(data: dict):
    trading_env = validate_trading_env(data.get("env", "paper"))
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, close_all_alpaca_positions, trading_env)
    except Exception as e:
        alpaca_error_response(e)

@app.get("/api/trade-history")
async def get_trade_history_endpoint(limit: int = Query(default=20, ge=1, le=100), env: str = Query(default="paper")):
    trading_env = validate_trading_env(env)
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, get_trade_history, limit, trading_env)
    except Exception as e:
        alpaca_error_response(e)

@app.post("/api/orders")
async def submit_order(data: dict):
    trading_env = validate_trading_env(data.get("env", "paper"))
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None,
            submit_stock_order,
            trading_env,
            data.get("ticker", ""),
            data.get("side", ""),
            data.get("order_type", "market"),
            data.get("qty", ""),
            data.get("limit_price")
        )
    except Exception as e:
        alpaca_error_response(e)

@app.post("/api/orders/cancel")
async def cancel_order(data: dict):
    trading_env = validate_trading_env(data.get("env", "paper"))
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, cancel_alpaca_order, trading_env, data.get("order_id", ""))
    except Exception as e:
        alpaca_error_response(e)

# Legacy SQLAlchemy endpoints kept for manual/debug access only or if we ever decide to move off supabase; 
# imports stay local so Supabase-backed app paths do not depend on DATABASE_URL unless these routes are called.
# These are not used by the main application, again unless we decide to move off supabase.
@app.get("/tweets")
async def get_tweets(limit: int = Query(default=5, ge=1, le=100)):
    async with async_session_maker() as session:
        result = await session.execute(
            select(Tweet).order_by(Tweet.created_at.desc()).limit(limit)
        )
        tweets = result.scalars().all()
        return [{col.name: getattr(t, col.name) for col in t.__table__.columns} for t in tweets]

@app.get("/users")
async def get_users(limit: int = Query(default=5, ge=1, le=100)):
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserSettings).order_by(UserSettings.created_at.desc()).limit(limit)
        )
        users = result.scalars().all()
        return [{col.name: getattr(u, col.name) for col in u.__table__.columns} for u in users]
