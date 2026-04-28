
import os
import sys
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime, timezone

# Add the current directory to sys.path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.base import Base
from models.tweet import Tweet
from models.tweet_sentiment import TweetSentiment, SentimentType

def test_relationships():
    # 1. Setup in-memory SQLite database
    # SQLite requires a special pragma to enforce foreign keys
    engine = create_engine("sqlite:///:memory:")
    
    # 2. Create tables
    Base.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Enable foreign keys for this session (SQLite specific)
        session.execute(text("PRAGMA foreign_keys = ON"))
        
        print("\n--- Phase 1: Verify Foreign Key Constraint ---")
        # Try to create a sentiment without a tweet
        bad_sentiment = TweetSentiment(
            tweet_timestamp="non_existent_timestamp",
            sentiment=SentimentType.BULLISH,
            confidence_score=0.95,
            stock_tickers=["AAPL"]
        )
        session.add(bad_sentiment)
        try:
            session.commit()
            print("❌ Error: Sentiment was saved without a valid Tweet (FK failed)")
        except IntegrityError:
            session.rollback()
            print("✅ Success: IntegrityError raised as expected (FK constraint works)")

        print("\n--- Phase 2: Create valid Tweet and Sentiment ---")
        timestamp = "2024-04-28T12:00:00Z"
        tweet = Tweet(
            tweet_timestamp=timestamp,
            tweet_text="Buying some $AAPL today! 🚀",
            tweet_link="https://twitter.com/user/status/123",
            created_at=datetime.now(timezone.utc)
        )
        session.add(tweet)
        session.commit()
        
        sentiment = TweetSentiment(
            tweet_timestamp=timestamp,
            sentiment=SentimentType.BULLISH,
            confidence_score=0.98,
            stock_tickers=["AAPL"]
        )
        session.add(sentiment)
        session.commit()
        print(f"✅ Success: Tweet and Sentiment created and linked via timestamp: {timestamp}")

        print("\n--- Phase 3: Verify CASCADE Delete ---")
        # Ensure sentiment exists
        s = session.execute(select(TweetSentiment).where(TweetSentiment.tweet_timestamp == timestamp)).scalar_one()
        print(f"Sentiment ID: {s.id} exists before tweet deletion.")
        
        # Delete the tweet
        session.delete(tweet)
        session.commit()
        
        # Check if sentiment still exists
        s_after = session.execute(select(TweetSentiment).where(TweetSentiment.tweet_timestamp == timestamp)).scalar()
        if s_after is None:
            print("✅ Success: Sentiment was automatically deleted (CASCADE works)")
        else:
            print("❌ Error: Sentiment still exists after Tweet deletion (CASCADE failed)")

if __name__ == "__main__":
    try:
        test_relationships()
        print("\nAll database relationship tests passed!")
    except Exception as e:
        print(f"\nTests failed with error: {e}")
        sys.exit(1)
