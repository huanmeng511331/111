"""应用级配置：数据库路径、CORS 白名单等运行参数。"""

import os
from pathlib import Path

# backend/ 目录，demo.db 与其同级，便于按需求在 backend/ 下直接查看数据文件
BACKEND_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("HSE_DB_PATH", BACKEND_DIR / "demo.db"))

# 本机演示：前端 Vite 默认 5173，允许其直接跨域调用后端
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

API_PREFIX = "/api"
