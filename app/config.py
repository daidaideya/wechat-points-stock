import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_TOKEN = os.getenv("API_TOKEN", "default_token")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database.db")
    UPLOAD_DIR = os.path.join("static", "uploads")

settings = Settings()
