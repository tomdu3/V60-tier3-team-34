import json
import os
import pytest
from filter import filter_tweets, is_valid_tweet

def test_mock_invalid_tweets_filtering():
    """Test the filtering logic using the mock JSON file with various edge cases."""
    mock_file_path = os.path.join(os.path.dirname(__file__), "data", "mock_invalid_tweets.json")
    
    with open(mock_file_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)
        
    filtered = filter_tweets(tweets)
    
    # Based on our mock data, exactly 2 tweets should survive the filtering
    assert len(filtered) == 2, f"Expected 2 tweets, but got {len(filtered)}"
    
    # Verify the specific tweets that survived
    surviving_texts = [t.get("text") for t in filtered]
    
    # We also verify the deduplication, only one of the duplicate valid tweets should survive
    # And they should be sorted by timestamp (reverse chronological)
    assert surviving_texts[0] == "Another perfectly fine tweet for testing."
    assert surviving_texts[1].lower() == "this is a valid tweet that should not be filtered out."

def test_is_valid_tweet_individual_cases():
    """Test the is_valid_tweet function on individual edge cases directly."""
    
    # Valid tweets
    assert is_valid_tweet({"text": "This is a great day for coding!"}) == True
    
    # Retweets
    assert is_valid_tweet({"text": "RT @user Check this out"}) == False
    assert is_valid_tweet({"text": "I really like this retweet"}) == False
    
    # Replies
    assert is_valid_tweet({"text": "@someone Hello there!"}) == False
    assert is_valid_tweet({"text": "Replying to @user yes I agree"}) == False
    
    # Empty / Emojis only
    assert is_valid_tweet({"text": "   "}) == False
    assert is_valid_tweet({"text": "🔥🔥🔥"}) == False
    
    # URLs only
    assert is_valid_tweet({"text": "https://t.co/abc123xyz"}) == False
    assert is_valid_tweet({"text": "http://example.com/link"}) == False
    
    # Mentions only
    assert is_valid_tweet({"text": "@user1 @user2 @user3"}) == False
