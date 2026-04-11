# =========================
# TASK #29 - TWEET FILTER MODULE
#
# STATUS: CORE IMPLEMENTATION COMPLETE (WIP FRIENDLY)
#
# PARTLY IMPLEMENTED BY: John Ezekiel
# EXTENDED BY: Ndzana Christophe
#
# IMPLEMENTED:
# - Retweet filtering (RT detection) [John]
# - Reply filtering (@mentions / replying patterns) [John]
# - Empty/invalid text handling [John]
# - Basic normalization (strip + lowercase) [John]
# - Deduplication (string-based) [John]
#
# EXTENDED (Christophe):
# - Fixed false-positive retweet detection (rt@ pattern instead of rt alone)
# - Fixed deduplication to use normalized text for comparison
# - URL-only tweet filtering (https://t.co links)
# - Emoji-only / no real word content filtering
#
# TESTING:
# - Verified using sample edge-case dataset
# - Handles common noisy tweet patterns
#
# IMPORTANT NOTES:
# - This is not a final production-locked version
# - It is designed for extension and team iteration
# - Additional edge cases can be safely added
# =========================

import re
from typing import List, Dict

# Type alias for clarity
Tweet = Dict[str, str]


def is_valid_tweet(tweet):
    text = tweet.get("text", "")
    if not text:
        return False

    text = text.strip().lower()

    # empty after stripping
    if not text:
        return False

    if text.startswith("rt @") or "retweet" in text:
        return False

    # check for replies
    if text.startswith("@") or "replying to" in text:
        return False

    if re.fullmatch(r'(https?://t\.co/\S+\s*)+', text):
        return False

    # links only (original rule kept)
    if text.startswith("http"):
        return False

    # mentions-only tweets
    if text.count("@") > 0 and len(text.split()) <= 3:
        return False

    cleaned = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
    if not cleaned.strip():
        return False

    return True


def filter_tweets(tweets: List[Tweet]) -> List[Tweet]:
    """
    Apply filtering rules to a list of tweets.
    This function:
    - Removes invalid tweets using `is_valid_tweet`
    - Removes duplicate tweets based on normalized text content

    Args:
        tweets (List[Tweet]): List of raw tweets from scraper

    Returns:
        List[Tweet]: Cleaned list of tweets
    """
    seen = set()    # Track unique tweet text
    filtered = []   # Store valid tweets

    for tweet in tweets:
        # Skip tweets that fail validation rules
        if not is_valid_tweet(tweet):
            continue

        text = tweet.get("text", "")

        normalized = text.strip().lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        filtered.append(tweet)

    return filtered