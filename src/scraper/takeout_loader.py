import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.scraper.browser_history import extract_video_id

class TakeoutHistoryLoader:
    """Parses Google Takeout watch-history.json and generates synthetic history if needed."""

    @staticmethod
    def load_from_json(file_path: Path) -> List[Dict[str, Any]]:
        """Load records from Google Takeout watch-history.json."""
        if not file_path.exists():
            raise FileNotFoundError(f"Takeout file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for item in data:
            url = item.get("titleUrl", "")
            video_id = extract_video_id(url)
            raw_title = item.get("title", "")
            # Takeout titles often start with 'Watched '
            title = re.sub(r"^Watched\s+", "", raw_title)

            # Parse timestamp e.g. "2026-10-31T14:22:10.000Z"
            time_str = item.get("time", "")
            try:
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

            channel_title = "Unknown Channel"
            subtitles = item.get("subtitles", [])
            if subtitles and isinstance(subtitles, list) and len(subtitles) > 0:
                channel_title = subtitles[0].get("name", "Unknown Channel")

            records.append({
                "type": "video",
                "url": url,
                "video_id": video_id,
                "search_query": None,
                "title": title,
                "channel": channel_title,
                "visited_at": dt.isoformat(),
                "date": dt.strftime("%Y-%m-%d"),
                "hour": dt.hour,
                "browser_recorded_duration_sec": 0,
                "browser": "Google Takeout",
            })

        return records

    @staticmethod
    def generate_demo_dataset() -> List[Dict[str, Any]]:
        """
        Generates realistic watch & search history over the past 7 days.
        Used for instant demo and evaluation if browser history is clean or on new machine.
        """
        import random
        from datetime import timedelta

        sample_items = [
            # Distractions / Entertainment / Gaming
            ("GTA 6 Full Map Leaks and Gameplay Analysis", "Gaming", 1260, "video", "M8Vz0B..."),
            ("Funniest Memes of 2026 Compilation #42", "Comedy", 940, "video", "K91..."),
            ("Twitch Streamer Loses Everything Live", "Entertainment", 1850, "video", "T2..."),
            ("Minecraft 100 Days Hardcore Survival", "Gaming", 3600, "video", "M100..."),
            ("Satisfying Soap Cutting & Slime Compilation", "Entertainment", 780, "video", "S9..."),
            ("Celebrity Drama: What Actually Happened?", "Entertainment", 1120, "video", "D4..."),
            ("Cat Videos to Watch While Procrastinating", "Comedy", 620, "video", "C1..."),
            ("TikTok Brainrot Compilation Vol 5", "Shorts", 450, "video", "B8..."),
            # Productive / Educational / Tech
            ("Building Scalable Microservices with Python and FastAPI", "Science & Technology", 2400, "video", "P1..."),
            ("Linear Algebra for Machine Learning - MIT Lecture 18", "Education", 3200, "video", "M18..."),
            ("How to Build RAG Systems with Vector Databases", "Science & Technology", 1950, "video", "R1..."),
            ("Deep Work Mastery: How to Eliminate Distractions & Focus", "Productivity", 1540, "video", "D1..."),
            ("System Design Interview: Designing YouTube and Netflix", "Education", 2800, "video", "S1..."),
            ("Clean Code Principles in Modern Python 3.14", "Science & Technology", 1680, "video", "C3..."),
            ("Calculus 3: Multiple Integrals Explained Simply", "Education", 2100, "video", "C9..."),
            # Neutral / Music / Podcasts
            ("Lofi Hip Hop Radio - Beats to Relax/Study to", "Music", 7200, "video", "L1..."),
            ("Huberman Lab: Optimize Your Dopamine & Motivation", "Education", 5400, "video", "H1..."),
        ]

        now = datetime.now(timezone.utc)
        records = []

        for day_offset in range(7):
            day_date = now - timedelta(days=day_offset)
            # Pick 6 to 12 videos per day
            num_videos = random.randint(6, 11)
            for _ in range(num_videos):
                title, cat, duration, rec_type, vid_id = random.choice(sample_items)
                # Random hour of day (biased towards afternoon/evening)
                hour = random.choice([9, 11, 14, 15, 16, 20, 21, 22, 23])
                minute = random.randint(0, 59)
                item_time = day_date.replace(hour=hour, minute=minute)

                records.append({
                    "type": rec_type,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "video_id": vid_id,
                    "search_query": None,
                    "title": title,
                    "channel": f"{cat} Creator Hub",
                    "category": cat,
                    "duration_sec": duration,
                    "visited_at": item_time.isoformat(),
                    "date": item_time.strftime("%Y-%m-%d"),
                    "hour": hour,
                    "browser_recorded_duration_sec": duration,
                    "browser": "Demo Dataset",
                })

        records.sort(key=lambda r: r["visited_at"], reverse=True)
        return records
