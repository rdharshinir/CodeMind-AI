"""Entry point for CodeMind AI server."""

import uvicorn
from codemind.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "codemind.api:app",
        host=settings.codemind_host,
        port=settings.codemind_port,
        reload=False,  # Keep server stable without accidental file-watcher reloads
        log_level="info",
    )
