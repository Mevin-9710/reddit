"""
Configuration file for Reddit Bot.
Edit these settings directly or set via environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===== SUBREDDITS =====
# Add or remove subreddits from this list
SUBREDDITS = [
    "startups", "entrepreneur", "SaaS",
    "GrowthHacking", "indiehackers", "webdev",
    "programming", "nocode", "microsaas", "EntrepreneurRideAlong"
]

# ===== POSTS PER SUBREDDIT =====
# Number of posts to comment on in each subreddit
POSTS_PER_SUBREDDIT = int(os.getenv("POSTS_PER_SUBREDDIT", "2"))

# ===== DELAYS (in seconds) =====
# Delay between posts in the same subreddit
MIN_DELAY = int(os.getenv("MIN_DELAY", "600"))   # 10 minutes
MAX_DELAY = int(os.getenv("MAX_DELAY", "1200")) # 20 minutes

# Delay between subreddits
MIN_SUBREDDIT_DELAY = int(os.getenv("MIN_SUBREDDIT_DELAY", "60"))   # 60 seconds
MAX_SUBREDDIT_DELAY = int(os.getenv("MAX_SUBREDDIT_DELAY", "90"))   # 90 seconds

# ===== SCHEDULER =====
# Time to run the bot daily (UTC)
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "06:00")