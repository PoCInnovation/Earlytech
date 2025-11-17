import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root if present
project_root = Path(__file__).resolve().parents[1]
dotenv_path = project_root / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
# Keep other keys as-needed (GITHUB_TOKEN, HF_TOKEN, etc.)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

# Where to store downloaded assets
DATA_DIR = os.getenv("DATA_DIR") or str(project_root / "data")
PDF_DIR = os.getenv("PDF_DIR") or str(project_root / "data" / "pdfs")

# Defaults
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))


def ensure_dirs():
    from pathlib import Path
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(PDF_DIR).mkdir(parents=True, exist_ok=True)
