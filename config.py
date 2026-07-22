import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///announcement_bot.db")

# Pagination
GROUPS_PER_PAGE: int = 10
ANNOUNCEMENTS_PER_PAGE: int = 5

# Broadcast Settings
BROADCAST_DELAY: float = 0.1
MAX_RETRIES: int = 3
RETRY_DELAY: float = 2.0

# Message Limits
MAX_MEDIA_GROUP_SIZE: int = 9
MAX_VIDEO_DURATION: int = 20
MAX_CAPTION_LENGTH: int = 1024

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is not set!")
