import sys
import json
import os
import asyncio
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert

from filter import filter_tweets
from db.database import async_session_maker
from models.tweet import Tweet

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

            await session.commit()
            print("Successfully saved filtered tweets to the database!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error saving to database: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run import_tweets.py <path_to_json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    
    # Run the async import function
    asyncio.run(import_tweets(json_file))

if __name__ == "__main__":
    main()
