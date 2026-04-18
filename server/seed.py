import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert

from db.database import async_session_maker
from models.tweet import Tweet
from models.user_settings import UserSettings

async def seed_db():
    print("Seeding database with mock data...")
    
    # 1. Prepare Mock Data
    mock_user = UserSettings(
        id=uuid.uuid4(),
        email="test_seed@example.com",
        username="seeduser",
        full_name="Seed User",
        avatar_url="https://example.com/seed.png",
        password_hash="hashed_password_123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        risk_per_trade=0.02,
        max_positions=10,
        max_daily_trades=5,
        min_ai_confidence=0.75
    )

    mock_tweets = [
        Tweet(
            tweet_timestamp="Apr 17, 2026 · 10:00 AM UTC",
            tweet_text="Buy Apple, it's going to the moon! $AAPL",
            tweet_link="https://x.com/jimcramer/status/12345",
            created_at=datetime.now(timezone.utc)
        ),
        Tweet(
            tweet_timestamp="Apr 17, 2026 · 10:05 AM UTC",
            tweet_text="Sell everything! The market is crashing! $SPY",
            tweet_link="https://x.com/jimcramer/status/12346",
            created_at=datetime.now(timezone.utc)
        )
    ]

    # 2. Insert into Database
    async with async_session_maker() as session:
        try:
            # We use an upsert approach for the user to avoid errors if run multiple times
            stmt_user = insert(UserSettings).values(
                id=mock_user.id,
                email=mock_user.email,
                username=mock_user.username,
                full_name=mock_user.full_name,
                password_hash=mock_user.password_hash,
                avatar_url=mock_user.avatar_url,
                created_at=mock_user.created_at,
                updated_at=mock_user.updated_at,
                risk_per_trade=mock_user.risk_per_trade,
                max_positions=mock_user.max_positions,
                max_daily_trades=mock_user.max_daily_trades,
                min_ai_confidence=mock_user.min_ai_confidence
            )
            # On conflict (unique email/username), just update the login time or ignore
            stmt_user = stmt_user.on_conflict_do_nothing(index_elements=['email'])
            
            await session.execute(stmt_user)

            # Insert Tweets using upsert to avoid duplicate errors on primary key
            for tweet in mock_tweets:
                stmt_tweet = insert(Tweet).values(
                    tweet_timestamp=tweet.tweet_timestamp,
                    tweet_text=tweet.tweet_text,
                    tweet_link=tweet.tweet_link,
                    created_at=tweet.created_at
                )
                stmt_tweet = stmt_tweet.on_conflict_do_nothing(index_elements=['tweet_timestamp'])
                await session.execute(stmt_tweet)

            await session.commit()
            print("Successfully inserted mock user and tweets!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error seeding database: {e}")

if __name__ == "__main__":
    asyncio.run(seed_db())
