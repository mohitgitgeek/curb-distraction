import re
import requests
from typing import List, Dict, Any, Optional
from src.config import YOUTUBE_API_KEY

CATEGORY_MAPPING = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "43": "Shows",
    "44": "Trailers",
}

def parse_iso8601_duration(duration_str: str) -> int:
    """Convert ISO 8601 duration string like 'PT1H15M30S' to total seconds."""
    if not duration_str:
        return 0
    pattern = r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
    match = re.match(pattern, duration_str)
    if not match:
        return 0
    parts = match.groupdict()
    hours = int(parts.get("hours") or 0)
    minutes = int(parts.get("minutes") or 0)
    seconds = int(parts.get("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds

class YouTubeAPIClient:
    """Enriches video records using YouTube Data API v3 or smart fallback heuristics."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3/videos"

    def enrich_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw history records and adds video duration, category, channel, and tags.
        Uses YouTube API when api_key is available; otherwise applies smart heuristic classifier.
        """
        video_ids = [r["video_id"] for r in records if r.get("video_id") and not r.get("category")]
        unique_ids = list(dict.fromkeys(video_ids))

        api_data = {}
        if self.api_key and unique_ids:
            try:
                api_data = self._fetch_from_api_batch(unique_ids)
            except Exception as e:
                print(f"[Warning] YouTube API call failed ({e}); falling back to heuristic engine.")

        # Enrich records
        enriched = []
        for record in records:
            url = record.get("url", "")
            title = record.get("title", "")
            is_short = bool(
                record.get("is_shorts") or
                "/shorts/" in url or 
                "#shorts" in title.lower() or 
                "#short" in title.lower() or
                record.get("type") == "shorts"
            )
            record["is_shorts"] = is_short
            if is_short:
                record["type"] = "shorts"

            vid = record.get("video_id")
            if vid and vid in api_data:
                meta = api_data[vid]
                record["duration_sec"] = meta["duration_sec"]
                record["duration_fmt"] = self._format_duration(meta["duration_sec"])
                record["category"] = "Shorts" if is_short else meta["category"]
                record["channel"] = meta["channel"]
                record["tags"] = meta["tags"]
                record["description"] = meta["description"]
            else:
                # Apply category inference
                if is_short:
                    record["category"] = "Shorts"
                elif not record.get("category"):
                    inferred_cat = self._infer_category_from_title(title, record.get("search_query"), url=url)
                    record["category"] = inferred_cat

                if not record.get("duration_sec"):
                    browser_sec = record.get("browser_recorded_duration_sec", 0)
                    if is_short:
                        record["duration_sec"] = min(browser_sec, 60) if browser_sec > 5 else 45
                    else:
                        record["duration_sec"] = browser_sec if browser_sec > 30 else 720
                    record["duration_fmt"] = self._format_duration(record["duration_sec"])

                if not record.get("channel"):
                    record["channel"] = "YouTube Creator"
                if not record.get("tags"):
                    record["tags"] = []
                if not record.get("description"):
                    record["description"] = ""

            # Ensure Shorts are always categorized as Shorts
            if is_short:
                record["category"] = "Shorts"

            enriched.append(record)

        return enriched

    def _fetch_from_api_batch(self, video_ids: List[str], chunk_size: int = 50) -> Dict[str, Dict[str, Any]]:
        metadata = {}
        for i in range(0, len(video_ids), chunk_size):
            chunk = video_ids[i : i + chunk_size]
            params = {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(chunk),
                "key": self.api_key,
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"[Warning] YouTube API error: {resp.status_code} - {resp.text}")
                continue

            data = resp.json()
            for item in data.get("items", []):
                vid = item["id"]
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})

                cat_id = snippet.get("categoryId", "")
                cat_name = CATEGORY_MAPPING.get(cat_id, "General")

                duration_sec = parse_iso8601_duration(content_details.get("duration", ""))
                metadata[vid] = {
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", "Unknown Channel"),
                    "category": cat_name,
                    "duration_sec": duration_sec,
                    "tags": snippet.get("tags", []),
                    "description": snippet.get("description", "")[:400],
                }

        return metadata

    def _infer_category_from_title(self, title: str, query: Optional[str] = None, url: str = "") -> str:
        """Rule-based NLP classifier when YouTube API key is missing."""
        if "/shorts/" in (url or "") or "#shorts" in (title or "").lower() or "#short" in (title or "").lower():
            return "Shorts"

        text = f"{title} {query or ''}".lower()

        # Distraction / Gaming
        if any(w in text for w in [
            "gameplay", "walkthrough", "speedrun", "minecraft", "gta", "fortnite",
            "valorant", "roblox", "elden ring", "twitch", "gaming", "bgmi", "pubg",
            "free fire", "playthrough", "gamer", "stream"
        ]):
            return "Gaming"

        # Distraction / Comedy & Memes
        if any(w in text for w in [
            "meme", "try not to laugh", "funniest", "fails", "comedy", "standup",
            "prank", "roast", "parody", "funny", "jokes", "humor"
        ]):
            return "Comedy"

        # Distraction / Entertainment, Shorts & Drama
        if any(w in text for w in [
            "tiktok", "shorts", "shortvideo", "#shorts", "#short", "satisfying",
            "reaction", "drama", "unboxing", "celebrity", "gossip", "vlog", "mrbeast",
            "kdrama", "k-drama", "anime", "web series", "episode", "season", "trailer",
            "teaser", "status", "edit", "reels", "cinematic", "scene", "clip"
        ]):
            return "Entertainment"

        # Productive / Tech / Learning
        if any(w in text for w in [
            "tutorial", "python", "javascript", "react", "programming", "coding",
            "software", "api", "docker", "machine learning", "ai", "deep learning",
            "algorithms", "system design", "data structures", "linux", "git",
            "web dev", "frontend", "backend", "sql", "database", "java", "c++",
            "developer", "framework", "architecture", "devops"
        ]):
            return "Science & Technology"

        if any(w in text for w in [
            "lecture", "course", "calculus", "linear algebra", "physics", "chemistry",
            "biology", "history", "university", "mit", "stanford", "education",
            "how to", "explained", "crash course", "summary", "notes", "concept"
        ]):
            return "Education"

        if any(w in text for w in [
            "deep work", "productivity", "study with me", "focus", "habit",
            "atomic habits", "time management", "pomodoro", "routine", "discipline"
        ]):
            return "Productivity"

        # Neutral
        if any(w in text for w in [
            "lofi", "song", "music", "album", "soundtrack", "concert", "beat",
            "chillhop", "playlist", "audio", "remix", "lyrics", "cover", "instrumental"
        ]):
            return "Music"

        if any(w in text for w in [
            "news", "politics", "election", "debate", "bbc", "cnn", "parliament", "breaking"
        ]):
            return "News & Politics"

        return "General"

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if seconds <= 0:
            return "0m"
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m {secs}s" if mins < 5 else f"{mins}m"
