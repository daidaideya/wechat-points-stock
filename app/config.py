import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # INGEST_TOKEN is the machine-to-machine credential used by external
    # points/stock reporters. Keep API_TOKEN as a one-release compatibility
    # alias so existing deployments do not break during the rename.
    INGEST_TOKEN = (os.getenv("INGEST_TOKEN") or os.getenv("API_TOKEN") or "").strip()
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database.db")
    UPLOAD_DIR = os.path.join("static", "uploads")

    def validate_runtime(self):
        token = self.INGEST_TOKEN
        if not token or token == "default_token" or len(token) < 32:
            raise RuntimeError(
                "INGEST_TOKEN is required and must be a random value of at least 32 characters; "
                "API_TOKEN is accepted only as a temporary compatibility alias."
            )

settings = Settings()
