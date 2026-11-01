import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import CACHE_DB_PATH
from src.scraper.browser_history import BrowserHistoryScraper
from src.scraper.takeout_loader import TakeoutHistoryLoader
from src.youtube.api_client import YouTubeAPIClient
from src.analytics.metrics_engine import MetricsEngine
from src.rag.vector_store import VectorStore
from src.rag.coach import ProductivityCoach

class YouTubeDistractionService:
    """Core service orchestrating scraping, YouTube API enrichment, RAG vector index, and metrics."""

    def __init__(self):
        self.scraper = BrowserHistoryScraper()
        self.api_client = YouTubeAPIClient()
        self.vector_store = VectorStore()
        self.coach = ProductivityCoach(self.vector_store)
        self.db_path = CACHE_DB_PATH
        self._init_db()
        self.vector_store.load()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                type TEXT,
                url TEXT,
                video_id TEXT,
                search_query TEXT,
                title TEXT,
                channel TEXT,
                category TEXT,
                duration_sec INTEGER,
                duration_fmt TEXT,
                visited_at TEXT,
                date TEXT,
                hour INTEGER,
                browser TEXT,
                tags_json TEXT,
                description TEXT
            )
        """)
        # Immediate migration: Ensure all YouTube Shorts are categorized as 'Shorts' and marked as type 'shorts'
        cursor.execute("""
            UPDATE records 
            SET category = 'Shorts', type = 'shorts'
            WHERE url LIKE '%/shorts/%' OR title LIKE '%#shorts%' OR title LIKE '%#short%'
        """)
        # For Shorts that had excessive default duration, normalize to 45s
        cursor.execute("""
            UPDATE records 
            SET duration_sec = 45, duration_fmt = '45s'
            WHERE (category = 'Shorts' OR url LIKE '%/shorts/%') AND (duration_sec > 60 OR duration_sec = 0)
        """)
        conn.commit()
        conn.close()

    def sync_history(self, days_back: int = 14, use_demo_if_empty: bool = True) -> int:
        """
        Scrapes browser history (Chrome, Edge), enriches with YouTube API / heuristics,
        stores in database, and updates the RAG vector index.
        """
        print(f"[Sync] Scanning local browser history for the past {days_back} days...")
        raw_records = self.scraper.extract_youtube_records(days_back=days_back)
        print(f"[Sync] Found {len(raw_records)} raw records from local browsers.")

        if not raw_records and use_demo_if_empty:
            print("[Sync] No browser history found. Generating realistic sample dataset for evaluation...")
            raw_records = TakeoutHistoryLoader.generate_demo_dataset()

        if not raw_records:
            return 0

        # Enrich with YouTube API / Categorizer
        enriched = self.api_client.enrich_records(raw_records)

        # Store in SQLite cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for r in enriched:
            rec_id = f"{r.get('video_id') or r.get('search_query')}_{r.get('visited_at')}"
            cursor.execute("""
                INSERT OR REPLACE INTO records (
                    id, type, url, video_id, search_query, title, channel,
                    category, duration_sec, duration_fmt, visited_at, date,
                    hour, browser, tags_json, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec_id,
                r.get("type", "video"),
                r.get("url", ""),
                r.get("video_id", ""),
                r.get("search_query", ""),
                r.get("title", ""),
                r.get("channel", "YouTube Creator"),
                r.get("category", "General"),
                r.get("duration_sec", 0),
                r.get("duration_fmt", ""),
                r.get("visited_at", ""),
                r.get("date", ""),
                r.get("hour", 0),
                r.get("browser", "Browser"),
                json.dumps(r.get("tags", [])),
                r.get("description", "")
            ))
        conn.commit()
        conn.close()

        # Update Vector Store RAG Index
        indexed_count = self.vector_store.build_from_records(enriched)
        print(f"[Sync] Successfully indexed {indexed_count} items into Vector RAG Store.")
        return len(enriched)

    def get_all_records(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records ORDER BY visited_at DESC")
        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            d = dict(row)
            try:
                d["tags"] = json.loads(d.get("tags_json") or "[]")
            except Exception:
                d["tags"] = []
            records.append(d)
        return records

    def get_metrics(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        records = self.get_all_records()
        if not records:
            # Auto-sync on first launch
            self.sync_history()
            records = self.get_all_records()
        return MetricsEngine.analyze_records(records, target_date=target_date)

    def get_productivity_plan(self, target_date: Optional[str] = None, user_goal: str = "Maximum focus and deep work") -> Dict[str, Any]:
        metrics = self.get_metrics(target_date)
        return self.coach.generate_daily_plan(metrics, user_goal=user_goal)

    def search_rag(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.vector_store.documents:
            self.vector_store.load()
            if not self.vector_store.documents:
                self.sync_history()
        return self.vector_store.similarity_search(query, top_k=top_k)

    def import_takeout_json(self, json_path: Path) -> int:
        records = TakeoutHistoryLoader.load_from_json(json_path)
        enriched = self.api_client.enrich_records(records)
        # Store in db and vector store
        self.vector_store.build_from_records(enriched)
        return len(enriched)
