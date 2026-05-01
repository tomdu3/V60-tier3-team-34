import os
from anthropic import Anthropic
from typing import Dict, Any
import json


class ClaudeService:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set!")
        self.client = Anthropic(api_key=api_key)
    
    def analyze_tweet(self, tweet_text: str) -> Dict[str, Any]:
        """
        Analyze a tweet for sentiment and stock tickers using Claude API.
        
        Args:
            tweet_text: The text of the tweet to analyze
            
        Returns:
            Dictionary with keys:
            - sentiment: "bullish", "bearish", or "neutral"
            - confidence_score: float between 0.0 and 1.0
            - stock_tickers: list of stock tickers in format "$AAPL"
            
        Raises:
            Exception: If the Claude API call fails
        """
        prompt = f"""Analyze the following tweet for financial sentiment and stock mentions.

Tweet: "{tweet_text}"

Return your analysis in the following strict JSON format:
{{
    "sentiment": "bullish" or "bearish" or "neutral",
    "confidence_score": 0.0 to 1.0,
    "stock_tickers": ["$AAPL", "$TSLA", "$GOOGL", ...]
}}

Guidelines:
- Sentiment reflects financial outlook (bullish = positive, bearish = negative, neutral = no clear direction).
- Confidence score should reflect certainty based on clarity and explicit financial language.
- Return stock tickers in the format "$TICKER".
- Include tickers if mentioned directly (e.g., "$TSLA") or by company name (e.g., "Tesla" → "$TSLA").
- If no stocks are mentioned, return an empty array.
- If sentiment cannot be determined, set sentiment to "neutral" and confidence_score to 0.0.
- Return ONLY the JSON, no other text.

Example:
{{
    "sentiment": "bullish",
    "confidence_score": 0.87,
    "stock_tickers": ["$TSLA"]
}}"""

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            # Strip markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()
            
            # Parse the JSON response
            result = json.loads(response_text)
            
            # Validate the response structure
            if "sentiment" not in result or "confidence_score" not in result or "stock_tickers" not in result:
                raise ValueError("Invalid response structure from Claude API")
            
            # Validate sentiment value
            valid_sentiments = ["bullish", "bearish", "neutral"]
            if result["sentiment"] not in valid_sentiments:
                raise ValueError(f"Invalid sentiment value: {result['sentiment']}")
            
            # Validate confidence score
            if not isinstance(result["confidence_score"], (int, float)) or not (0.0 <= result["confidence_score"] <= 1.0):
                raise ValueError(f"Invalid confidence score: {result['confidence_score']}")
            
            # Validate stock tickers format and ensure they have $ prefix
            if not isinstance(result["stock_tickers"], list):
                raise ValueError("stock_tickers must be a list")
            
            formatted_tickers = []
            for ticker in result["stock_tickers"]:
                if isinstance(ticker, str):
                    # Ensure ticker has $ prefix
                    if not ticker.startswith("$"):
                        ticker = f"${ticker.upper()}"
                    else:
                        ticker = ticker.upper()
                    formatted_tickers.append(ticker)
            
            result["stock_tickers"] = formatted_tickers
            
            return result
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Claude API response as JSON: {e}")
        except Exception as e:
            raise Exception(f"Claude API call failed: {e}")


# Singleton instance
_claude_service = None


def get_claude_service() -> ClaudeService:
    """Get or create the singleton ClaudeService instance."""
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service
