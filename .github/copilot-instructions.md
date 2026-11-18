# Copilot instructions for FocusCurb

## Project overview

This repository is a Python productivity app that audits local YouTube watch history, scores distraction vs. productive time, and generates coaching recommendations. The main workflow is:

- scrape local Chrome/Edge history (`src/scraper/`)
- enrich records with metadata and category heuristics (`src/youtube/`, `src/config.py`)
- store the normalized dataset in SQLite (`data/watch_history.db`)
- build/search a vector index for semantic retrieval (`src/rag/`)
- expose the results through a CLI, Flask dashboard, and MCP server

The repo is intentionally a small app with one main service layer: `src/service.py` orchestrates nearly all behavior. Treat that file as the default entry point for project-level logic.

## Build, test, and validation commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
python run_dashboard.py
```

Run the CLI audit/report flow:

```bash
python run_cli.py audit
python run_cli.py plan --goal "Finish database project and complete deep work block"
python run_cli.py search "programming tutorials and system design"
python run_cli.py sync --days 14
```

Run a single test module:

```bash
python -m unittest tests.test_vector_store -v
python -m unittest tests.test_embeddings -v
```

Run the full test suite:

```bash
python -m unittest discover -s tests -v
```

There is no dedicated lint or build config checked into this repo at the moment. The validation path is the unit test suite above.

## High-level architecture

### Runtime entry points

- `run_cli.py`: command-line interface for audit, plan, search, and sync flows.
- `run_dashboard.py`: starts the Flask dashboard used for browsing metrics and triggering scans.
- `src/mcp/server.py`: exposes the MCP tools used by external AI clients.
- `src/web/app.py`: Flask routes for the web dashboard (`/api/metrics`, `/api/plan`, `/api/search`, `/api/sync`).

### Core service flow

`src/service.py` is the orchestration layer that:

1. creates/initializes the SQLite cache
2. calls the history scraper to collect YouTube records
3. enriches records with API metadata or heuristic categorization
4. writes records to `data/watch_history.db`
5. rebuilds the vector store from those records
6. exposes `get_metrics()`, `get_productivity_plan()`, and `search_rag()` for callers

### Data and classification layers

- `src/config.py`: central configuration and the productive/distractive/neutral category sets.
- `src/analytics/metrics_engine.py`: computes daily metrics, category breakdowns, binge detection, and peak distraction hour.
- `src/rag/vector_store.py`: vector index persistence, cosine similarity, lexical filtering, and local embedding fallback behavior.
- `src/rag/embeddings.py`: embedding provider abstraction with Gemini support and an offline local fallback.

### Scraping and enrichment

- `src/scraper/browser_history.py`: reads browser SQLite history for Chrome/Edge and extracts YouTube entries.
- `src/scraper/takeout_loader.py`: supports Google Takeout JSON and demo datasets.
- `src/youtube/api_client.py`: enriches records with metadata like duration, category, channel, tags, and descriptions.

## Key conventions

- Keep the app data local and privacy-preserving. Browser history is copied to temporary files before reading when possible, and the repo stores cached analysis outputs under `data/`.
- Treat `data/watch_history.db` as the persistent cache and `data/vector_index.json` as the persisted semantic index. Rebuilding the index via `python run_cli.py sync` is the standard way to refresh search results after data changes.
- Category classification is centralized in `src/config.py` and enforced in `src/analytics/metrics_engine.py`. Shorts are always treated as distracting.
- Search relevance is intentionally hybrid: `VectorStore.similarity_search()` combines lexical matching and embedding similarity, then filters duplicates. Do not replace this behavior with a plain cosine-only similarity check without preserving the lexical fallback behavior.
- The project prefers adding behavior through the service layer rather than writing ad hoc DB or vector-store logic directly in CLI or Flask handlers.
- `.env` is the expected place for optional `YOUTUBE_API_KEY` and `GEMINI_API_KEY`; values are loaded by `src/config.py` automatically.
- Windows UTF-8 console handling is intentionally included in entry-point scripts; keep compatibility when touching CLI behavior.

## Examples of repo-specific patterns to preserve

- If you add a new analysis metric, update the `MetricsEngine` output contract and validate it against the existing CLI/dashboard consumers.
- If you change the search index format, keep the `save()`/`load()` compatibility path intact and account for local fallback dimensions used by `EmbeddingProvider`.
- If you add a new CLI subcommand, update both `run_cli.py` and the related dashboard/MCP surface where applicable so the tooling stays consistent.

## Repository-specific notes

- The README is the best source of product intent and user-facing examples; keep changes aligned with the documented dashboard and MCP behavior.
- The project is small but layered: service orchestration + analytics + retrieval + UI. Ask what layer a feature belongs to before making large edits, rather than patching only the surface code.
- The app is designed to work offline by default, with optional API-key enrichment. Code and tests should not assume external services are always available.
