# 🎯 FocusCurb: YouTube Distraction & Productivity Agent

An intelligent, privacy-preserving agent that audits your YouTube watch habits, detects distraction rabbit holes, calculates daily watch metrics, and generates personalized productivity coaching plans with embedded resource links.

Built with **Browser History Scraping**, **YouTube Data API v3**, **Vector Embeddings & RAG**, and **Model Context Protocol (MCP)**.

---

## 🚀 Key Features

1. **Automatic Browser History Scraping**:
   - Directly extracts YouTube watch history and search queries from local **Google Chrome** and **Microsoft Edge** SQLite databases.
   - Non-intrusive: copies the history database to a temporary location to prevent locking conflicts even while your browser is actively open.
   - Also supports **Google Takeout** `watch-history.json` and synthetic evaluation datasets.

2. **YouTube Data API v3 Enrichment**:
   - Fetches exact ISO 8601 video durations, official category IDs, channel metadata, and tags.
   - Includes an intelligent offline heuristic classifier if an API key is not configured.

3. **Distraction & Productivity Analytics**:
   - **Daily Watch Time**: Aggregated hours, minutes, and video counts.
   - **Distraction Index (%)**: Percentage of time spent on entertainment/gaming/memes vs productive learning.
   - **Peak Vulnerability Window**: Pinpoints the exact hour of the day you are most likely to fall into rabbit holes.
   - **Binge Streak Detection**: Flags sequences of 3+ consecutive distractive videos.

4. **Vector Embeddings & RAG Engine**:
   - Generates high-dimensional vector embeddings for all watched titles, categories, and searches.
   - Built-in dual provider: Google Gemini Embeddings (`gemini-embedding-001`) with an automatic fallback to an offline normalized subword vectorizer.
   - Semantic retrieval to query distraction patterns and find tutorials.

5. **RAG Productivity Coach with Embedded Links**:
   - Translates metrics into concrete behavioral interventions (e.g. setting up evening friction, blocking afternoon slump periods).
   - **Embedded Curated Links**: Direct links to tools like [Pomofocus](https://pomofocus.io/), [Unhook YouTube](https://unhook.app/), [Cold Turkey Blocker](https://getcoldturkey.com/), [Cal Newport's Deep Work](https://calnewport.com/deep-work-rules-for-focused-success-in-a-distracted-world/), and [freeCodeCamp](https://www.freecodecamp.org/).

6. **Model Context Protocol (MCP) Server**:
   - Native MCP 2.x server exposing tools for AI assistants (Antigravity, Claude Desktop, Cursor):
     - `get_daily_watch_metrics(target_date)`
     - `get_productivity_recommendations(user_goals)`
     - `search_watch_history(query, top_k)`
     - `refresh_browser_history(days_back)`

7. **Modern Web Dashboard**:
   - Responsive dark-mode interface with Tailwind CSS and Chart.js.
   - Real-time KPI cards, 24-hour distribution bar chart, category donut chart, and interactive RAG search bar.

---

## 🛠️ Quick Start

### 1. Installation

```bash
cd C:\Users\mohit\curb-distraction
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)

Copy `.env.example` to `.env` and configure your keys if desired:
```env
# Optional: YouTube Data API v3 key
YOUTUBE_API_KEY=your_youtube_api_key_here

# Optional: Gemini API Key for gemini-embedding-001
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: FocusCurb operates 100% offline out-of-the-box with heuristic categorization and local vector embeddings if no keys are provided!)*

---

## 🖥️ Usage

### A. Run the Interactive Web Dashboard

```bash
python run_dashboard.py
```
Open your browser to: **http://127.0.0.1:5000**

- View your total watch time and distraction ratio.
- Click **"Scan History"** to fetch live YouTube visits from Chrome and Edge.
- Set your goals in the prompt bar to generate actionable suggestions with embedded links.
- Use the **Semantic Vector Search** to find any past video or rabbit hole.

---

### B. Run from Terminal (CLI)

```bash
# 1. Audit today's YouTube watch metrics:
python run_cli.py audit

# 2. Get tailored productivity plan with embedded links:
python run_cli.py plan --goal "Finish database project and complete deep work block"

# 3. Perform semantic RAG search:
python run_cli.py search "programming tutorials and system design"

# 4. Scan and sync local browser history:
python run_cli.py sync --days 14
```

Search ranks topic matches alongside vector similarity and avoids repeating the same video in the results.

---

### C. Connect as an MCP Server

Add to your MCP Client configuration (e.g. `claude_desktop_config.json` or Antigravity):

```json
{
  "mcpServers": {
    "youtube-distraction-curb": {
      "command": "python",
      "args": ["C:\\Users\\mohit\\curb-distraction\\run_mcp_server.py"]
    }
  }
}
```

Now your AI assistant can query your watch time, diagnose your distractions, and coach you through your day!
