from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.config import PRODUCTIVE_CATEGORIES, DISTRACTIVE_CATEGORIES, NEUTRAL_CATEGORIES

class MetricsEngine:
    """Calculates daily watch time, distraction indexes, temporal habits, and binge patterns."""

    @staticmethod
    def classify_category(category: str) -> str:
        """Returns 'Productive', 'Distractive', or 'Neutral'."""
        if category in PRODUCTIVE_CATEGORIES:
            return "Productive"
        elif category in DISTRACTIVE_CATEGORIES:
            return "Distractive"
        return "Neutral"

    @classmethod
    def analyze_records(cls, records: List[Dict[str, Any]], target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a list of enriched YouTube records.
        If target_date is given (YYYY-MM-DD), filters for that specific date;
        otherwise analyzes the most recent date available in records.
        """
        if not records:
            return cls._empty_metrics()

        # Group records by date
        records_by_date = defaultdict(list)
        for r in records:
            date_str = r.get("date")
            if date_str:
                records_by_date[date_str].append(r)

        available_dates = sorted(records_by_date.keys(), reverse=True)
        selected_date = target_date if target_date in records_by_date else (available_dates[0] if available_dates else None)

        day_records = records_by_date.get(selected_date, []) if selected_date else records

        # 1. Total Daily Watch Time
        total_watch_sec = sum(r.get("duration_sec", 0) for r in day_records)
        total_videos = len([r for r in day_records if r.get("type") == "video"])
        total_searches = len([r for r in day_records if r.get("type") == "search"])

        # 2. Category & Productivity Breakdown
        category_durations = defaultdict(int)
        category_counts = defaultdict(int)
        type_durations = {"Productive": 0, "Distractive": 0, "Neutral": 0}

        for r in day_records:
            cat = r.get("category", "General")
            dur = r.get("duration_sec", 0)
            category_durations[cat] += dur
            category_counts[cat] += 1

            classified = cls.classify_category(cat)
            type_durations[classified] += dur

        # Distraction / Productivity ratios
        distraction_ratio = (type_durations["Distractive"] / total_watch_sec * 100) if total_watch_sec > 0 else 0.0
        productive_ratio = (type_durations["Productive"] / total_watch_sec * 100) if total_watch_sec > 0 else 0.0

        # 3. Hourly Activity (0 to 23)
        hourly_watch_sec = [0] * 24
        hourly_distractive_sec = [0] * 24
        for r in day_records:
            h = r.get("hour", 0)
            dur = r.get("duration_sec", 0)
            if 0 <= h < 24:
                hourly_watch_sec[h] += dur
                if cls.classify_category(r.get("category", "General")) == "Distractive":
                    hourly_distractive_sec[h] += dur

        peak_hour = max(range(24), key=lambda h: hourly_distractive_sec[h]) if any(hourly_distractive_sec) else -1

        # 4. Binge Detection (3 or more consecutive distractive videos)
        binge_sessions = []
        current_streak = []
        for r in sorted(day_records, key=lambda x: x.get("visited_at", "")):
            if r.get("type") == "video":
                if cls.classify_category(r.get("category", "General")) == "Distractive":
                    current_streak.append(r)
                else:
                    if len(current_streak) >= 3:
                        binge_sessions.append(current_streak)
                    current_streak = []
        if len(current_streak) >= 3:
            binge_sessions.append(current_streak)

        # 5. Top Channels and Searches
        channel_durations = defaultdict(int)
        for r in day_records:
            ch = r.get("channel", "Unknown Channel")
            if ch:
                channel_durations[ch] += r.get("duration_sec", 0)

        top_channels = sorted(channel_durations.items(), key=lambda x: x[1], reverse=True)[:5]
        top_channels_fmt = [{"channel": ch, "duration_fmt": cls.format_duration(dur)} for ch, dur in top_channels]

        searches = [r.get("title", "") for r in day_records if r.get("type") == "search"][:5]

        # 6. Multi-day 7-day trend
        trend_7d = []
        for d in available_dates[:7]:
            d_records = records_by_date[d]
            d_tot_sec = sum(item.get("duration_sec", 0) for item in d_records)
            d_dist_sec = sum(item.get("duration_sec", 0) for item in d_records if cls.classify_category(item.get("category", "General")) == "Distractive")
            trend_7d.append({
                "date": d,
                "total_hours": round(d_tot_sec / 3600, 2),
                "distraction_hours": round(d_dist_sec / 3600, 2),
                "distraction_pct": round((d_dist_sec / d_tot_sec * 100) if d_tot_sec > 0 else 0, 1)
            })
        trend_7d.reverse()

        return {
            "selected_date": selected_date,
            "available_dates": available_dates,
            "total_watch_seconds": total_watch_sec,
            "total_watch_fmt": cls.format_duration(total_watch_sec),
            "total_videos": total_videos,
            "total_searches": total_searches,
            "productive_seconds": type_durations["Productive"],
            "productive_fmt": cls.format_duration(type_durations["Productive"]),
            "productive_pct": round(productive_ratio, 1),
            "distractive_seconds": type_durations["Distractive"],
            "distractive_fmt": cls.format_duration(type_durations["Distractive"]),
            "distractive_pct": round(distraction_ratio, 1),
            "neutral_seconds": type_durations["Neutral"],
            "neutral_fmt": cls.format_duration(type_durations["Neutral"]),
            "peak_distraction_hour": f"{peak_hour:02d}:00 - {(peak_hour+1)%24:02d}:00" if peak_hour >= 0 else "None",
            "binge_sessions_count": len(binge_sessions),
            "categories_breakdown": [
                {
                    "category": cat,
                    "type": cls.classify_category(cat),
                    "duration_sec": dur,
                    "duration_fmt": cls.format_duration(dur),
                    "count": category_counts[cat],
                    "percentage": round(dur / total_watch_sec * 100, 1) if total_watch_sec > 0 else 0
                }
                for cat, dur in sorted(category_durations.items(), key=lambda x: x[1], reverse=True)
            ],
            "hourly_watch_hours": [round(s / 3600, 2) for s in hourly_watch_sec],
            "hourly_distractive_hours": [round(s / 3600, 2) for s in hourly_distractive_sec],
            "top_channels": top_channels_fmt,
            "recent_searches": searches,
            "weekly_trend": trend_7d,
            "records": day_records
        }

    @staticmethod
    def format_duration(seconds: int) -> str:
        if seconds <= 0:
            return "0m"
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    @classmethod
    def _empty_metrics(cls) -> Dict[str, Any]:
        return {
            "selected_date": None,
            "available_dates": [],
            "total_watch_seconds": 0,
            "total_watch_fmt": "0m",
            "total_videos": 0,
            "total_searches": 0,
            "productive_seconds": 0,
            "productive_fmt": "0m",
            "productive_pct": 0.0,
            "distractive_seconds": 0,
            "distractive_fmt": "0m",
            "distractive_pct": 0.0,
            "neutral_seconds": 0,
            "neutral_fmt": "0m",
            "peak_distraction_hour": "None",
            "binge_sessions_count": 0,
            "categories_breakdown": [],
            "hourly_watch_hours": [0] * 24,
            "hourly_distractive_hours": [0] * 24,
            "top_channels": [],
            "recent_searches": [],
            "weekly_trend": [],
            "records": []
        }
