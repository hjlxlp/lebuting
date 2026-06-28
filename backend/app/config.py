"""lebuting 业务 API — 多模块共用 8181 端口。"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "lebuting.db"
API_PORT = 8181
