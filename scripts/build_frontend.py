# Script to build and verify the upgraded BalanceVault multi-page frontend
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"

print(f"Base dir: {BASE_DIR}")
