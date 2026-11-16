"""SQLite 连接管理、建表与演示数据初始化。"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from app.models.enums import HazardLevel, HazardStatus, HazardType

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "demo.db"

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
    attachment_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hazards_status ON hazards (status);
CREATE INDEX IF NOT EXISTS idx_hazards_level ON hazards (hazard_level);
CREATE INDEX IF NOT EXISTS idx_hazards_type ON hazards (hazard_type);
CREATE INDEX IF NOT EXISTS idx_hazards_created_at ON hazards (created_at);

CREATE TABLE IF NOT EXISTS hazard_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hazard_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    operator TEXT,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (hazard_id) REFERENCES hazards (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_hazard_logs_hazard_id ON hazard_logs (hazard_id);
"""


def resolve_db_path() -> Path:
    """返回数据库文件路径，可通过 HSE_DB_PATH 覆盖（测试使用）。"""

    configured = os.getenv("HSE_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB_PATH


def connect(db_path: Path) -> sqlite3.Connection:
    """创建 SQLite 连接；使用自动提交模式以便显式控制事务边界。"""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """显式事务：写操作要么全部成功，要么回滚。"""

    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def init_db(db_path: Path) -> None:
    """建表并在空库时写入演示数据。"""

    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        if _count_hazards(conn) == 0:
            _seed(conn)
    finally:
        conn.close()


def _count_hazards(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS total FROM hazards").fetchone()
    return int(row["total"])


def _iso(moment: datetime) -> str:
    return moment.replace(microsecond=0).isoformat()


def _insert_log(
    conn: sqlite3.Connection,
    hazard_id: int,
    action: str,
    from_status: str | None,
    to_status: str,
    operator: str,
    comment: str | None,
    created_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO hazard_logs
            (hazard_id, action, from_status, to_status, operator, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (hazard_id, action, from_status, to_status, operator, comment, created_at),
    )


def _seed(conn: sqlite3.Connection) -> None:
    """写入可直接演示的模拟隐患数据（全部为虚构信息）。"""

    today = date.today()
    now = datetime.now(timezone.utc)

    pending = HazardStatus.PENDING_REVIEW.value
    rectifying = HazardStatus.RECTIFYING.value
    acceptance = HazardStatus.PENDING_ACCEPTANCE.value
    closed = HazardStatus.CLOSED.value

    seeds: list[dict] = [
        {
            "type": HazardType.FIRE.value,
            "level": HazardLevel.GENERAL.value,
            "location": "1号厂房东侧消防通道",
            "description": "消防通道被纸箱和托盘占用约3米，人员通行宽度不足，影响应急疏散。",
            "reporter": "张伟",
            "owner": None,
            "due_offset": 3,
            "status": pending,
            "created_days_ago": 1,
        },
        {
            "type": HazardType.ELECTRIC.value,
            "level": HazardLevel.MAJOR.value,
            "location": "2号厂房配电间",
            "description": "配电箱柜门未上锁，柜内接线端子裸露，存在误触风险。",
            "reporter": "李娜",
            "owner": "李强",
            "due_offset": 2,
            "status": rectifying,
            "created_days_ago": 3,
        },
        {
            "type": HazardType.OPERATION.value,
            "level": HazardLevel.CRITICAL.value,
            "location": "3号装置区检修脚手架",
            "description": "高处作业人员未规范系挂安全带，下方未设置警戒区域。",
            "reporter": "王芳",
            "owner": "王磊",
            "due_offset": -1,
            "status": rectifying,
            "created_days_ago": 4,
        },
        {
            "type": HazardType.ENVIRONMENT.value,
            "level": HazardLevel.GENERAL.value,
            "location": "危废暂存间门口",
            "description": "危废暂存间未张贴危废种类标识和应急联系电话，标识牌缺失。",
            "reporter": "赵敏",
            "owner": "赵敏",
            "due_offset": 5,
            "status": acceptance,
            "created_days_ago": 4,
            "measure": "补充危废种类标识牌，张贴应急联系电话，并纳入每周巡检。",
            "result": "已完成标识牌制作与张贴，现场照片已归档。",
        },
        {
            "type": HazardType.OCCUPATIONAL_HEALTH.value,
            "level": HazardLevel.GENERAL.value,
            "location": "空压机房",
            "description": "巡检人员进入空压机房未佩戴耳塞，现场噪声检测值为 92 分贝。",
            "reporter": "陈静",
            "owner": "陈涛",
            "due_offset": -2,
            "status": acceptance,
            "created_days_ago": 5,
            "measure": "在入口设置噪声危害告知牌与耳塞取用点，班前会强调佩戴要求。",
            "result": "告知牌与耳塞已配置到位，抽查 6 人均按要求佩戴。",
        },
        {
            "type": HazardType.FIRE.value,
            "level": HazardLevel.MAJOR.value,
            "location": "成品仓库A区",
            "description": "消防栓前方堆放成品货物，遮挡消防设施，影响紧急取用。",
            "reporter": "刘海",
            "owner": "刘海",
            "due_offset": -6,
            "status": closed,
            "created_days_ago": 9,
            "measure": "清理消防栓前方货物，地面划定禁放黄线，纳入每日巡查。",
            "result": "货物已清理，禁放线已施划，连续 3 日巡查无反弹。",
            "acceptance": "现场复核已整改到位，同意关闭。",
        },
        {
            "type": HazardType.EQUIPMENT.value,
            "level": HazardLevel.GENERAL.value,
            "location": "办公楼二层走廊",
            "description": "二层走廊 2 盏应急照明灯故障，断电测试时无法点亮。",
            "reporter": "孙磊",
            "owner": "周鹏",
            "due_offset": -10,
            "status": closed,
            "created_days_ago": 13,
            "measure": "更换故障应急照明灯具，并完成全楼应急照明放电测试。",
            "result": "2 盏灯具已更换，全楼放电测试 90 分钟正常。",
            "acceptance": "测试记录齐全，整改有效，同意关闭。",
        },
        {
            "type": HazardType.OPERATION.value,
            "level": HazardLevel.CRITICAL.value,
            "location": "检修车间动火作业点",
            "description": "动火作业期间监护人离开现场，未配备灭火器材。",
            "reporter": "吴敏",
            "owner": "郑凯",
            "due_offset": -8,
            "status": closed,
            "created_days_ago": 12,
            "measure": "立即停止动火作业，补充监护人及灭火器材，重新办理动火票。",
            "result": "作业已停工整改，监护人到位，灭火器配置 2 具，重新交底后复工。",
            "acceptance": "复核动火票与现场监护记录，同意关闭。",
        },
        {
            "type": HazardType.ENVIRONMENT.value,
            "level": HazardLevel.MAJOR.value,
            "location": "化学品库B区",
            "description": "部分化学品容器未张贴中文标签，无法快速辨识介质名称与危险性。",
            "reporter": "何丽",
            "owner": "马超",
            "due_offset": 4,
            "status": rectifying,
            "created_days_ago": 2,
        },
        {
            "type": HazardType.EQUIPMENT.value,
            "level": HazardLevel.GENERAL.value,
            "location": "变电所东侧电缆沟",
            "description": "电缆沟盖板缺失 2 块，存在人员踏空和异物落入风险。",
            "reporter": "杨帆",
            "owner": None,
            "due_offset": 6,
            "status": pending,
            "created_days_ago": 0,
        },
        {
            "type": HazardType.OPERATION.value,
            "level": HazardLevel.GENERAL.value,
            "location": "成品库主通道",
            "description": "叉车在成品库主通道行驶速度过快，未执行限速 5 公里要求。",
            "reporter": "徐涛",
            "owner": "高翔",
            "due_offset": -14,
            "status": closed,
            "created_days_ago": 18,
            "measure": "对叉车司机开展限速专项培训，通道增设限速标识与减速带。",
            "result": "培训 12 人并考核合格，限速标识与减速带已安装。",
            "acceptance": "抽查 5 车次均按限速行驶，同意关闭。",
        },
        {
            "type": HazardType.ENVIRONMENT.value,
            "level": HazardLevel.GENERAL.value,
            "location": "焚烧炉废气采样平台",
            "description": "废气采样口密封盖未复位，存在无组织排放风险。",
            "reporter": "罗静",
            "owner": "谢峰",
            "due_offset": 1,
            "status": acceptance,
            "created_days_ago": 3,
            "measure": "复位采样口密封盖并加装防脱链条，纳入交接班检查项。",
            "result": "密封盖已复位，防脱链条安装完成，交接班表已更新。",
        },
    ]

    for index, item in enumerate(seeds, start=1):
        created_at = now - timedelta(days=item["created_days_ago"]) - timedelta(hours=index % 6)
        hazard_no = f"HSE-{created_at.strftime('%Y%m%d')}-{index:04d}"
        due_date = (today + timedelta(days=item["due_offset"])).isoformat()
        updated_at = created_at
        if item["status"] in {rectifying, acceptance, closed}:
            updated_at = created_at + timedelta(hours=4)
        if item["status"] in {acceptance, closed}:
            updated_at = created_at + timedelta(hours=28)
        if item["status"] == closed:
            updated_at = created_at + timedelta(hours=52)

        cursor = conn.execute(
            """
            INSERT INTO hazards
                (hazard_no, hazard_type, hazard_level, location, description, reporter,
                 owner, due_date, status, rectification_measure, rectification_result,
                 acceptance_comment, attachment_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hazard_no,
                item["type"],
                item["level"],
                item["location"],
                item["description"],
                item["reporter"],
                item["owner"],
                due_date,
                item["status"],
                item.get("measure"),
                item.get("result"),
                item.get("acceptance"),
                None,
                _iso(created_at),
                _iso(updated_at),
            ),
        )
        hazard_id = int(cursor.lastrowid)
        _insert_log(
            conn,
            hazard_id,
            "create",
            None,
            pending,
            item["reporter"],
            "现场发现隐患并上报。",
            _iso(created_at),
        )
        if item["status"] in {rectifying, acceptance, closed}:
            _insert_log(
                conn,
                hazard_id,
                "assign",
                pending,
                rectifying,
                "安全管理员",
                f"审核通过，分派责任人 {item['owner']}，整改期限 {due_date}。",
                _iso(created_at + timedelta(hours=4)),
            )
        if item["status"] in {acceptance, closed}:
            _insert_log(
                conn,
                hazard_id,
                "submit_rectification",
                rectifying,
                acceptance,
                item["owner"] or "责任人",
                item.get("result"),
                _iso(created_at + timedelta(hours=28)),
            )
        if item["status"] == closed:
            _insert_log(
                conn,
                hazard_id,
                "accept",
                acceptance,
                closed,
                "安全管理员",
                item.get("acceptance"),
                _iso(created_at + timedelta(hours=52)),
            )
