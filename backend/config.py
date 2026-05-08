import os
from urllib.parse import quote_plus

# ── Database ──────────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "47.104.72.198")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Kewen888@")
DB_NAME = os.getenv("DB_NAME", "ai_product")

# quote_plus encodes special chars like '@' in the password to avoid URL parsing errors
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# ── Single account auth ───────────────────────────────────────────────────────
ACCOUNT_USERNAME = os.getenv("ACCOUNT_USERNAME", "admin")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD", "admin888")

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# ── File storage ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Max images per day before locking
DAILY_IMAGE_LIMIT = 60
