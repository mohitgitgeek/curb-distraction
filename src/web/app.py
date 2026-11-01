import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify
from src.service import YouTubeDistractionService

app = Flask(__name__)
service = YouTubeDistractionService()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics")
def api_metrics():
    target_date = request.args.get("date", "").strip() or None
    metrics = service.get_metrics(target_date=target_date)
    return jsonify(metrics)

@app.route("/api/plan", methods=["GET", "POST"])
def api_plan():
    target_date = request.args.get("date", "").strip() or None
    user_goal = request.args.get("goal", "").strip()
    if request.is_json and request.json:
        user_goal = request.json.get("goal", user_goal)
        target_date = request.json.get("date", target_date)

    if not user_goal:
        user_goal = "Deep work, high focus, and zero mindless scrolling"

    plan = service.get_productivity_plan(target_date=target_date, user_goal=user_goal)
    return jsonify(plan)

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    results = service.search_rag(query, top_k=6)
    return jsonify(results)

@app.route("/api/sync", methods=["POST"])
def api_sync():
    days_back = int(request.json.get("days", 14) if request.is_json else 14)
    count = service.sync_history(days_back=days_back)
    return jsonify({"status": "success", "synced_count": count})

def start_server(host="127.0.0.1", port=5000, debug=False):
    print(f"[FocusCurb] Starting Dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    start_server(debug=True)
