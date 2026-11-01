import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables from .env if present
load_dotenv(PROJECT_ROOT / ".env")

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default database / cache file paths
CACHE_DB_PATH = DATA_DIR / "watch_history.db"
VECTOR_INDEX_PATH = DATA_DIR / "vector_index.json"

# Categorization heuristics
PRODUCTIVE_CATEGORIES = {
    "Education",
    "Science & Technology",
    "Howto & Style",
    "Programming",
    "Tutorial",
    "Lecture",
    "Documentary",
    "Productivity",
    "Books & Literature"
}

DISTRACTIVE_CATEGORIES = {
    "Gaming",
    "Entertainment",
    "Comedy",
    "Shorts",
    "Memes",
    "Celebrity",
    "Vlog",
    "Reaction"
}

NEUTRAL_CATEGORIES = {
    "Music",
    "News & Politics",
    "Film & Animation",
    "Autos & Vehicles",
    "Sports",
    "Pets & Animals",
    "Travel & Events",
    "General"
}
