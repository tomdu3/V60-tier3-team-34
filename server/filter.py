# =========================
# TASK #29 - TWEET FILTER MODULE
#
# STATUS: CORE IMPLEMENTATION COMPLETE (WIP FRIENDLY)
#
# PARTLY IMPLEMENTED BY: John Ezekiel
# NEEDS FURTHER IMPROVEMENT BY: Ndzana Christophe
#
# IMPLEMENTED:
# - Retweet filtering (RT detection)
# - Reply filtering (@mentions / replying patterns)
# - Empty/invalid text handling
# - Basic normalization (strip + lowercase)
# - Deduplication (string-based)
#
# TESTING:
# - Verified using sample edge-case dataset
# - Handles common noisy tweet patterns
#
# IMPORTANT NOTES:
# - This is not a final production-locked version
# - It is designed for extension and team iteration
# - Additional edge cases can be safely added
#
# RECOMMENDED NEXT EXTENSIONS:
# - URL/link filtering (https://t.co)
# - Emoji-only / spam detection
# - Improved dedup normalization rules
# =========================



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

    # check for retweets
    if text.startswith("rt") or "retweet" in text:
        return False

    # check for replies
    if text.startswith("@") or "replying to" in text:
        return False

    # links only
    if text.startswith("http"):
        return False

    # mentions-only tweets
    if text.count("@") > 0 and len(text.split()) <= 3:
        return False

    return True


def filter_tweets(tweets: List[Tweet]) -> List[Tweet]:
    """
    Apply filtering rules to a list of tweets.

    This function:
    - Removes invalid tweets using `is_valid_tweet`
    - Removes duplicate tweets based on text content

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

        # Skip duplicate tweets
        if text in seen:
            continue

        seen.add(text)
        filtered.append(tweet)

    return filtered
