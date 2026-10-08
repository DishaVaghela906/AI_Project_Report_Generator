"""
AI Report Generator – Application Entry Point
"""
import uvicorn
from app.main import app  # noqa: F401

if __name__ == "__main__":
    from app.core.config import settings
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
