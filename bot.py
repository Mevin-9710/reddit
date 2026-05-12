#!/usr/bin/env python3
"""
Reddit Bot - ALL IN ONE
"""

import asyncio
import time
import random
import os
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

# User agents for rotating
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

BASE_DIR = Path(__file__).parent

BROWSER_PROFILE = BASE_DIR / "browser_profile"

SUBREDDITS = [
    "startups", "entrepreneur", "SaaS",
    "GrowthHacking", "indiehackers", "webdev",
    "programming", "nocode", "microsaas", "EntrepreneurRideAlong"
]
POSTS_PER_SUBREDDIT = 2
MIN_DELAY = 360   # 6 minutes
MAX_DELAY = 3600  # 60 minutes

LOG_FILE = BASE_DIR / "bot.log"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Create timestamped run folder for screenshots
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
SCREENSHOTS_RUN_DIR = SCREENSHOTS_DIR / f"run_{RUN_ID}"
SCREENSHOTS_RUN_DIR.mkdir(exist_ok=True)

# Clear old screenshots (keep only last 2 runs)
old_runs = sorted([d for d in SCREENSHOTS_DIR.iterdir() if d.is_dir() and d.name.startswith("run_")])
if len(old_runs) > 2:
    for old_run in old_runs[:-2]:
        import shutil
        shutil.rmtree(old_run)
        print(f"Cleaned up: {old_run}")


class LiveLogger:
    """Logs to both console and file"""

    def __init__(self, log_file: Path = LOG_FILE):
        self.log_file = log_file
        self.log_file.write_text("")

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def info(self, msg):
        self.log(msg, "INFO")
    def success(self, msg):
        self.log(msg, "SUCCESS")
    def error(self, msg):
        self.log(msg, "ERROR")
    def warning(self, msg):
        self.log(msg, "WARN")
    def wait(self, msg):
        self.log(msg, "WAIT")


class SessionManager:
    """Simple session cookie manager"""

    def __init__(self, session_file: Path = BASE_DIR / "session.json"):
        self.session_file = session_file

    def save_cookies(self, cookies: list) -> None:
        with open(self.session_file, "w") as f:
            json.dump(cookies, f)

    def load_cookies(self) -> Optional[list]:
        if not self.session_file.exists():
            return None
        with open(self.session_file, "r") as f:
            return json.load(f)

    def has_session(self) -> bool:
        return self.session_file.exists() and self.load_cookies() is not None


logger = LiveLogger()


class RedditBot:
    def __init__(self):
        self.session_mgr = SessionManager()
        self.comments_posted = 0
        self.failed = 0
        self.total_posts = len(SUBREDDITS) * POSTS_PER_SUBREDDIT
        self.current_action = "Idle"

        self.http = requests.Session()
        self.http.headers.update({
            "User-Agent": get_random_user_agent(),
            "Referer": "https://www.reddit.com"
        })

    def _random_delay(self, min_sec: int = MIN_DELAY, max_sec: int = MAX_DELAY):
        delay = random.uniform(min_sec, max_sec)
        self.current_action = f"Next post in {int(delay/60)} min"
        logger.wait(f"Next post in {int(delay/60)} min ({int(delay)}s)...")

        # Countdown in terminal
        start_time = time.time()
        while time.time() - start_time < delay:
            remaining = delay - (time.time() - start_time)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            print(f"\r  Next post in {mins:02d}:{secs:02d}...", end="", flush=True)
            time.sleep(1)
        print()

    def _get_new_posts(self, subreddit: str) -> list:
        self.current_action = f"Fetching r/{subreddit}"
        logger.info(f"Fetching posts from r/{subreddit}...")

        try:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={POSTS_PER_SUBREDDIT * 2}"
            response = self.http.get(url, timeout=15)

            if response.status_code != 200:
                logger.error(f"Failed to fetch r/{subreddit}: HTTP {response.status_code}")
                return []

            data = response.json()
            posts = data.get("data", {}).get("children", [])
            results = []
            for post in posts[:POSTS_PER_SUBREDDIT * 2]:
                p = post.get("data", {})
                if p.get("title") and p.get("permalink"):
                    results.append({
                        "title": p.get("title"),
                        "permalink": f"https://www.reddit.com{p.get('permalink')}",
                        "id": p.get("id")
                    })
                    if len(results) >= POSTS_PER_SUBREDDIT:
                        break
            return results

        except Exception as e:
            logger.error(f"Failed to fetch r/{subreddit}: {e}")
            return []

    async def _generate_comment_gemini(self, page, post_title: str, subreddit: str) -> str:
        timestamp = datetime.now().strftime("%H%M%S")

        logger.info("Opening Gemini...")
        await page.goto("https://gemini.google.com/app", timeout=60000)
        await asyncio.sleep(3)
        await page.screenshot(path=str(SCREENSHOTS_DIR / f"gemini_{timestamp}_01_loaded.png"))

        prompt = f"""Write one short Reddit comment (max 25 words) for this post in r/{subreddit}:

Title: {post_title}

Write ONLY the comment text, nothing else:"""

        logger.info("Typing prompt...")
        textarea = page.locator('textarea')
        if await textarea.count() > 0:
            await textarea.fill(prompt)
        else:
            textarea = page.locator('[contenteditable="true"]').first
            await textarea.fill(prompt)

        await asyncio.sleep(1)
        await page.screenshot(path=str(SCREENSHOTS_DIR / f"gemini_{timestamp}_02_prompt.png"))

        logger.info("Sending to Gemini...")
        send_btn = page.locator('button[aria-label="Send"]')
        if await send_btn.count() > 0:
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")

        logger.info("Waiting for Gemini response...")
        await asyncio.sleep(10)
        await page.screenshot(path=str(SCREENSHOTS_DIR / f"gemini_{timestamp}_03_response.png"))

        try:
            all_divs = await page.locator('[id*="model-response-message-content"]').all()
            if all_divs:
                comment = await all_divs[-1].inner_text()
                if comment and len(comment.strip()) > 5:
                    return comment.strip()[:200]
        except Exception as e:
            logger.error(f"Failed to get Gemini response: {e}")

        raise Exception("Could not extract comment from Gemini")

    async def _post_comment(self, page, permalink: str, comment: str, screenshot_prefix: str = "") -> bool:
        try:
            self.current_action = "Posting comment"
            logger.info(f"Going to: {permalink}")
            await page.goto(permalink, timeout=30000)
            await asyncio.sleep(4)

            if screenshot_prefix:
                await page.screenshot(path=str(SCREENSHOTS_DIR / f"run_{RUN_ID}.png"))

            # Scroll to bottom where the comment composer is
            logger.info("Scrolling to comments...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(3)

            await page.screenshot(path=str(SCREENSHOTS_DIR / f"{screenshot_prefix}_scrolled.png"))

            # Click the comment composer to activate it
            logger.info("Activating comment form...")
            await page.evaluate('''() => {
                const wrapper = document.querySelector('#fixed-comment-composer-wrapper');
                if (wrapper) wrapper.style.display = 'block';
            }''')
            await asyncio.sleep(1)

            # Get the shadow root and click the input
            await page.screenshot(path=str(SCREENSHOTS_DIR / f"{screenshot_prefix}_activated.png"))

            # Find the shadow root input
            clicked = await page.evaluate('''() => {
                const textarea = document.querySelector("#fixed-comment-composer-wrapper > shreddit-async-loader > comment-composer-host > faceplate-tracker:nth-child(1) > faceplate-textarea-input");
                if (textarea && textarea.shadowRoot) {
                    const input = textarea.shadowRoot.querySelector("label > div");
                    if (input) {
                        input.click();
                        return true;
                    }
                }
                return false;
            }''')
            logger.info(f"Clicked input via shadow root: {clicked}")
            await asyncio.sleep(1)

            # Type the comment using keyboard.type
            logger.info(f"Typing comment: {comment[:50]}...")
            await page.keyboard.type(comment, delay=80)
            await asyncio.sleep(1)

            await page.screenshot(path=str(SCREENSHOTS_DIR / f"{screenshot_prefix}_typed.png"))

            # Click the Comment button (NOT Reply)
            logger.info("Clicking Comment button...")
            clicked = await page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                // Find button with exact text "Comment" (not Reply)
                for (let btn of buttons) {
                    const text = btn.textContent.trim();
                    if (text === 'Comment') {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }''')

            logger.info(f"Comment button clicked: {clicked}")

            if clicked:
                await asyncio.sleep(5)
                await page.screenshot(path=str(SCREENSHOTS_DIR / f"{screenshot_prefix}_after.png"))
                logger.info("Comment posted!")
                return True

            logger.error("Could not post comment")
            await page.screenshot(path=str(SCREENSHOTS_DIR / f"{screenshot_prefix}_error.png"))
            return False

        except Exception as e:
            logger.error(f"Failed to post comment: {e}")
            return False

    def print_status(self):
        progress = f"{self.comments_posted + self.failed}/{self.total_posts}"
        status = f"Progress: {progress} | Posted: {self.comments_posted} | Failed: {self.failed}"
        print(f"\r{status} | {self.current_action}    ", end="", flush=True)

    async def run(self):
        print("\n" + "=" * 60)
        logger.info("Reddit Bot - ONE BROWSER SESSION")
        print("=" * 60)
        logger.info("Browser will open. LOG IN to Reddit.")
        logger.info("Browser stays OPEN the whole time.")
        print("=" * 60 + "\n")

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                str(BROWSER_PROFILE),
                headless=False,
                args=['--start-maximized', '--no-sandbox'],
                viewport={"width": 1400, "height": 900}
            )
            page = context.pages[0] if context.pages else context.new_page()

            logger.info("Browser opened with saved profile.")
            logger.info("Opening Reddit...")
            await page.goto("https://www.reddit.com", timeout=60000)
            await asyncio.sleep(3)

            try:
                login_check = await page.locator('a[href*="/login"], [data-testid="login-button"]').count()
                if login_check > 0:
                    logger.info("Not logged in - please login in the browser...")
                    await asyncio.sleep(30)
                    await page.screenshot(path=str(SCREENSHOTS_DIR / "reddit_login_screen.png"))
            except:
                pass

            await page.screenshot(path=str(SCREENSHOTS_DIR / "reddit_start.png"))

            print("\n" + "!" * 60)
            print("Starting automation in 5 seconds...")
            print("Browser will stay OPEN the whole time.")
            print("!" * 60 + "\n")

            await asyncio.sleep(5)

            cookies = await context.cookies()
            session_mgr = SessionManager()
            session_mgr.save_cookies(cookies)

            for c in cookies:
                self.http.cookies.set(c["name"], c["value"], domain=".reddit.com")

            logger.info("Reddit login saved!")
            print("\nStarting automation...\n")

            for i, subreddit in enumerate(SUBREDDITS, 1):
                logger.info(f"=== [{i}/{len(SUBREDDITS)}] r/{subreddit} ===")

                posts = self._get_new_posts(subreddit)

                if not posts:
                    logger.warning(f"No posts found in r/{subreddit}")
                    continue

                for j, post in enumerate(posts[:POSTS_PER_SUBREDDIT], 1):
                    post_num = (i - 1) * POSTS_PER_SUBREDDIT + j
                    title_short = post['title'][:45] + "..." if len(post['title']) > 45 else post['title']
                    self.current_action = f"Post {post_num}/{self.total_posts}: {title_short}"
                    logger.info(f"Post {j}/{len(posts)}: {title_short}")

                    try:
                        self.current_action = "Generating comment via Gemini"
                        comment = await self._generate_comment_gemini(page, post["title"], subreddit)
                        logger.info(f"Generated: {comment[:50]}...")
                    except Exception as e:
                        logger.error(f"Failed to generate: {e}")
                        self.failed += 1
                        self.print_status()
                        print()
                        continue

                    success = await self._post_comment(page, post["permalink"], comment, f"r{subreddit}_p{post_num}")

                    if success:
                        self.comments_posted += 1
                        logger.success(f"Comment posted! ({self.comments_posted}/{self.total_posts})")
                    else:
                        self.failed += 1
                        logger.error("Failed to post comment")

                    self.print_status()
                    print()

                    if j < len(posts):
                        self._random_delay()

                if i < len(SUBREDDITS):
                    logger.info("Moving to next subreddit...")
                    self._random_delay(min_sec=15, max_sec=25)

            print("\n" + "=" * 60)
            logger.info("Automation complete!")
            print(f"Posted: {self.comments_posted} | Failed: {self.failed}")
            print("=" * 60)

            await context.close()
            logger.info("Browser closed.")
            print("Bot finished. Exiting.")


async def main():
    try:
        bot = RedditBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())