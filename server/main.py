from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, or_
from db.database import async_session_maker
from models.tweet import Tweet
from models.user_settings import UserSettings
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_file = BASE_DIR / "templates" / "dashboard.html"
    return HTMLResponse(content=html_file.read_text())

@app.get("/api/signal-feed")
async def signal_feed_partial(
    limit: int = Query(default=20, ge=1, le=100),
    tickers: str = Query(default="")
):
    async with async_session_maker() as session:
        query = select(Tweet).order_by(Tweet.created_at.desc()).limit(limit)

        if tickers:
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            filters = [Tweet.tweet_text.ilike(f"%{ticker}%") for ticker in ticker_list]
            query = query.where(or_(*filters))

        result = await session.execute(query)
        tweets = result.scalars().all()

    return [
        {
            "text": t.tweet_text,
            "link": t.tweet_link,
            "created_at": str(t.created_at)
        }
        for t in tweets
    ]

@app.get("/tweets")
async def get_tweets(limit: int = Query(default=5, ge=1, le=100)):
    async with async_session_maker() as session:
        result = await session.execute(
            select(Tweet).order_by(Tweet.created_at.desc()).limit(limit)
        )
        tweets = result.scalars().all()
        return [{col.name: getattr(t, col.name) for col in t.__table__.columns} for t in tweets]

@app.get("/api/account-equity")
async def account_equity(days: int = Query(default=30, ge=30, le=90)):
    """
    Returns mock portfolio equity data over time.
    In production, this will fetch from Alpaca API.
    """
    from datetime import datetime, timedelta
    import math
    
    # Mock data: simulate equity growth over the requested period
    data = []
    start_date = datetime.now() - timedelta(days=days)
    current_equity = 100000  # Starting equity
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Simulate realistic daily changes (-2% to +3%)
        daily_change = current_equity * (0.01 * math.sin(i / 10) + 0.002)
        current_equity += daily_change
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "equity": round(current_equity, 2)
        })
    
    total_change = data[-1]["equity"] - data[0]["equity"]
    percent_change = (total_change / data[0]["equity"]) * 100
    
    return {
        "equity_history": data,
        "current_equity": round(current_equity, 2),
        "total_change": round(total_change, 2),
        "percent_change": round(percent_change, 2),
        "days": days
    }


@app.get("/users")
async def get_users(limit: int = Query(default=5, ge=1, le=100)):
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserSettings).order_by(UserSettings.created_at.desc()).limit(limit)
        )
        users = result.scalars().all()
        return [{col.name: getattr(u, col.name) for col in u.__table__.columns} for u in users]
