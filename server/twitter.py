import asyncio
import json
import argparse
import os
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
import pandas as pd
from bs4 import BeautifulSoup
import random
import re
import urllib.parse
from dotenv import load_dotenv
from supabase import create_client, Client


class TwitterScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.playwright = None
        # Expanded list of working mirrors for better resilience
        self.nitter_mirrors = [
            "https://nitter.net",
            "https://nitter.poast.org", 
            "https://nitter.privacyredirect.com",
            "https://nitter.uni-sonia.com",
            "https://xcancel.com"
        ]

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            # Use more standard args to avoid detection
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ]
        )
        
        # Create context with a more realistic user agent and viewport
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=1
        )
        
        # Add script to further hide automation
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            // Overwrite the 'plugins' property to look more natural
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            // Overwrite the 'languages' property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'browser') and self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()

    async def login(self, username: str, password: str, email: Optional[str] = None):
        """Log in to Twitter/X with humanized interactions"""
        print(f"Logging in to Twitter as {username}...")
        
        try:
            # Random helper to simulate human pauses
            import random
            async def human_pause(min_ms=500, max_ms=1500):
                await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000.0)

            # Go to home page first to handle cookies and establish session
            await self.page.goto("https://x.com", wait_until="load", timeout=60000)
            await human_pause(1000, 2000)
            
            # 1. Handle cookie banner if it exists
            try:
                cookie_button = self.page.get_by_role("button", name="Accept all cookies")
                if await cookie_button.is_visible(timeout=3000):
                    print("Accepting cookies...")
                    await cookie_button.click()
                    await human_pause()
            except:
                pass

            # 2. Start Login Flow from Home Page
            print("Preparing to open login modal...")
            await human_pause(2000, 4000)
            
            sign_in_button = self.page.locator('a[href="/login"], button:has-text("Sign in")').first
            await sign_in_button.wait_for(state="visible", timeout=30000)
            await sign_in_button.click()
            
            # Wait for modal to fully animate and settle
            await human_pause(3000, 5000)
            
            # Wait for username input
            print("Entering username...")
            username_field = self.page.locator('input[autocomplete="username"]')
            await username_field.wait_for(state="visible", timeout=30000)
            
            # Focus and click before typing
            await username_field.focus()
            await human_pause(500, 1000)
            await username_field.click()
            await human_pause(500, 1000)
            
            # Type slowly and naturally
            await username_field.press_sequentially(username, delay=random.randint(70, 180))
            await human_pause(1500, 3000)
            
            # Navigate using Enter key (more human than button click often)
            print("Advancing to next screen...")
            await self.page.keyboard.press("Enter")
            
            # Wait for transition
            await human_pause(3000, 6000)
            
            # Check for verification or password
            print("Checking screen state...")
            
            for i in range(15):
                # 1. Is it the password field?
                password_field = self.page.locator('input[name="password"]')
                if await password_field.is_visible():
                    print("Found password field.")
                    break
                
                # 2. Is it a verification field?
                v_selectors = ['input[data-testid="ocfEnterTextTextInput"]', 'input[name="text"]']
                page_text = (await self.page.content()).lower()
                is_verification_page = any(term in page_text for term in ["unusual activity", "verify", "phone or email", "confirmation code"])

                if is_verification_page:
                    for sel in v_selectors:
                        v_field = self.page.locator(sel)
                        if await v_field.is_visible():
                            is_username = await v_field.get_attribute("autocomplete") == "username"
                            if not is_username:
                                if email:
                                    print(f"Bypassing verification step...")
                                    await v_field.click()
                                    await human_pause()
                                    await v_field.press_sequentially(email, delay=random.randint(70, 180))
                                    await human_pause(1500, 3000)
                                    await self.page.keyboard.press("Enter")
                                    await human_pause(4000, 7000)
                                    break
                                else:
                                    print("Warning: Verification screen detected but no email provided!")
                                    break
                
                await asyncio.sleep(1)
            
            # Wait for password input and enter
            print("Entering password...")
            password_field = self.page.locator('input[name="password"]')
            await password_field.wait_for(state="visible", timeout=20000)
            await password_field.click()
            await human_pause()
            await password_field.press_sequentially(password, delay=random.randint(70, 180))
            await human_pause(1500, 3000)
            
            # Use Enter to submit
            print("Submitting login...")
            await self.page.keyboard.press("Enter")
            
            # Wait to confirm login
            try:
                await self.page.wait_for_url("**/*home*", timeout=25000)
                print("✓ Successfully logged in!")
            except Exception:
                if "/home" in self.page.url:
                    print("✓ Successfully logged in (URL verified)!")
                else:
                    print(f"Warning: Login may have failed (URL: {self.page.url})")
                    await self.page.screenshot(path="debug_login_result.png")
                
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"✗ Error during login process: {e}")
            await self.page.screenshot(path="debug_login_error.png")
            print("Debug screenshot saved to debug_login_error.png")

    async def discover_tweets_via_search(
        self, 
        username: str, 
        timeframe: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[str]:
        """Discover tweet status URLs via Google Search to bypass login wall"""
        search_query = f"site:x.com/{username}/status"
        
        # Construct search URL (Google tbs: qdr:d=day, qdr:w=week, qdr:m=month)
        if timeframe:
            tbs_map = {'day': 'qdr:d', 'week': 'qdr:w', 'month': 'qdr:m'}
            tbs = tbs_map.get(timeframe, 'qdr:d')
            search_url = f"https://www.google.com/search?q={search_query}&tbs={tbs}"
        elif since or until:
            if since: search_query += f" after:{since}"
            if until: search_query += f" before:{until}"
            search_url = f"https://www.google.com/search?q={search_query}"
        else:
            search_url = f"https://www.google.com/search?q={search_query}&tbs=qdr:d"

        print(f"Discovering recent tweets via Search...")
        try:
            # Human-like delay and initial navigation
            await asyncio.sleep(random.uniform(1.0, 3.0))
            await self.page.goto("https://www.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1.0, 2.0))
            await self.page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # Extract links matching status pattern
            links = await self.page.query_selector_all('a[href*="/status/"]')
            urls = []
            
            if not links:
                print("No links found on search page. Saving debug screenshot...")
                await self.page.screenshot(path="debug_discovery_search.png")
            
            for link in links:
                href = await link.get_attribute('href')
                if href and f"/{username}/status/" in href:
                    # Clean the URL
                    if "google.com/url?" in href:
                        parsed = urllib.parse.urlparse(href)
                        q_param = urllib.parse.parse_qs(parsed.query).get('q', [''])[0]
                        if q_param: href = q_param
                    
                    href = href.split('?')[0]
                    if 'x.com' in href and href not in urls:
                        urls.append(href)
            print(f"Found {len(urls)} potential tweet URLs through search discovery.")
            return urls
        except Exception as e:
            print(f"Error during discovery: {e}")
            return []

    async def scrape_from_mirror(
        self, 
        username: str, 
        max_tweets: int = 20,
        include_replies: bool = False,
        output_file: Optional[str] = None
    ) -> List[Dict]:
        """Scrape tweets from a Nitter mirror (no login required, chronological)"""
        for base_url in self.nitter_mirrors:
            url = f"{base_url}/{username}"
            print(f"Attempting to scrape from mirror: {base_url}...")
            
            try:
                # Add a bit of randomization to avoid rate limits
                await asyncio.sleep(random.uniform(1.0, 3.0))
                await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Wait for at least some content to appear
                try:
                    await self.page.wait_for_selector(".timeline-item", timeout=10000)
                except:
                    print(f"Mirror {base_url} timeout waiting for timeline. Saving debug screenshot...")
                    await self.page.screenshot(path=f"debug_mirror_{base_url.split('//')[1].replace('.', '_')}.png")
                    continue
                
                tweets = []
                last_height = await self.page.evaluate("document.body.scrollHeight")
                
                while len(tweets) < max_tweets:
                    html_content = await self.page.content()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    items = soup.find_all('div', class_='timeline-item')
                    
                    for item in items:
                        if len(tweets) >= max_tweets: break
                        
                        # 1. Skip non-tweet items (like thread continuations)
                        if 'show-more' in item.get('class', []): continue
                        
                        # 2. Check if it's a reply
                        is_reply = item.find('div', class_='tweet-body').find('div', class_='replying-to') is not None
                        if not include_replies and is_reply: continue
                        
                        # 3. Extract text
                        content_div = item.find('div', class_='tweet-content')
                        if not content_div: continue
                        text = content_div.get_text(strip=True)
                        
                        # 4. Extract timestamp (from title attribute for precision)
                        date_link = item.find('span', class_='tweet-date').find('a')
                        timestamp_str = date_link.get('title') if date_link else ""
                        
                        # 5. Extract Status URL
                        status_link = item.find('a', class_='tweet-link')
                        tweet_url = f"https://x.com{status_link.get('href')}" if status_link else ""
                        
                        # 6. Extract Metrics
                        stats = item.find_all('span', class_='tweet-stat')
                        metrics = {'replies': 0, 'retweets': 0, 'likes': 0}
                        for stat in stats:
                            icon = stat.find('span', class_=re.compile(r'icon-'))
                            val = self._parse_number(stat.get_text(strip=True))
                            if not icon: continue
                            cls = "".join(icon.get('class', []))
                            if 'comment' in cls: metrics['replies'] = val
                            elif 'retweet' in cls: metrics['retweets'] = val
                            elif 'heart' in cls: metrics['likes'] = val
                        
                        tweet_data = {
                            'username': username,
                            'text': text,
                            'timestamp': timestamp_str,
                            'url': tweet_url,
                            'is_reply': is_reply,
                            **metrics,
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        if text not in [t['text'] for t in tweets]:
                            tweets.append(tweet_data)
                            print(f"✓ Scraped (Mirror): {text[:50]}...")
                    
                    # Scroll for more if needed
                    if len(tweets) < max_tweets:
                        await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await asyncio.sleep(2)
                        new_height = await self.page.evaluate("document.body.scrollHeight")
                        if new_height == last_height: break
                        last_height = new_height
                    else:
                        break
                
                if tweets:
                    if output_file: self._save_tweets(tweets, output_file)
                    return tweets
                    
            except Exception as e:
                print(f"Error scraping mirror {base_url}: {e}")
                continue
                
        return []

    async def scrape_tweets(
        self, 
        username: str, 
        max_tweets: int = 20,
        include_replies: bool = False,
        output_file: Optional[str] = None,
        timeframe: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[Dict]:
        """Scrape tweets from a Twitter/X account (Mirror or Direct mode)"""
        
        # Determine if we should use Mirror Mode
        # Use mirror if: NOT logged in OR specifically requested login-free
        is_logged_in = "/home" in self.page.url
        use_mirror = not is_logged_in or timeframe or since or until
        
        if use_mirror:
            print(f"Using login-free Mirror Mode for @{username}...")
            return await self.scrape_from_mirror(username, max_tweets, include_replies, output_file)
        else:
            print(f"Using direct X.com mode for @{username} (Authenticated)...")
            return await self._scrape_profile_method(username, max_tweets, include_replies, output_file)

    async def _scrape_profile_method(self, username, max_tweets, include_replies, output_file):
        """Standard profile scraping (best for logged-in sessions)"""
        print(f"Starting to scrape tweets from @{username} profile timeline...")
        url = f"https://x.com/{username}"
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Error navigating to profile: {e}")
            return []
        
        try:
            await self.page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
        except Exception as e:
            print(f"No tweets found on profile: {e}")
            return []
        
        tweets = []
        last_height = await self.page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        
        while len(tweets) < max_tweets and scroll_attempts < 10:
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
            
            for tweet_element in tweet_elements:
                if len(tweets) >= max_tweets: break
                tweet_data = self._parse_tweet(tweet_element, username)
                if not tweet_data: continue
                if not include_replies and tweet_data.get('is_reply', False): continue
                if tweet_data['text'] not in [t['text'] for t in tweets]:
                    tweets.append(tweet_data)
                    print(f"✓ Scraped tweet {len(tweets)}/{max_tweets}: {tweet_data['text'][:50]}...")
            
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(2)
            new_height = await self.page.evaluate("document.body.scrollHeight")
            if new_height == last_height: scroll_attempts += 1
            else: scroll_attempts = 0
            last_height = new_height
        
        tweets.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
        if output_file and tweets:
            self._save_tweets(tweets, output_file)
        return tweets

    async def scrape_status_url(self, url: str) -> Optional[Dict]:
        """Scrape details for a single tweet status URL"""
        print(f"Scraping status URL: {url}...")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # Wait for the main tweet article
            try:
                await self.page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
            except:
                print(f"Tweet article not found at {url}")
                return None
            
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # On a status page, the main tweet is usually the first article
            # or the one that matches the ID in the URL
            tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
            for element in tweet_elements:
                # We try to find the one that matches the ID or just take the first one if it's a status page
                # Often the first one is the main tweet
                tweet_data = self._parse_tweet(element, "")
                if tweet_data:
                    # Clean up username if possible
                    if not tweet_data['username']:
                        match = re.search(r'x\.com/([^/]+)/status', url)
                        if match: tweet_data['username'] = match.group(1)
                    return tweet_data
                    
        except Exception as e:
            print(f"Error scraping status URL {url}: {e}")
        return None

    async def find_tweet_url_by_text(self, text: str, username: Optional[str] = None) -> Optional[str]:
        """Find the status URL of a tweet based on its text content"""
        # Clean text for search (remove newlines, extra spaces)
        search_text = " ".join(text.split())
        
        # 1. Try X.com search if logged in
        is_logged_in = "/home" in self.page.url
        if is_logged_in:
            query = f'"{search_text}"'
            if username:
                query += f" from:{username}"
            
            search_url = f"https://x.com/search?q={query}&f=live"
            print(f"Searching X.com for: {query}...")
            
            try:
                await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)
                
                # Find the first tweet matching the text
                await self.page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
                html_content = await self.page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})
                
                for element in tweet_elements:
                    text_div = element.find('div', {'data-testid': 'tweetText'})
                    if text_div and search_text[:50].lower() in text_div.get_text().lower():
                        link = element.find('a', href=lambda h: h and '/status/' in h)
                        if link:
                            return f"https://x.com{link['href']}"
            except Exception as e:
                print(f"X.com search failed: {e}")

        # 2. Fallback to Search Engines (Nitter Search is primary for exact matches)
        clean_text = re.sub(r'[^\w\s\$\%\#\.]', ' ', search_text)
        clean_text = " ".join(clean_text.split())
        
        # Build discovery sources: Nitter mirrors first, then fallbacks
        discovery_sources = []
        for mirror in self.nitter_mirrors:
            discovery_sources.append({
                "name": f"Nitter ({urllib.parse.urlparse(mirror).netloc})", 
                "url": f"{mirror}/search?f=tweets&q={{query}}"
            })
        
        discovery_sources.extend([
            {"name": "Brave", "url": "https://search.brave.com/search?q={query}"},
            {"name": "DuckDuckGo", "url": "https://duckduckgo.com/?q={query}"}
        ])
        
        queries = []
        # For Nitter, we can use the 'from:username' operator directly
        if username:
            if len(clean_text) > 40:
                queries.append(f'"{clean_text[:60]}" from:{username}')
            # Variation for long texts on Nitter: just the core keywords
            keywords = " ".join(clean_text.split()[:10])
            queries.append(f'{keywords} from:{username}')
        else:
            if len(clean_text) > 40:
                queries.append(f'"{clean_text[:50]}" site:x.com')
            queries.append(f'{clean_text[:100]} site:x.com')

        for source in discovery_sources:
            for base_query in queries:
                # For non-Nitter engines, we need 'site:x.com' if not already there
                query = base_query
                is_nitter = "Nitter" in source['name']
                if not is_nitter and "site:x.com" not in query:
                    if username:
                        query = f'"{clean_text[:50]}" site:x.com/{username}' if len(clean_text) > 40 else f'{clean_text} site:x.com/{username}'
                    else:
                        query = f'{query} site:x.com'
                
                print(f"Searching {source['name']} for: {query}...")
                search_url = source['url'].format(query=urllib.parse.quote(query))
                
                try:
                    # Clear any pending navigations/redirects from previous failed mirrors
                    try:
                        await self.page.stop()
                    except: pass
                    
                    # Wait for 'load' instead of 'domcontentloaded' to ensure results are rendering
                    await self.page.goto(search_url, wait_until="load", timeout=45000)
                    # Increased stabilization sleep
                    await asyncio.sleep( random.uniform(4, 7) )
                    
                    # Ensure the page is stabilized with longer networkidle timeout
                    try:
                        await self.page.wait_for_load_state("networkidle", timeout=10000)
                    except: pass
                    
                    # Detect "No results" or CAPTCHAs
                    content = ""
                    for retry in range(3):
                        try:
                            content = (await self.page.content()).lower()
                            break
                        except:
                            await asyncio.sleep(1)

                    if not content or any(term in content for term in ["no results", "did not match", "captcha", "security check", "not found"]):
                        continue

                    # Look for status links
                    # Nitter links: /user/status/123#m or /search?q=...
                    # We want /user/status/123
                    links = await self.page.query_selector_all('a[href*="/status/"]')
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and '/status/' in href:
                            # Clean the URL
                            if "google.com/url?" in href:
                                parsed = urllib.parse.urlparse(href)
                                q_param = urllib.parse.parse_qs(parsed.query).get('q', [''])[0]
                                if q_param: href = q_param
                            
                            # Handle Nitter links (relative or absolute)
                            if is_nitter:
                                if not href.startswith('http'):
                                    href = f"https://x.com{href}"
                                else:
                                    # Convert nitter domain back to x.com
                                    href = re.sub(r'https?://nitter\.[^/]+', 'https://x.com', href)
                            
                            href = href.split('?')[0].split('#')[0].replace('http:', 'https:')
                            if 'x.com' in href:
                                if username and f'/{username.lower()}/' not in href.lower():
                                    continue
                                return href
                    
                    # Special check for search snippets or raw HTML matches
                    raw_html = await self.page.content()
                    # Catch both x.com links and nitter relative status links
                    matches = re.findall(r'/(?:[^/ ]+)/status/\d+', raw_html)
                    for match in matches:
                        if '/search' in match or '/status/s' in match: continue
                        full_url = f"https://x.com{match}"
                        if username and f'/{username.lower()}/' not in full_url.lower():
                            continue
                        return full_url

                except Exception as e:
                    print(f"{source['name']} search variation failed: {e}")
            
        return None

    async def scrape_by_text(self, text: str, username: Optional[str] = None) -> Optional[Dict]:
        """Find and scrape a tweet by its text"""
        url = await self.find_tweet_url_by_text(text, username)
        if url:
            return await self.scrape_status_url(url)
        return None

    async def scrape_from_json(self, json_path: str, output_file: Optional[str] = None, default_username: Optional[str] = None) -> List[Dict]:
        """Scrape multiple tweets from a JSON file containing texts"""
        print(f"Reading input JSON from {json_path}...")
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return []
            
        if not isinstance(data, list):
            print("Error: JSON must be a list of objects.")
            return []
            
        results = []
        for i, item in enumerate(data):
            text = item.get('text')
            if not text:
                print(f"Skipping item {i}: No 'text' field found.")
                continue
                
            username = item.get('username') or item.get('handle') or default_username
            print(f"[{i+1}/{len(data)}] Processing: {text[:50]}...")
            
            tweet_data = await self.scrape_by_text(text, username)
            if tweet_data:
                results.append(tweet_data)
                print(f"✓ Successfully scraped: {tweet_data['url']}")
            else:
                print(f"✗ Could not find/scrape tweet: {text[:50]}...")
            
            # Small delay between searches to be nice
            await asyncio.sleep(random.uniform(2, 5))
            
        if output_file and results:
            self._save_tweets(results, output_file)
            
        return results

    def _parse_tweet(self, tweet_element, username: str) -> Optional[Dict]:
        """Parse individual tweet element"""
        try:
            # Extract tweet text
            text_element = tweet_element.find('div', {'data-testid': 'tweetText'})
            if not text_element:
                return None
                
            tweet_text = text_element.get_text(strip=True)
            if not tweet_text:
                return None
            
            # Check if it's a reply
            reply_element = tweet_element.find('div', {'data-testid': 'socialContext'})
            is_reply = reply_element is not None
            
            # Extract timestamp
            time_element = tweet_element.find('time')
            timestamp = time_element.get('datetime') if time_element else None
            
            # Extract metrics
            metrics = self._extract_metrics(tweet_element)
            
            # Extract tweet URL
            link_elements = tweet_element.find_all('a', href=True)
            tweet_url = ""
            for link in link_elements:
                href = link['href']
                if '/status/' in href:
                    tweet_url = f"https://x.com{href}"
                    break
            
            return {
                'username': username,
                'text': tweet_text,
                'timestamp': timestamp,
                'url': tweet_url,
                'is_reply': is_reply,
                'replies': metrics.get('replies', 0),
                'retweets': metrics.get('retweets', 0),
                'likes': metrics.get('likes', 0),
                'views': metrics.get('views', 0),
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            return None

    def _parse_number(self, text: str) -> int:
        """Parse numeric value from text with K/M suffixes"""
        try:
            import re
            # Find numbers with optional K/M suffix
            text = text.replace(',', '')
            match = re.search(r'(\d+(?:\.\d+)?)\s*([KM]?)', text)
            if not match: return 0
            
            num = float(match.group(1))
            suffix = match.group(2)
            
            if suffix == 'K': return int(num * 1000)
            elif suffix == 'M': return int(num * 1000000)
            else: return int(num)
        except:
            return 0

    def _extract_metrics(self, tweet_element) -> Dict[str, int]:
        """Extract engagement metrics from tweet"""
        metrics = {'replies': 0, 'retweets': 0, 'likes': 0, 'views': 0}
        try:
            all_elements = tweet_element.find_all(attrs={"aria-label": True})
            for element in all_elements:
                label = element.get('aria-label', '').lower()
                if 'reply' in label and 'replies' not in label:
                    metrics['replies'] = self._parse_number(label)
                elif 'repost' in label or 'retweet' in label:
                    metrics['retweets'] = self._parse_number(label)
                elif 'like' in label and 'likes' not in label:
                    metrics['likes'] = self._parse_number(label)
                elif 'view' in label:
                    metrics['views'] = self._parse_number(label)
        except: pass
        return metrics

    def _save_tweets(self, tweets: List[Dict], filename: str):
        """Save tweets to file"""
        # Ensure the output directory exists
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        json_file = f"{filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tweets, f, indent=2, ensure_ascii=False)
        csv_file = f"{filename}.csv"
        pd.DataFrame(tweets).to_csv(csv_file, index=False, encoding='utf-8')
        print(f"\n✓ Tweets saved to:\n  - {json_file}\n  - {csv_file}")

    def save_to_supabase(self, tweets: List[Dict]) -> int:
        """Save tweets to Supabase database with deduplication"""
        if not supabase:
            print("Warning: Supabase client not initialized. Skipping database save.")
            return 0
        
        if not tweets:
            print("No tweets to save to Supabase.")
            return 0
        
        saved_count = 0
        for tweet in tweets:
            try:
                # Prepare data for Supabase
                tweet_data = {
                    'text': tweet.get('text', ''),
                    'timestamp': tweet.get('timestamp'),
                    'url': tweet.get('url', '')
                }
                
                # Use upsert to handle duplicates (url is unique)
                result = supabase.table('tweets').upsert(
                    tweet_data,
                    on_conflict='url'
                ).execute()
                
                saved_count += 1
                print(f"✓ Saved tweet to Supabase: {tweet_data['text'][:50]}...")
                
            except Exception as e:
                print(f"✗ Error saving tweet to Supabase: {e}")
                continue
        
        print(f"\n✓ Total tweets saved to Supabase: {saved_count}/{len(tweets)}")
        return saved_count

async def main():
    parser = argparse.ArgumentParser(description='Scrape tweets from Twitter/X account')
    parser.add_argument('username', nargs='?', help='Twitter/X username to scrape')
    parser.add_argument('--max-tweets', type=int, default=20, help='Maximum number of tweets to scrape')
    parser.add_argument('--include-replies', action='store_true', help='Include reply tweets')
    parser.add_argument('--output', '-o', help='Output file name')
    parser.add_argument('--visible', action='store_true', help='Show browser window')
    parser.add_argument('--login-user', help='Twitter handle/email for login')
    parser.add_argument('--login-pass', help='Twitter password')
    parser.add_argument('--login-email', help='Account email for bypass')
    parser.add_argument('--timeframe', choices=['day', 'week', 'month'], help='Scrape tweets from this timeframe')
    parser.add_argument('--since', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--until', help='End date (YYYY-MM-DD)')
    parser.add_argument('--input-json', help='Path to JSON file with tweet texts to scrape')
    
    args = parser.parse_args()
    if not args.output:
        import os
        os.makedirs("data", exist_ok=True)
        suffix = args.username if args.username else "batch"
        args.output = os.path.join("data", f"tweets_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    async with TwitterScraper(headless=not args.visible) as scraper:
        # Only attempt login if credentials are provided
        if args.login_user and args.login_pass:
            await scraper.login(args.login_user, args.login_pass, args.login_email)
            
        if args.input_json:
            print(f"Processing batch scrape from: {args.input_json}")
            if args.username:
                print(f"Using '@{args.username}' as default username for search.")
            tweets = await scraper.scrape_from_json(args.input_json, args.output, args.username)
        else:
            if not args.username:
                print("Error: Either username or --input-json must be provided.")
                return
                
            tweets = await scraper.scrape_tweets(
                username=args.username,
                max_tweets=args.max_tweets,
                include_replies=args.include_replies,
                output_file=args.output,
                timeframe=args.timeframe,
                since=args.since,
                until=args.until
            )
        
        if tweets:
            target = f"@{args.username}" if args.username else "batch"
            print(f"\n✓ Successfully scraped {len(tweets)} tweets for {target}")
            print(f"\nSample tweet:\n  Time: {tweets[0]['timestamp']}\n  Text: {tweets[0]['text'][:100]}...")
            
            # Save to Supabase if configured
            scraper.save_to_supabase(tweets)
        else:
            target = f"@{args.username}" if args.username else "batch input"
            print(f"\n✗ No tweets found for {target}")


if __name__ == "__main__":
    asyncio.run(main())