import sys
import json

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from mcp.server.mcpserver import MCPServer
from src.service import YouTubeDistractionService

# Initialize MCP server
mcp = MCPServer(name="youtube-distraction-curb")
service = YouTubeDistractionService()

@mcp.tool()
def get_daily_watch_metrics(target_date: str = "") -> str:
    """
    Get your daily YouTube watch time, distraction index, videos watched,
    and category breakdown.
    
    Args:
        target_date: Optional date formatted as YYYY-MM-DD. Defaults to today/most recent date.
    """
    date_arg = target_date.strip() if target_date else None
    metrics = service.get_metrics(target_date=date_arg)
    
    lines = [
        f"[YouTube Daily Watch Metrics ({metrics.get('selected_date')})]",
        f"• Total Watch Time: {metrics.get('total_watch_fmt')} across {metrics.get('total_videos')} videos",
        f"• Distraction Ratio: {metrics.get('distractive_pct')}% ({metrics.get('distractive_fmt')})",
        f"• Productive Time: {metrics.get('productive_pct')}% ({metrics.get('productive_fmt')})",
        f"• Peak Distraction Hour: {metrics.get('peak_distraction_hour')}",
        f"• Multi-video Binge Streaks: {metrics.get('binge_sessions_count')}",
        "\nTop Categories:"
    ]
    for cat in metrics.get("categories_breakdown", [])[:5]:
        lines.append(f"  - {cat['category']} ({cat['type']}): {cat['duration_fmt']} ({cat['percentage']}%)")
        
    return "\n".join(lines)

@mcp.tool()
def get_productivity_recommendations(user_goals: str = "Deep work and focused learning") -> str:
    """
    Generate personalized daily productivity suggestions with curated clickable links
    tailored to your actual YouTube watch history and identified distraction triggers.
    
    Args:
        user_goals: The productivity or learning goals you want to achieve today.
    """
    plan = service.get_productivity_plan(user_goal=user_goals)
    
    lines = [
        f"[Productivity Coaching Plan]",
        f"Goal: {user_goals}",
        f"Current Distraction Baseline: {plan.get('distraction_pct')}% of {plan.get('total_watch_time')}\n"
    ]
    
    for idx, s in enumerate(plan.get("suggestions", []), 1):
        lines.append(f"### {idx}. [{s['badge']}] {s['title']}")
        lines.append(f"• Diagnosis: {s['diagnosis']}")
        lines.append(f"• Action: {s['prescription']}")
        lines.append("• Curated Links:")
        for link in s.get("links", []):
            lines.append(f"  - [{link['label']}]({link['url']})")
        lines.append("")
        
    return "\n".join(lines)

@mcp.tool()
def search_watch_history(query: str, top_k: int = 5) -> str:
    """
    Perform semantic vector search (RAG) across your YouTube watch history to locate
    specific rabbit holes, tutorials, or topics you watched.
    
    Args:
        query: Search term or description (e.g. 'gaming streams', 'python tutorial')
        top_k: Number of matching results to retrieve (default: 5)
    """
    results = service.search_rag(query, top_k=top_k)
    if not results:
        return f"No matching watch history found for query: '{query}'"
        
    lines = [f"[RAG Search Results for '{query}']"]
    for r in results:
        meta = r.get("metadata", {})
        score = r.get("score", 0.0)
        lines.append(f"• [{score:.2f} match] {meta.get('title')} ({meta.get('category')}) - {meta.get('duration_fmt')}")
        lines.append(f"  Channel: {meta.get('channel')} | Visited: {meta.get('visited_at')}")
        if meta.get("url"):
            lines.append(f"  URL: {meta.get('url')}")
    return "\n".join(lines)

@mcp.tool()
def refresh_browser_history(days_back: int = 7) -> str:
    """
    Scrape the local browser history (Chrome, Edge), enrich metadata with the
    YouTube Data API, and rebuild the vector embedding index.
    
    Args:
        days_back: How many days of browser history to scan (default: 7)
    """
    count = service.sync_history(days_back=days_back)
    return f"Successfully scanned and synchronized {count} YouTube watch records into the database and RAG index."

def run():
    """Runs the MCP server over standard I/O for client connections."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run()
