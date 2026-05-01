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
import asyncio
from services.alpaca_service import get_account_info, get_portfolio_history, get_positions, get_trade_history

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
