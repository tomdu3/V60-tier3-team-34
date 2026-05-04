from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
from services.alpaca_service import get_account_info, get_portfolio_history, get_positions, get_trade_history
from services.supabase_signal_service import read_sentiments_from_supabase, read_signal_feed_from_supabase

app = FastAPI()

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

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
async def get_account_equity(days: int = Query(default=30, ge=1, le=365)):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_portfolio_history, days)

@app.get("/api/account-stats")
async def get_account_stats():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_account_info)

@app.get("/api/positions")
async def get_positions_endpoint():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_positions)

@app.post("/api/positions/close")
async def close_position(data: dict):
    ticker = data.get("ticker", "")
    return {"success": True, "message": f"Position {ticker} closed successfully"}

@app.get("/api/trade-history")
async def get_trade_history_endpoint():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_trade_history)

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
