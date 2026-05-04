import os

from dotenv import load_dotenv
from fastapi import HTTPException
from supabase import Client, create_client

load_dotenv()

_supabase_client: Client | None = None


def _get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client:
        return _supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase configuration is missing")

    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as exc:
        print(f"Supabase client initialization failed: {exc}")
        raise HTTPException(status_code=500, detail="Supabase client initialization failed")


def _get_inverse_action(sentiment):
    if sentiment == "bearish":
        return "BUY"
    elif sentiment == "bullish":
        return "SELL"
    return None


def _normalize_tickers(stock_tickers):
    if isinstance(stock_tickers, list):
        return [str(t).strip().upper().lstrip("$") for t in stock_tickers if str(t).strip()]
    if isinstance(stock_tickers, str) and stock_tickers.strip():
        return [stock_tickers.strip().upper().lstrip("$")]
    return []


def _matches_ticker_filter(stock_tickers, ticker_filter):
    if not ticker_filter:
        return True
    normalized = set(_normalize_tickers(stock_tickers))
    return any(t in normalized for t in ticker_filter)


def read_sentiments_from_supabase(limit: int):
    supabase = _get_supabase_client()

    try:
        result = (
            supabase.table("tweet_sentiments")
            .select("id,tweet_timestamp,sentiment,confidence_score,stock_tickers,analyzed_at")
            .order("analyzed_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Failed to read tweet sentiments from Supabase: {exc}")
        raise HTTPException(status_code=502, detail="Failed to read tweet sentiments from Supabase")


def read_signal_feed_from_supabase(limit: int, ticker: str = ""):
    supabase = _get_supabase_client()
    ticker_filter = [t.strip().upper().lstrip("$") for t in ticker.split(",") if t.strip()]
    candidate_limit = min(1000, max(limit * 10, limit)) if ticker_filter else limit

    try:
        sentiment_result = (
            supabase.table("tweet_sentiments")
            .select("id,tweet_timestamp,sentiment,confidence_score,stock_tickers,analyzed_at")
            .order("analyzed_at", desc=True)
            .limit(candidate_limit)
            .execute()
        )
        sentiments = sentiment_result.data or []
        sentiments = [s for s in sentiments if _matches_ticker_filter(s.get("stock_tickers"), ticker_filter)][:limit]

        tweet_timestamps = [s.get("tweet_timestamp") for s in sentiments if s.get("tweet_timestamp")]
        if not tweet_timestamps:
            return []

        tweet_result = (
            supabase.table("tweets")
            .select("tweet_timestamp,tweet_text,tweet_link,created_at")
            .in_("tweet_timestamp", tweet_timestamps)
            .execute()
        )
        tweets_by_timestamp = {
            t.get("tweet_timestamp"): t
            for t in (tweet_result.data or [])
            if t.get("tweet_timestamp")
        }

        signals = []
        for sentiment_row in sentiments:
            tweet = tweets_by_timestamp.get(sentiment_row.get("tweet_timestamp"))
            if not tweet:
                continue

            sentiment = sentiment_row.get("sentiment")
            signals.append({
                "tweet_timestamp": sentiment_row.get("tweet_timestamp"),
                "tweet_text": tweet.get("tweet_text"),
                "tweet_link": tweet.get("tweet_link"),
                "created_at": tweet.get("created_at"),
                "sentiment": sentiment,
                "confidence_score": sentiment_row.get("confidence_score"),
                "stock_tickers": sentiment_row.get("stock_tickers") or [],
                "inverse_action": _get_inverse_action(sentiment),
            })

        return signals
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Failed to read signal feed from Supabase: {exc}")
        raise HTTPException(status_code=502, detail="Failed to read signal feed from Supabase")
