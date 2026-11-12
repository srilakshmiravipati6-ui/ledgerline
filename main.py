# BalanceVault entrypoint for Vercel Serverless and Uvicorn
from app.main import app

# Export for ASGI servers
__all__ = ["app"]

