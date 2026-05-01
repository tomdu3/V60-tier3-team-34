from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, or_, join
from sqlalchemy.orm import Session
from db.database import async_session_maker
from models.tweet import Tweet
from models.tweet_sentiment import TweetSentiment
from models.user_settings import UserSettings
from pathlib import Path
from datetime import datetime, timedelta
import random

app = FastAPI()

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    html_file = BASE_DIR / "templates" / "dashboard.html"
    return HTMLResponse(content=html_file.read_text())

@app.get("/api/signal-feed")
async def get_signal_feed(limit: int = Query(default=20, ge=1, le=100), ticker: str = Query(default="")):
    async with async_session_maker() as session:
        query = select(Tweet, TweetSentiment).join(
            TweetSentiment, Tweet.tweet_timestamp == TweetSentiment.tweet_timestamp
        ).order_by(Tweet.created_at.desc()).limit(limit)

        if ticker:
            tickers = [t.strip().upper() for t in ticker.split(",") if t.strip()]
            if tickers:
                query = query.where(
                    or_(*[TweetSentiment.stock_tickers.contains([t]) for t in tickers])
                )

        result = await session.execute(query)
        rows = result.all()

        def get_inverse_action(sentiment):
            if sentiment == "bearish":
                return "BUY"
            elif sentiment == "bullish":
                return "SELL"
            return None

        return [
            {
                "tweet_timestamp": t.tweet_timestamp,
                "tweet_text": t.tweet_text,
                "tweet_link": t.tweet_link,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "sentiment": ts.sentiment,
                "confidence_score": ts.confidence_score,
                "stock_tickers": ts.stock_tickers,
                "inverse_action": get_inverse_action(ts.sentiment),
            }
            for t, ts in rows
        ]

@app.get("/api/account-equity")
async def get_account_equity(days: int = Query(default=30, ge=1, le=365)):
    base_equity = 125000
    labels = []
    values = []
    today = datetime.now()
    for i in range(days, -1, -1):
        date = today - timedelta(days=i)
        labels.append(date.strftime("%b %d"))
        change = random.uniform(-2000, 2500)
        base_equity = max(base_equity + change, 90000)
        values.append(round(base_equity, 2))
    return {"labels": labels, "values": values}

@app.get("/api/account-stats")
async def get_account_stats():
    return {
        "total_equity": 127450.82,
        "daily_pnl": 1823.45,
        "daily_pnl_pct": 1.45,
        "cash_balance": 34210.00,
        "win_rate": 68.4,
    }

@app.get("/api/positions")
async def get_positions():
    return [
        {"ticker": "AAPL", "shares": 50, "avg_price": 178.32, "market_price": 182.45, "pnl": 206.50, "pnl_pct": 2.31},
        {"ticker": "NVDA", "shares": 20, "avg_price": 445.10, "market_price": 467.30, "pnl": 444.00, "pnl_pct": 4.99},
        {"ticker": "MSFT", "shares": 30, "avg_price": 415.20, "market_price": 408.75, "pnl": -193.50, "pnl_pct": -1.55},
    ]

@app.post("/api/positions/close")
async def close_position(data: dict):
    ticker = data.get("ticker", "")
    return {"success": True, "message": f"Position {ticker} closed successfully"}

@app.get("/api/trade-history")
async def get_trade_history():
    return [
        {"ticker": "AAPL", "side": "BUY", "status": "Filled", "qty": 50, "price": 178.32, "time": "2025-04-24 09:31"},
        {"ticker": "NVDA", "side": "BUY", "status": "Filled", "qty": 20, "price": 445.10, "time": "2025-04-23 10:15"},
        {"ticker": "TSLA", "side": "SELL", "status": "Filled", "qty": 15, "price": 248.90, "time": "2025-04-22 14:42"},
        {"ticker": "MSFT", "side": "BUY", "status": "Filled", "qty": 30, "price": 415.20, "time": "2025-04-22 11:05"},
        {"ticker": "META", "side": "SELL", "status": "Cancelled", "qty": 10, "price": 512.00, "time": "2025-04-21 13:20"},
        {"ticker": "AMZN", "side": "BUY", "status": "Pending", "qty": 25, "price": 185.50, "time": "2025-04-25 09:00"},
    ]

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
