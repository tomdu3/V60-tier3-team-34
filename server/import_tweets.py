import sys
import json
import os
import asyncio
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from filter import filter_tweets
from db.database import async_session_maker
from models.tweet import Tweet
from models.tweet_sentiment import TweetSentiment, SentimentType
from services.claude_service import get_claude_service

async def import_tweets(json_file: str):
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)

    print(f"Reading file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        try:
            raw_tweets = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            sys.exit(1)

    print(f"Loaded {len(raw_tweets)} raw tweets. Applying filter...")
    
    # 1. Filter the tweets using filter.py logic
    filtered_tweets = filter_tweets(raw_tweets)
    print(f"Filtered down to {len(filtered_tweets)} valid tweets.")
    
    if not filtered_tweets:
        print("No valid tweets to insert. Exiting.")
        return

    # 2. Insert into the Database using async session
    print("Inserting tweets into the database...")
    
    async with async_session_maker() as session:
        try:
            inserted_tweets = []
            for tweet_data in filtered_tweets:
                # Prepare the insert statement for the Tweet model
                stmt = insert(Tweet).values(
                    tweet_timestamp=tweet_data.get("timestamp"),
                    tweet_text=tweet_data.get("text"),
                    tweet_link=tweet_data.get("url"),
                    created_at=datetime.now(timezone.utc)
                )
                
                # On conflict (meaning the tweet_timestamp already exists), we can either
                # DO NOTHING or UPDATE. We'll DO NOTHING to avoid unnecessary writes,
                # as Jim Cramer's historical tweets won't change text.
                stmt = stmt.on_conflict_do_nothing(index_elements=['tweet_timestamp'])
                
                await session.execute(stmt)
                inserted_tweets.append(tweet_data)

            await session.commit()
            print(f"Successfully saved {len(inserted_tweets)} filtered tweets to the database!")
            
            # 3. Analyze tweets with Claude API
            print("Analyzing tweets with Claude API for sentiment and stock tickers...")
            claude_service = get_claude_service()
            
            async def analyze_single_tweet(tweet_data):
                try:
                    tweet_text = tweet_data.get("text", "")
                    tweet_timestamp = tweet_data.get("timestamp")
                    
                    if not tweet_text:
                        print(f"Warning: No text for tweet at {tweet_timestamp}, skipping analysis")
                        return None
                    
                    print(f"Analyzing tweet: {tweet_text[:50]}...")
                    analysis = claude_service.analyze_tweet(tweet_text)
                    
                    return {
                        "tweet_timestamp": tweet_timestamp,
                        "sentiment": analysis["sentiment"],
                        "confidence_score": analysis["confidence_score"],
                        "stock_tickers": analysis["stock_tickers"]
                    }
                except Exception as e:
                    print(f"Error analyzing tweet at {tweet_data.get('timestamp')}: {e}")
                    raise  # Re-raise to trigger rollback
            
            # Analyze all tweets concurrently
            analysis_results = await asyncio.gather(
                *[analyze_single_tweet(tweet) for tweet in inserted_tweets],
                return_exceptions=True
            )
            
            # Check for errors in analysis
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    raise result  # Raise the first error to trigger rollback
            
            # Filter out None results (tweets without text)
            valid_results = [r for r in analysis_results if r is not None]
            
            print(f"Successfully analyzed {len(valid_results)} tweets with Claude API")
            
            # Print sentiment analysis results for testing
            print("\n=== Sentiment Analysis Results ===")
            for result in valid_results:
                print(f"\nTimestamp: {result['tweet_timestamp']}")
                print(f"Sentiment: {result['sentiment']}")
                print(f"Confidence Score: {result['confidence_score']}")
                print(f"Stock Tickers: {result['stock_tickers']}")
            print("=== End of Analysis Results ===\n")
            
            # 4. Insert sentiment analysis results
            print("Inserting sentiment analysis results into database...")
            for result in valid_results:
                stmt = insert(TweetSentiment).values(
                    tweet_timestamp=result["tweet_timestamp"],
                    sentiment=SentimentType(result["sentiment"]),
                    confidence_score=result["confidence_score"],
                    stock_tickers=result["stock_tickers"],
                    analyzed_at=datetime.now(timezone.utc)
                )
                await session.execute(stmt)
            
            await session.commit()
            print("Successfully saved sentiment analysis results to the database!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error during import/analysis: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run import_tweets.py <path_to_json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    
    # Run the async import function
    asyncio.run(import_tweets(json_file))

if __name__ == "__main__":
    main()
