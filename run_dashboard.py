import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.web.app import start_server

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run FocusCurb Web Dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Port to run web dashboard on (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode")
    args = parser.parse_args()

    start_server(port=args.port, debug=args.debug)
