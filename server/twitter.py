import os
from playwright.async_api import async_playwright
from typing import List, Dict
# limit is the number of tweets to scrape
# max_scroll_attempts is the maximum number of times to scroll
async def scrape_tweet(username: str, password: str, limit: int = 20, max_scroll_attempts: int = 30) -> List[Dict[str, str]]:
    playwright = await async_playwright().start()
    try:
        device = playwright.devices["Desktop Chrome"]
        browser = await playwright.chromium.launch()
        try:
            context = await browser.new_context(**device)
            page = await context.new_page()
            
            # Login to X first
            await page.goto("https://x.com/i/flow/login")
            
            await page.wait_for_selector('input[autocomplete="username"]')
            await page.fill('input[autocomplete="username"]', username)
            await page.keyboard.press("Enter")

            await page.wait_for_selector('input[name="password"]')
            await page.fill('input[name="password"]', password)
            await page.keyboard.press("Enter")

            # Wait for home page to load or a short timeout
            try:
                await page.wait_for_selector('[aria-label="Account menu"]', timeout=10000)
            except Exception:
                print("Login might be facing extra verification or already proceeded.")

            # Navigate to target profile
            await page.goto("https://x.com/jimcramer")
            await page.wait_for_selector('[aria-label="Timeline: Jim Cramer’s posts"]')

            tweets_locator = page.locator('[data-testid="tweetText"]')
            attempts = 0
            while await tweets_locator.count() < limit and attempts < max_scroll_attempts:
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                attempts += 1

            total = await tweets_locator.count()
            n = min(limit, total)
            results = []
            for i in range(n):
                t = tweets_locator.nth(i)
                text = await t.inner_text()
                results.append({"text": text})

            return results
        finally:
            await browser.close()
    finally:
        await playwright.stop()


if __name__ == "__main__":
    import asyncio
    import json
    from dotenv import load_dotenv

    # Load environment variables from .env file if present
    load_dotenv()

    username = os.environ.get("TWITTER_USERNAME", "")
    password = os.environ.get("TWITTER_PASSWORD", "")
    
    if not username or not password:
        print("Please set TWITTER_USERNAME and TWITTER_PASSWORD environment variables.")
        exit(1)

    tweets = asyncio.run(scrape_tweet(username, password, 20))
    print(json.dumps(tweets, ensure_ascii=False, indent=2))