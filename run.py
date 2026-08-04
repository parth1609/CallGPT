"""
Launcher script for CallGPT on Windows.

Why this file exists:
  When running `python -m uvicorn app.main:app`, uvicorn creates its event loop
  BEFORE it imports app.main. On Windows, this means the loop is already a
  ProactorEventLoop by the time our code sets WindowsSelectorEventLoopPolicy.
  psycopg (async PostgreSQL driver) is incompatible with ProactorEventLoop,
  causing PoolTimeout errors on every connection attempt.

  This script sets the event loop policy FIRST, then launches uvicorn with
  loop="none" so it uses our policy (SelectorEventLoop) instead of overriding it.

Usage:
  python run.py                          # Default: host=0.0.0.0, port=8000
  python run.py --port 9000              # Custom port
  python run.py --reload                 # Enable hot-reload for development
"""

import sys
import asyncio

# MUST happen before ANY event loop is created
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run CallGPT server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # loop="none" tells uvicorn to NOT create its own loop factory,
    # so asyncio.run() will use our WindowsSelectorEventLoopPolicy.
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        loop="none",
    )


if __name__ == "__main__":
    main()
