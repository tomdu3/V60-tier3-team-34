# Testing `filter.py`

This project includes two primary ways to test the tweet filtering logic found in `filter.py`: automated tests using Pytest and manual CLI testing against real or mock JSON data.

## 1. Automated Testing (`test_filter.py`)

The automated test suite uses `pytest` to verify the logic of `filter.py`. It includes unit tests for individual edge cases (like retweets, replies, empty tweets, and links) as well as an integration test that runs the filter against a mock JSON file (`data/mock_invalid_tweets.json`).

**Purpose:** Ensure the filter logic remains accurate and doesn't regress when making changes to the codebase.

**How to run:**
Execute the following command in your terminal from the `server` directory:

```bash
uv run pytest
```

*(You can also use `uv run pytest --verbose` for more detailed output.)*

## 2. Manual CLI Testing (`run_filter.py`)

If you want to manually inspect the output of the filter against a specific JSON file of scraped tweets, you can use the `run_filter.py` script. 

**Purpose:** Quickly preview how real-world scraped data (or edge-case mock data) is being filtered, deduplicated, and sorted in a human-readable format.

**How to run:**
Pass the path to your target JSON file as an argument to the script from the `server` directory:

```bash
uv run run_filter.py data/name_of_json.json
```

For example, to test against the mock file:
```bash
uv run run_filter.py data/mock_invalid_tweets.json
```

The script will load the tweets, apply the filter, and print out a summary along with a preview of the valid tweets that survived the filter.

## 3. Understanding the Data Requirements

When testing or extending `filter.py`, keep in mind how the functions interact with the tweet dictionary structure:

- **`is_valid_tweet`**: Looks primarily at the `"text"` key of the tweet dictionary to determine if the content violates any rules (e.g., retweets, mentions-only, etc).
- **`filter_tweets`**: Applies `is_valid_tweet` to a list of tweets, and further expects a `"text"` key for case-insensitive deduplication, and a `"timestamp"` key to sort the final list in reverse chronological order.
