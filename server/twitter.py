from playwright.async_api import async_playwright
from typing import List, Dict

async def scrape_tweet(limit: int = 20) -> List[Dict[str, str]]:
    playwright = await async_playwright().start()
    try:
        device = playwright.devices["Desktop Chrome"]
        browser = await playwright.chromium.launch()
        try:
            context = await browser.new_context(**device)
            page = await context.new_page()
            await page.goto("https://x.com/jimcramer")
            await page.wait_for_selector('[aria-label="Timeline: Jim Cramer’s posts"]')

            tweets_locator = page.locator('[data-testid="tweetText"]')
            attempts = 0
            max_attempts = 10
            while await tweets_locator.count() < limit and attempts < max_attempts:
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

    tweets = asyncio.run(scrape_tweet(20))
    print(json.dumps(tweets, ensure_ascii=False, indent=2))