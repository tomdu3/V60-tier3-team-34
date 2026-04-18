import pytest
import uuid
from datetime import datetime, timezone

from models.tweet import Tweet
from models.user_settings import UserSettings

@pytest.fixture
def mock_tweet_data():
    """Returns a dictionary representing valid tweet data"""
    return {
        "tweet_timestamp": "Apr 17, 2026 · 10:00 AM UTC",
        "tweet_text": "Buy Apple, it's going to the moon! $AAPL",
        "tweet_link": "https://x.com/jimcramer/status/12345",
        "created_at": datetime.now(timezone.utc)
    }

@pytest.fixture
def mock_tweet_model(mock_tweet_data):
    """Returns an instantiated SQLAlchemy Tweet model"""
    return Tweet(**mock_tweet_data)

@pytest.fixture
def mock_user_settings_data():
    """Returns a dictionary representing user profile data"""
    return {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "password_hash": "hashed_password_123",
        "last_login_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "deleted_at": None,
        "risk_per_trade": 0.02,
        "max_positions": 10,
        "max_daily_trades": 5,
        "min_ai_confidence": 0.75
    }

@pytest.fixture
def mock_user_settings_model(mock_user_settings_data):
    """Returns an instantiated SQLAlchemy UserSettings model"""
    return UserSettings(**mock_user_settings_data)

@pytest.fixture
def list_of_mock_tweets():
    """Returns a list of multiple mock Tweet dictionaries"""
    return [
        {
            "tweet_timestamp": "Apr 17, 2026 · 10:00 AM UTC",
            "tweet_text": "First test tweet",
            "tweet_link": "https://x.com/jimcramer/status/1",
        },
        {
            "tweet_timestamp": "Apr 17, 2026 · 10:05 AM UTC",
            "tweet_text": "Second test tweet",
            "tweet_link": "https://x.com/jimcramer/status/2",
        }
    ]
