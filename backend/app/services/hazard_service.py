"""隐患业务服务：查询、上报、状态流转与统计。"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone

from app.db import transaction
from app.errors import HazardNotFound, InvalidTransition
from app.models.enums import (
    ACTION_LABELS,
    STATUS_TRANSITIONS,
    HazardLevel,
    HazardStatus,
    HazardType,
)
from app.schemas.hazard import (
    HazardAcceptanceRequest,
    HazardAssignRequest,
    HazardCreate,
    HazardDetail,
    HazardListResponse,
    HazardLogOut,
    HazardOut,
    HazardRectificationRequest,
    HazardStatistics,
    TrendPoint,
)

SORT_COLUMNS = {
    "hazard_no": "hazard_no",
    "due_date": "due_date",
    "created_at": "created_at",
    "updated_at": "updated_at",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _escape_like(keyword: str) -> str:
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _is_overdue(due_date: str, status: str) -> bool:
    if status == HazardStatus.CLOSED.value:
        return False
    return date.fromisoformat(due_date) < date.today()


def _to_out(row: sqlite3.Row) -> HazardOut:
    data = dict(row)
    data["is_overdue"] = _is_overdue(data["due_date"], data["status"])
    return HazardOut.model_validate(data)


def _load(conn: sqlite3.Connection, hazard_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM hazards WHERE id = ?", (hazard_id,)).fetchone()
    if row is None:
        raise HazardNotFound(f"未找到 id 为 {hazard_id} 的隐患记录")
    return row


def _next_status(current: str, action: str) -> str:
    allowed = STATUS_TRANSITIONS.get(current, {})
    if action not in allowed:
        label = ACTION_LABELS.get(action, action)
        raise InvalidTransition(f"当前状态「{current}」不允许执行「{label}」操作")
    return allowed[action]


def _add_log(
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


def _next_hazard_no(conn: sqlite3.Connection, today: date) -> str:
    prefix = f"HSE-{today.strftime('%Y%m%d')}-"
    row = conn.execute(
        "SELECT hazard_no FROM hazards WHERE hazard_no LIKE ? ORDER BY hazard_no DESC LIMIT 1",
        (prefix + "%",),
    ).fetchone()
    sequence = int(row["hazard_no"].rsplit("-", 1)[1]) + 1 if row else 1
    return f"{prefix}{sequence:04d}"


def list_hazards(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    hazard_type: str | None = None,
    level: str | None = None,
    keyword: str | None = None,
    overdue: bool | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> HazardListResponse:
    """按状态、等级、类型、关键字筛选，支持分页与排序。"""

    conditions: list[str] = []
    params: list[object] = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if hazard_type:
        conditions.append("hazard_type = ?")
        params.append(hazard_type)
    if level:
        conditions.append("hazard_level = ?")
        params.append(level)
    if keyword:
        pattern = f"%{_escape_like(keyword)}%"
        conditions.append(
            "(hazard_no LIKE ? ESCAPE '\\' OR location LIKE ? ESCAPE '\\' "
            "OR description LIKE ? ESCAPE '\\' OR reporter LIKE ? ESCAPE '\\' "
            "OR owner LIKE ? ESCAPE '\\')"
        )
        params.extend([pattern] * 5)
    if overdue:
        conditions.append("status <> ? AND due_date < ?")
        params.extend([HazardStatus.CLOSED.value, date.today().isoformat()])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    total = int(
        conn.execute(
            f"SELECT COUNT(*) AS total FROM hazards {where_clause}", params
        ).fetchone()["total"]
    )

    column = SORT_COLUMNS[sort_by]
    order = "ASC" if sort_order == "asc" else "DESC"
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"""
        SELECT * FROM hazards {where_clause}
        ORDER BY {column} {order}, id {order}
        LIMIT ? OFFSET ?
        """,
        [*params, page_size, offset],
    ).fetchall()

    return HazardListResponse(
        items=[_to_out(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_hazard(conn: sqlite3.Connection, hazard_id: int) -> HazardDetail:
    row = _load(conn, hazard_id)
    log_rows = conn.execute(
        "SELECT * FROM hazard_logs WHERE hazard_id = ? ORDER BY id ASC", (hazard_id,)
    ).fetchall()
    logs = [
        HazardLogOut(
            id=log["id"],
            action=log["action"],
            action_label=ACTION_LABELS.get(log["action"], log["action"]),
            from_status=log["from_status"],
            to_status=log["to_status"],
            operator=log["operator"],
            comment=log["comment"],
            created_at=log["created_at"],
        )
        for log in log_rows
    ]
    data = dict(row)
    data["is_overdue"] = _is_overdue(data["due_date"], data["status"])
    data["logs"] = logs
    return HazardDetail.model_validate(data)


def create_hazard(conn: sqlite3.Connection, payload: HazardCreate) -> HazardDetail:
    """上报隐患：生成编号并写入待审核状态。"""

    now = _now_iso()
    with transaction(conn):
        hazard_no = _next_hazard_no(conn, date.today())
        cursor = conn.execute(
            """
            INSERT INTO hazards
                (hazard_no, hazard_type, hazard_level, location, description, reporter,
                 owner, due_date, status, rectification_measure, rectification_result,
                 acceptance_comment, attachment_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, NULL, NULL, ?, ?, ?)
            """,
            (
                hazard_no,
                payload.hazard_type.value,
                payload.hazard_level.value,
                payload.location,
                payload.description,
                payload.reporter,
                payload.due_date.isoformat(),
                HazardStatus.PENDING_REVIEW.value,
                payload.attachment_url,
                now,
                now,
            ),
        )
        hazard_id = int(cursor.lastrowid)
        _add_log(
            conn,
            hazard_id,
            "create",
            None,
            HazardStatus.PENDING_REVIEW.value,
            payload.reporter,
            "现场发现隐患并上报。",
            now,
        )
    return get_hazard(conn, hazard_id)


def assign_hazard(
    conn: sqlite3.Connection, hazard_id: int, payload: HazardAssignRequest
) -> HazardDetail:
    """审核并分派责任人，状态流转为整改中。"""

    now = _now_iso()
    with transaction(conn):
        row = _load(conn, hazard_id)
        next_status = _next_status(row["status"], "assign")
        due_date = payload.due_date.isoformat() if payload.due_date else row["due_date"]
        conn.execute(
            """
            UPDATE hazards
            SET owner = ?, due_date = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (payload.owner, due_date, next_status, now, hazard_id),
        )
        comment = payload.comment or f"审核通过，分派责任人 {payload.owner}，整改期限 {due_date}。"
        _add_log(
            conn,
            hazard_id,
            "assign",
            row["status"],
            next_status,
            payload.operator,
            comment,
            now,
        )
    return get_hazard(conn, hazard_id)


def submit_rectification(
    conn: sqlite3.Connection, hazard_id: int, payload: HazardRectificationRequest
) -> HazardDetail:
    """责任人提交整改措施与完成情况，状态流转为待验收。"""

    now = _now_iso()
    with transaction(conn):
        row = _load(conn, hazard_id)
        next_status = _next_status(row["status"], "submit_rectification")
        attachment = payload.attachment_url or row["attachment_url"]
        conn.execute(
            """
            UPDATE hazards
            SET rectification_measure = ?, rectification_result = ?,
                attachment_url = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                payload.rectification_measure,
                payload.rectification_result,
                attachment,
                next_status,
                now,
                hazard_id,
            ),
        )
        _add_log(
            conn,
            hazard_id,
            "submit_rectification",
            row["status"],
            next_status,
            payload.operator,
            payload.rectification_result,
            now,
        )
    return get_hazard(conn, hazard_id)


def accept_hazard(
    conn: sqlite3.Connection, hazard_id: int, payload: HazardAcceptanceRequest
) -> HazardDetail:
    """验收通过则关闭隐患，退回则回到整改中。"""

    now = _now_iso()
    action = "accept" if payload.approved else "reject"
    with transaction(conn):
        row = _load(conn, hazard_id)
        next_status = _next_status(row["status"], action)
        conn.execute(
            """
            UPDATE hazards
            SET acceptance_comment = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (payload.acceptance_comment, next_status, now, hazard_id),
        )
        _add_log(
            conn,
            hazard_id,
            action,
            row["status"],
            next_status,
            payload.operator,
            payload.acceptance_comment,
            now,
        )
    return get_hazard(conn, hazard_id)


def get_statistics(conn: sqlite3.Connection) -> HazardStatistics:
    """统计各状态、等级、类型数量，超期数量与近 7 日上报趋势。"""

    total = int(conn.execute("SELECT COUNT(*) AS total FROM hazards").fetchone()["total"])

    status_counts = {item.value: 0 for item in HazardStatus}
    for row in conn.execute(
        "SELECT status, COUNT(*) AS count FROM hazards GROUP BY status"
    ).fetchall():
        status_counts[row["status"]] = int(row["count"])

    level_counts = {item.value: 0 for item in HazardLevel}
    for row in conn.execute(
        "SELECT hazard_level, COUNT(*) AS count FROM hazards GROUP BY hazard_level"
    ).fetchall():
        level_counts[row["hazard_level"]] = int(row["count"])

    type_counts = {item.value: 0 for item in HazardType}
    for row in conn.execute(
        "SELECT hazard_type, COUNT(*) AS count FROM hazards GROUP BY hazard_type"
    ).fetchall():
        type_counts[row["hazard_type"]] = int(row["count"])

    overdue_count = int(
        conn.execute(
            "SELECT COUNT(*) AS total FROM hazards WHERE status <> ? AND due_date < ?",
            (HazardStatus.CLOSED.value, date.today().isoformat()),
        ).fetchone()["total"]
    )

    closed_total = status_counts[HazardStatus.CLOSED.value]
    closed_rate = round(closed_total * 100 / total, 1) if total else 0.0

    start_day = date.today() - timedelta(days=6)
    daily = {
        row["day"]: int(row["count"])
        for row in conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM hazards
            WHERE substr(created_at, 1, 10) >= ?
            GROUP BY day
            """,
            (start_day.isoformat(),),
        ).fetchall()
    }
    recent = [
        TrendPoint(
            date=start_day + timedelta(days=offset),
            count=daily.get((start_day + timedelta(days=offset)).isoformat(), 0),
        )
        for offset in range(7)
    ]

    return HazardStatistics(
        total=total,
        status_counts=status_counts,
        level_counts=level_counts,
        type_counts=type_counts,
        overdue_count=overdue_count,
        closed_rate=closed_rate,
        recent_7_days=recent,
    )
