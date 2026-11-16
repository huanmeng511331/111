"""SQLite 连接管理与建表逻辑（标准库 sqlite3，无需额外数据库服务）。"""

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS hazards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hazard_no TEXT NOT NULL UNIQUE,
    hazard_type TEXT NOT NULL,
    hazard_level TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    reporter TEXT NOT NULL,
    owner TEXT,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL,
    rectification_measure TEXT,
    rectification_result TEXT,
    acceptance_comment TEXT,
    image_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hazard_flow_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hazard_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    operator TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (hazard_id) REFERENCES hazards (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_hazards_status ON hazards (status);
CREATE INDEX IF NOT EXISTS idx_hazards_level ON hazards (hazard_level);
CREATE INDEX IF NOT EXISTS idx_hazards_due_date ON hazards (due_date);
CREATE INDEX IF NOT EXISTS idx_flow_logs_hazard ON hazard_flow_logs (hazard_id);
"""


def _create_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """每次请求/操作独立连接，正常退出提交，异常回滚。"""
    connection = _create_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)
