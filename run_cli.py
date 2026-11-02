import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.service import YouTubeDistractionService

def main():
    parser = argparse.ArgumentParser(description="FocusCurb - YouTube Distraction Breaker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Audit daily YouTube watch time and distraction metrics")
    audit_parser.add_argument("--date", type=str, default="", help="Date in YYYY-MM-DD format (default: latest)")

    # Command: plan
    plan_parser = subparsers.add_parser("plan", help="Generate AI productivity recommendations with embedded links")
    plan_parser.add_argument("--goal", type=str, default="Deep work and focused learning", help="Your goal for today")
    plan_parser.add_argument("--date", type=str, default="", help="Date in YYYY-MM-DD format")

    # Command: search (RAG)
    search_parser = subparsers.add_parser("search", help="Search watched history by topic and semantic similarity")
    search_parser.add_argument("query", type=str, help="Search query or topic description")
    search_parser.add_argument("--top", type=int, default=5, help="Number of results to return")

    # Command: sync
    sync_parser = subparsers.add_parser("sync", help="Scan local browser history and rebuild vector index")
    sync_parser.add_argument("--days", type=int, default=14, help="Days of history to scan")

    args = parser.parse_args()
    service = YouTubeDistractionService()

    if args.command == "audit" or args.command is None:
        target_date = getattr(args, "date", "") or None
        metrics = service.get_metrics(target_date=target_date)

        print("\n" + "=" * 60)
        print(f"📊 YouTube Daily Distraction Audit ({metrics.get('selected_date')})")
        print("=" * 60)
        print(f"⏱️ Total Watch Time:        {metrics.get('total_watch_fmt')} ({metrics.get('total_videos')} videos, {metrics.get('total_searches')} searches)")
        print(f"⚠️ Distraction Index:       {metrics.get('distractive_pct')}% ({metrics.get('distractive_fmt')})")
        print(f"💡 Productive Watch Time:   {metrics.get('productive_pct')}% ({metrics.get('productive_fmt')})")
        print(f"🎯 Peak Vulnerability Hour: {metrics.get('peak_distraction_hour')}")
        print(f"🔁 Binge Streaks:           {metrics.get('binge_sessions_count')} sessions (>=3 consecutive distraction videos)")
        print("\nTop Category Breakdown:")
        for cat in metrics.get("categories_breakdown", [])[:5]:
            print(f"  • {cat['category']:<22} [{cat['type']:<11}] {cat['duration_fmt']:<8} ({cat['percentage']}%)")
        print("=" * 60 + "\n")

    elif args.command == "plan":
        target_date = args.date or None
        plan = service.get_productivity_plan(target_date=target_date, user_goal=args.goal)

        print("\n" + "=" * 60)
        print(f"🎯 Tailored Productivity Coaching Plan")
        print(f"Declared Goal: '{args.goal}'")
        print(f"Distraction Baseline: {plan.get('distraction_pct')}% of {plan.get('total_watch_time')}")
        print("=" * 60)

        for idx, s in enumerate(plan.get("suggestions", []), 1):
            print(f"\n{idx}. [{s['badge']}] {s['title']}")
            print(f"   Diagnosis:    {s['diagnosis']}")
            print(f"   Prescription: {s['prescription']}")
            print(f"   Resource Links:")
            for l in s.get("links", []):
                print(f"     🔗 {l['label']}: {l['url']}")
        print("\n" + "=" * 60 + "\n")

    elif args.command == "search":
        print(f"\n🔍 Searching Vector Store (RAG) for: '{args.query}'...\n")
        results = service.search_rag(args.query, top_k=args.top)
        if not results:
            print("No matching items found.")
        else:
            for idx, r in enumerate(results, 1):
                m = r.get("metadata", {})
                score = round(r.get("score", 0.0) * 100)
                print(f"{idx}. [{score}% Match] {m.get('title')}")
                print(f"   Category: {m.get('category')} | Duration: {m.get('duration_fmt')} | Channel: {m.get('channel')}")
                if m.get("url"):
                    print(f"   URL: {m.get('url')}")
                print()

    elif args.command == "sync":
        count = service.sync_history(days_back=args.days)
        print(f"\n✅ Synchronization complete. Indexed {count} records into database and RAG vector store.\n")

if __name__ == "__main__":
    main()
