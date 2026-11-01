import os
import shutil
import sqlite3
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

def webkit_to_datetime(webkit_timestamp: int) -> datetime:
    """Convert WebKit/Chrome timestamp (microseconds since Jan 1, 1601 UTC) to datetime."""
    try:
        if not webkit_timestamp or webkit_timestamp <= 0:
            return datetime.now(timezone.utc)
        # 11644473600 is seconds between 1601-01-01 and 1970-01-01
        epoch_seconds = (webkit_timestamp / 1_000_000) - 11644473600
        if epoch_seconds < 0:
            return datetime.now(timezone.utc)
        return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube Video ID from various URL formats."""
    parsed = urllib.parse.urlparse(url)
    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            qs = urllib.parse.parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                return parts[1]
    elif "youtu.be" in parsed.netloc:
        parts = parsed.path.strip("/").split("/")
        if parts:
            return parts[0]
    return None

def extract_search_query(url: str) -> Optional[str]:
    """Extract search query from YouTube search URLs."""
    parsed = urllib.parse.urlparse(url)
    if "youtube.com" in parsed.netloc and parsed.path == "/results":
        qs = urllib.parse.parse_qs(parsed.query)
        queries = qs.get("search_query", [])
        if queries:
            return queries[0]
    return None

class BrowserHistoryScraper:
    def __init__(self):
        self.browser_paths = self._detect_browser_paths()

    def _detect_browser_paths(self) -> Dict[str, List[Path]]:
        """Detect existing History SQLite files across Chrome, Edge, and Brave."""
        detected = {}
        local_app_data = os.getenv("LOCALAPPDATA")
        if not local_app_data:
            return detected

        candidates = {
            "Chrome": Path(local_app_data) / "Google" / "Chrome" / "User Data",
            "Edge": Path(local_app_data) / "Microsoft" / "Edge" / "User Data",
            "Brave": Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "User Data",
        }

        for browser_name, user_data_path in candidates.items():
            if not user_data_path.exists():
                continue
            history_files = []
            
            # Check Default profile
            default_history = user_data_path / "Default" / "History"
            if default_history.exists():
                history_files.append(default_history)

            # Check Profile 1, Profile 2, etc.
            for profile_dir in user_data_path.glob("Profile *"):
                profile_history = profile_dir / "History"
                if profile_history.exists():
                    history_files.append(profile_history)

            if history_files:
                detected[browser_name] = history_files

        return detected

    def extract_youtube_records(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Extract YouTube video views and searches from all detected browser history databases.
        Copies the DB file to a temp file to prevent database locking issues.
        """
        records = []
        seen_keys = set()  # (video_id/query, timestamp_str) to deduplicate visits

        for browser_name, paths in self.browser_paths.items():
            for history_file in paths:
                try:
                    records_from_db = self._read_sqlite_history(history_file, browser_name, days_back)
                    for rec in records_from_db:
                        # Deduplicate
                        key = (rec.get("video_id") or rec.get("search_query"), rec.get("visited_at"))
                        if key not in seen_keys:
                            seen_keys.add(key)
                            records.append(rec)
                except Exception as e:
                    print(f"[Warning] Failed to read {history_file} ({browser_name}): {e}")

        # Sort descending by visited_at
        records.sort(key=lambda r: r.get("visited_at", ""), reverse=True)
        return records

    def _read_sqlite_history(self, db_path: Path, browser_name: str, days_back: int) -> List[Dict[str, Any]]:
        results = []
        # Create temp file copy
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp_file:
            temp_db = Path(tmp_file.name)

        try:
            shutil.copy2(db_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Query URLs & visits
            query = """
            SELECT 
                urls.url,
                urls.title,
                visits.visit_time,
                visits.visit_duration
            FROM urls
            JOIN visits ON urls.id = visits.url
            WHERE urls.url LIKE '%youtube.com/watch%'
               OR urls.url LIKE '%youtu.be/%'
               OR urls.url LIKE '%youtube.com/shorts/%'
               OR urls.url LIKE '%youtube.com/results%'
            ORDER BY visits.visit_time DESC
            LIMIT 5000
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            now_utc = datetime.now(timezone.utc)

            for url, raw_title, visit_time, visit_duration in rows:
                dt = webkit_to_datetime(visit_time)
                # Filter by days_back
                age_days = (now_utc - dt).total_seconds() / 86400.0
                if age_days > days_back:
                    continue

                # Clean title (removes ' - YouTube' suffix)
                title = raw_title or ""
                if title.endswith(" - YouTube"):
                    title = title[:-10].strip()

                video_id = extract_video_id(url)
                search_query = extract_search_query(url)

                if not video_id and not search_query:
                    continue

                # Chrome stores visit_duration in microseconds
                duration_sec = 0
                if visit_duration and visit_duration > 0:
                    duration_sec = int(visit_duration / 1_000_000)

                is_short = bool(
                    "/shorts/" in url or 
                    (title and ("#shorts" in title.lower() or "#short" in title.lower()))
                )
                if is_short:
                    record_type = "shorts"
                elif video_id:
                    record_type = "video"
                else:
                    record_type = "search"

                results.append({
                    "type": record_type,
                    "is_shorts": is_short,
                    "url": url,
                    "video_id": video_id,
                    "search_query": search_query,
                    "title": title if title else (f"Search: {search_query}" if search_query else "YouTube Video"),
                    "visited_at": dt.isoformat(),
                    "date": dt.strftime("%Y-%m-%d"),
                    "hour": dt.hour,
                    "browser_recorded_duration_sec": duration_sec,
                    "browser": browser_name,
                })

        finally:
            if temp_db.exists():
                try:
                    os.remove(temp_db)
                except Exception:
                    pass

        return results
