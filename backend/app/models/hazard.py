"""隐患数据模型：状态/等级/类型字典、状态机与行转换。"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from app.db import get_connection

STATUS_PENDING_REVIEW = "待审核"
STATUS_RECTIFYING = "整改中"
STATUS_PENDING_ACCEPTANCE = "待验收"
STATUS_CLOSED = "已关闭"

ALL_STATUSES = [
    STATUS_PENDING_REVIEW,
    STATUS_RECTIFYING,
    STATUS_PENDING_ACCEPTANCE,
    STATUS_CLOSED,
]

HAZARD_LEVELS = ["一般", "较大", "重大"]
HAZARD_TYPES = ["消防", "用电", "设备设施", "作业行为", "环境", "职业健康"]

# 状态机：当前状态 -> 允许的动作 -> 下一状态（需求 6.6）
TRANSITIONS = {
    STATUS_PENDING_REVIEW: {"审核并分派": STATUS_RECTIFYING},
    STATUS_RECTIFYING: {"提交整改": STATUS_PENDING_ACCEPTANCE},
    STATUS_PENDING_ACCEPTANCE: {
        "验收通过": STATUS_CLOSED,
        "验收退回": STATUS_RECTIFYING,
    },
    STATUS_CLOSED: {},
}

NOW_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_text() -> str:
    return datetime.now().strftime(NOW_FORMAT)


def is_overdue(status: str, due_date: Optional[str]) -> bool:
    """未关闭且整改期限早于今天既视为超期。"""
    if not due_date or status == STATUS_CLOSED:
        return False
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return False
    return due < date.today()


def hazard_to_dict(row: Any) -> Dict[str, Any]:
    record = dict(row)
    record["is_overdue"] = is_overdue(record.get("status"), record.get("due_date"))
    return record


def flow_log_to_dict(row: Any) -> Dict[str, Any]:
    return dict(row)


def fetch_flow_logs(connection: Any, hazard_id: int) -> list:
    rows = connection.execute(
        "SELECT id, hazard_id, action, from_status, to_status, operator, comment, created_at "
        "FROM hazard_flow_logs WHERE hazard_id = ? ORDER BY id ASC",
        (hazard_id,),
    ).fetchall()
    return [flow_log_to_dict(row) for row in rows]


def add_flow_log(
    connection: Any,
    hazard_id: int,
    action: str,
    from_status: Optional[str],
    to_status: str,
    operator: str,
    comment: Optional[str] = None,
) -> None:
    connection.execute(
        "INSERT INTO hazard_flow_logs "
        "(hazard_id, action, from_status, to_status, operator, comment, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (hazard_id, action, from_status, to_status, operator, comment, now_text()),
    )


def next_hazard_no(connection: Any) -> str:
    """按天生成 HZ-YYYYMMDD-NNN 形式的隐患编号。"""
    prefix = "HZ-" + date.today().strftime("%Y%m%d")
    row = connection.execute(
        "SELECT hazard_no FROM hazards WHERE hazard_no LIKE ? ORDER BY hazard_no DESC LIMIT 1",
        (prefix + "-%",),
    ).fetchone()
    if row is None:
        sequence = 1
    else:
        sequence = int(str(row["hazard_no"]).rsplit("-", 1)[-1]) + 1
    return f"{prefix}-{sequence:03d}"


def find_hazard(connection: Any, hazard_id: int) -> Optional[Dict[str, Any]]:
    row = connection.execute("SELECT * FROM hazards WHERE id = ?", (hazard_id,)).fetchone()
    return hazard_to_dict(row) if row else None
