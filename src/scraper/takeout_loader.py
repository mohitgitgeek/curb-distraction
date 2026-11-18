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

    @staticmethod
    def generate_range_dataset(start_date: str = "2026-11-02", end_date: str = "2026-11-14") -> List[Dict[str, Any]]:
        """
        Generates realistic YouTube watch history specifically covering a specified date range.
        Enables exploration of historical timeframes (e.g. November 2 to 14).
        """
        import random
        from datetime import datetime, timedelta, timezone

        sample_library = [
            # YouTube Shorts (Tagged distractive, 45s)
            ("Quick Pasta Hack in 45 Seconds #shorts #cooking", "Shorts", 45, "shorts", "sh_pst_01", "Gordon Ramsay Shorts", ["pasta", "cooking", "shorts"]),
            ("Why Sherman Tanks Were Feared #shorts #history", "Shorts", 45, "shorts", "sh_shm_02", "History Vault", ["history", "military", "tanks", "shorts"]),
            ("When the AI Code Actually Works First Try #shorts", "Shorts", 45, "shorts", "sh_cde_03", "Tech Bro Laughs", ["coding", "python", "programming", "shorts"]),
            ("Craziest Physics Experiment You Didn't Know #shorts", "Shorts", 45, "shorts", "sh_phy_04", "Veritasium Clips", ["science", "physics", "shorts"]),
            ("Cat Refuses to Move from Keyboard #shorts #funny", "Shorts", 45, "shorts", "sh_cat_05", "Animal Antics", ["comedy", "cat", "memes", "shorts"]),
            ("Top 5 VS Code Shortcuts You Must Know #shorts", "Shorts", 45, "shorts", "sh_vsc_06", "CodeWithAntonio", ["coding", "programming", "shorts"]),
            ("The Ultimate Crispy Fried Chicken Recipe #shorts", "Shorts", 45, "shorts", "sh_chk_07", "Cooking Hub", ["cooking", "food", "shorts"]),
            ("Instant Dopamine Trap - Stop Scrolling #shorts", "Shorts", 45, "shorts", "sh_dop_08", "Mindset Shift", ["productivity", "shorts"]),

            # Productive / Educational / Homework & Tech (Long-form)
            ("Building Full Stack APIs with Python, FastAPI and Postgres", "Science & Technology", 2800, "video", "lf_py_01", "ArjanCodes", ["python", "fastapi", "coding", "backend"]),
            ("Calculus 3: Double and Triple Integrals Solved Step by Step", "Education", 3100, "video", "lf_mat_02", "Professor Leonard", ["calculus", "math", "homework", "study"]),
            ("System Design Fundamentals: Microservices vs Monolith", "Education", 2400, "video", "lf_sys_03", "ByteByteGo", ["system design", "architecture", "software"]),
            ("Data Structures & Algorithms: Mastering Dynamic Programming", "Education", 3600, "video", "lf_dsa_04", "NeetCode", ["dsa", "coding", "algorithms", "homework"]),
            ("Deep Work Mastery: How to Protect Your Brain From Distractions", "Productivity", 1800, "video", "lf_foc_05", "Cal Newport Hub", ["deep work", "productivity", "focus"]),
            ("Operating Systems: Virtual Memory and Paging Explained", "Education", 2700, "video", "lf_os_06", "NPTEL Computer Science", ["operating systems", "study", "homework"]),
            ("Database Systems: Normalization (1NF, 2NF, 3NF, BCNF) Tutorial", "Education", 2200, "video", "lf_db_07", "Gate Smashers", ["database", "sql", "dbms", "homework"]),

            # Distractive / Gaming / Entertainment (Long-form)
            ("GTA 6 Underground Racing & Vehicle Physics Breakdown", "Gaming", 1500, "video", "lf_gm_01", "IGN", ["gta", "gaming", "entertainment"]),
            ("Funniest Standup Comedy Clips of 2026", "Comedy", 1200, "video", "lf_com_02", "Comedy Central", ["comedy", "funny", "standup"]),
            ("World of Tanks: Battleship Defense Line Showdown", "Gaming", 2100, "video", "lf_gm_03", "QuickyBaby", ["gaming", "tanks", "military"]),
            ("Most Absurd Internet Scandals Exposed", "Entertainment", 1650, "video", "lf_ent_04", "Coffeezilla", ["entertainment", "investigation"]),
            ("Streamer Tries Not To Laugh Challenge #18", "Comedy", 950, "video", "lf_com_05", "Daily Dose of Internet", ["comedy", "memes", "funny"]),

            # History / Naval / Military (Matching User Interests)
            ("Yamato's Secret Armor: How the Super Battleship Was Engineered", "Film & Animation", 1450, "video", "lf_ym_01", "Yarnhub", ["history", "military", "yamato", "navy"]),
            ("Why Tiger Tanks Broke Down in the Battle of Kursk", "Education", 1950, "video", "lf_tk_02", "Military History Visualized", ["history", "ww2", "tanks"]),

            # Music & Neutral
            ("Lofi Hip Hop Radio - Beats to Sleep/Chill/Study to", "Music", 7200, "video", "lf_mus_01", "Lofi Girl", ["music", "lofi", "study"]),
            ("Interstellar Soundtrack - Epic Hans Zimmer Live Suite", "Music", 3600, "video", "lf_mus_02", "Hans Zimmer", ["music", "soundtrack"])
        ]

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        
        current_dt = start_dt
        records = []

        while current_dt <= end_dt:
            # Generate 10 to 18 watch records per day
            num_records = random.randint(11, 17)
            # Create a realistic time sequence across morning, afternoon, evening
            hours_pool = [8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23]
            selected_hours = sorted(random.sample(hours_pool, min(num_records, len(hours_pool))))
            while len(selected_hours) < num_records:
                selected_hours.append(random.choice(hours_pool))
            selected_hours.sort()

            for h in selected_hours:
                title, cat, dur, r_type, vid_id, channel, tags = random.choice(sample_library)
                minute = random.randint(0, 59)
                item_time = current_dt.replace(hour=h, minute=minute, second=random.randint(0, 59))
                
                is_short = (r_type == "shorts") or ("#shorts" in title.lower()) or (cat == "Shorts")
                url = f"https://www.youtube.com/shorts/{vid_id}" if is_short else f"https://www.youtube.com/watch?v={vid_id}"

                records.append({
                    "type": "shorts" if is_short else "video",
                    "is_shorts": is_short,
                    "url": url,
                    "video_id": vid_id,
                    "search_query": None,
                    "title": title,
                    "channel": channel,
                    "category": "Shorts" if is_short else cat,
                    "duration_sec": 45 if is_short else dur,
                    "visited_at": item_time.isoformat(),
                    "date": item_time.strftime("%Y-%m-%d"),
                    "hour": h,
                    "browser_recorded_duration_sec": 45 if is_short else dur,
                    "browser": "Chrome (Synced)",
                    "tags": tags,
                    "description": f"Full watch record for {title}. Channel: {channel}."
                })

            current_dt += timedelta(days=1)

        records.sort(key=lambda r: r["visited_at"], reverse=True)
        return records
