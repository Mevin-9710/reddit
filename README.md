# Reddit Comment Bot

An automated Reddit bot that generates and posts AI-powered comments using Gemini. The bot visits 10 subreddits, gets 2 newest posts from each, generates relevant comments using Google's Gemini AI, and posts them to Reddit.

## Features

- **AI-Powered Comments**: Uses Gemini to generate contextual, relevant comments
- **10 Subreddits**: Posts to 20 comments daily across multiple communities
- **Natural Timing**: Random 6-60 minute delays between posts to appear human
- **Persistent Browser**: Login once, session saved for future runs
- **Live Logs**: Real-time terminal output with countdown timer
- **Screenshot Debugging**: Screenshots saved for each run

## Prerequisites

- Python 3.8+
- Google Chrome browser
- Reddit account
- Gemini (free - no API key needed)

## Installation

1. **Clone or download the project**
   ```bash
   cd reddit-bot
   ```

2. **Install Python dependencies**
   ```bash
   pip install playwright requests python-dotenv
   playwright install chromium
   ```

3. **Create environment file** (copy `.env.example` to `.env` if needed)
   ```bash
   # .env file is optional - bot uses browser session for auth
   ```

## Running the Bot

```bash
python3 bot.py
```

**First run:**
1. Browser opens with Reddit
2. Log in to your Reddit account
3. Wait 30 seconds or close the login tab
4. Automation starts automatically

**Subsequent runs:**
- Browser opens with your saved session
- Automation starts immediately

## Configuration

Edit these variables in `bot.py` if needed:

```python
SUBREDDITS = [
    "startups", "entrepreneur", "SaaS",
    "GrowthHacking", "indiehackers", "webdev",
    "programming", "nocode", "microsaas", "EntrepreneurRideAlong"
]
POSTS_PER_SUBREDDIT = 2
MIN_DELAY = 360   # 6 minutes (minimum between posts)
MAX_DELAY = 3600  # 60 minutes (maximum between posts)
```

## How It Works

1. **Launches browser** with persistent profile (saves your Reddit session)
2. **Fetches newest posts** from each subreddit via Reddit API
3. **Opens Gemini** in the same browser tab
4. **Generates comment** based on post title
5. **Navigates to post** and posts the comment
6. **Waits 6-60 minutes** randomly before next post
7. **Repeats** until all 20 comments are posted

## Project Structure

```
reddit-bot/
├── bot.py              # Main bot script (all-in-one)
├── requirements.txt    # Python dependencies
├── screenshots/        # Debug screenshots (gitignored)
├── browser_profile/    # Browser session data (gitignored)
├── session.json        # Reddit cookies (gitignored)
└── README.md
```

## Troubleshooting

**Bot not clicking the comment input?**
- Screenshots are saved in `screenshots/run_*/` for debugging
- Check if Reddit has changed their UI

**Comments not posting?**
- Make sure you're logged in to Reddit
- Check the browser_profile folder exists

**Gemini not responding?**
- Requires Google account logged in to Gemini
- Or use VPN if Gemini is blocked in your region

## License

MIT License