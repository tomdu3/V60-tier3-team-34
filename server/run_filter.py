import sys
import json
import os
from filter import filter_tweets

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run run_filter.py <path_to_json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)

    with open(json_file, 'r', encoding='utf-8') as f:
        try:
            tweets = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            sys.exit(1)

    print(f"Loaded {len(tweets)} tweets from {json_file}")
    
    filtered_tweets = filter_tweets(tweets)
    
    print(f"Filtered down to {len(filtered_tweets)} tweets")
    print("-" * 40)
    for i, tweet in enumerate(filtered_tweets[:5]):
        print(f"[{i+1}] {tweet.get('text')}")
    
    if len(filtered_tweets) > 5:
        print(f"... and {len(filtered_tweets) - 5} more.")

if __name__ == "__main__":
    main()
