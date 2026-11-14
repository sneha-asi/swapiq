"""Launcher that respects the PORT env var when one is set (e.g. by a hosting
or dev environment), falling back to 8020 for manual runs (python run_server.py)."""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8020"))
    uvicorn.run("api.index:app", host="0.0.0.0", port=port)
