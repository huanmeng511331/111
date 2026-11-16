"""隐患业务逻辑：查询、上报、分派、整改、验收与统计。"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.db import get_connection
from app.models.hazard import (
    ALL_STATUSES,
    HAZARD_LEVELS,
    HAZARD_TYPES,
    STATUS_CLOSED,
    STATUS_PENDING_ACCEPTANCE,
    STATUS_PENDING_REVIEW,
    STATUS_RECTIFYING,
    TRANSITIONS,
    add_flow_log,
    fetch_flow_logs,
    find_hazard,
    hazard_to_dict,
    next_hazard_no,
    now_text,
)
from app.schemas.hazard import (
    AcceptanceRequest,
    AssignRequest,
    HazardCreate,
    RectificationRequest,
)
from app.services.errors import HazardError

SORTABLE_COLUMNS = {
    "created_at": "created_at",
    "due_date": "due_date",
    "status": "status",
    "hazard_level": (
        "CASE hazard_level WHEN '重大' THEN 1 WHEN '较大' THEN 2 WHEN '一般' THEN 3 ELSE 4 END"
    ),
    "hazard_no": "hazard_no",
}

OWNER_CANDIDATES = ["张伟（设备部）", "李强（安全部）", "王敏（生产一部）", "赵磊（后勤部）"]


def _load_or_404(connection: Any, hazard_id: int) -> Dict[str, Any]:
    hazard = find_hazard(connection, hazard_id)
    if hazard is None:
        raise HazardError(f"隐患 {hazard_id} 不存在", status_code=404, code="HAZARD_NOT_FOUND")
    return hazard


def _require_status(hazard: Dict[str, Any], expected: str, action: str) -> None:
    if hazard["status"] != expected:
        raise HazardError(
            f"当前状态为「{hazard['status']}」，仅「{expected}」状态可执行「{action}」",
            status_code=409,
            code="INVALID_STATUS_TRANSITION",
        )


def list_hazards(
    status: Optional[str] = None,
    hazard_level: Optional[str] = None,
    hazard_type: Optional[str] = None,
    keyword: Optional[str] = None,
    overdue_only: bool = False,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> Dict[str, Any]:
    if status and status not in ALL_STATUSES:
        raise HazardError(f"状态必须是：{'、'.join(ALL_STATUSES)}")
    if hazard_level and hazard_level not in HAZARD_LEVELS:
        raise HazardError(f"等级必须是：{'、'.join(HAZARD_LEVELS)}")
    if hazard_type and hazard_type not in HAZARD_TYPES:
        raise HazardError(f"类型必须是：{'、'.join(HAZARD_TYPES)}")

    conditions: List[str] = []
    params: List[Any] = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if hazard_level:
        conditions.append("hazard_level = ?")
        params.append(hazard_level)
    if hazard_type:
        conditions.append("hazard_type = ?")
        params.append(hazard_type)
    if keyword:
        conditions.append(
            "(hazard_no LIKE ? OR location LIKE ? OR description LIKE ? OR owner LIKE ?)"
        )
        like_keyword = f"%{keyword.strip()}%"
        params.extend([like_keyword] * 4)
    if overdue_only:
        conditions.append("status != ? AND due_date < ?")
        params.extend([STATUS_CLOSED, date.today().isoformat()])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order_column = SORTABLE_COLUMNS.get(sort_by, "created_at")
    order_direction = "ASC" if str(sort_order).lower() == "asc" else "DESC"
    offset = (page - 1) * page_size

    with get_connection() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) AS total FROM hazards {where_clause}", params
        ).fetchone()["total"]
        rows = connection.execute(
            f"SELECT * FROM hazards {where_clause} "
            f"ORDER BY {order_column} {order_direction}, id {order_direction} "
            "LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [hazard_to_dict(row) for row in rows],
    }


def get_hazard(hazard_id: int) -> Dict[str, Any]:
    with get_connection() as connection:
        hazard = _load_or_404(connection, hazard_id)
        hazard["flow_logs"] = fetch_flow_logs(connection, hazard_id)
    return hazard


def create_hazard(payload: HazardCreate) -> Dict[str, Any]:
    timestamp = now_text()
    with get_connection() as connection:
        hazard_no = next_hazard_no(connection)
        cursor = connection.execute(
            "INSERT INTO hazards (hazard_no, hazard_type, hazard_level, location, description, "
            "reporter, owner, due_date, status, image_url, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                hazard_no,
                payload.hazard_type,
                payload.hazard_level,
                payload.location,
                payload.description,
                payload.reporter,
                None,
                payload.due_date.isoformat(),
                STATUS_PENDING_REVIEW,
                payload.image_url or None,
                timestamp,
                timestamp,
            ),
        )
        hazard_id = int(cursor.lastrowid)
        add_flow_log(
            connection,
            hazard_id,
            action="上报隐患",
            from_status=None,
            to_status=STATUS_PENDING_REVIEW,
            operator=payload.reporter,
            comment=payload.description,
        )
        hazard = _load_or_404(connection, hazard_id)
        hazard["flow_logs"] = fetch_flow_logs(connection, hazard_id)
    return hazard


def assign_hazard(hazard_id: int, payload: AssignRequest) -> Dict[str, Any]:
    with get_connection() as connection:
        hazard = _load_or_404(connection, hazard_id)
        _require_status(hazard, STATUS_PENDING_REVIEW, "审核并分派")
        target_status = TRANSITIONS[STATUS_PENDING_REVIEW]["审核并分派"]
        connection.execute(
            "UPDATE hazards SET owner = ?, due_date = ?, status = ?, updated_at = ? WHERE id = ?",
            (
                payload.owner,
                payload.due_date.isoformat(),
                target_status,
                now_text(),
                hazard_id,
            ),
        )
        add_flow_log(
            connection,
            hazard_id,
            action="审核并分派",
            from_status=STATUS_PENDING_REVIEW,
            to_status=target_status,
            operator=payload.auditor,
            comment=payload.comment or f"分派给 {payload.owner}，整改期限 {payload.due_date.isoformat()}",
        )
        updated = _load_or_404(connection, hazard_id)
        updated["flow_logs"] = fetch_flow_logs(connection, hazard_id)
    return updated


def submit_rectification(hazard_id: int, payload: RectificationRequest) -> Dict[str, Any]:
    with get_connection() as connection:
        hazard = _load_or_404(connection, hazard_id)
        _require_status(hazard, STATUS_RECTIFYING, "提交整改")
        target_status = TRANSITIONS[STATUS_RECTIFYING]["提交整改"]
        connection.execute(
            "UPDATE hazards SET rectification_measure = ?, rectification_result = ?, "
            "status = ?, updated_at = ? WHERE id = ?",
            (
                payload.rectification_measure,
                payload.rectification_result,
                target_status,
                now_text(),
                hazard_id,
            ),
        )
        add_flow_log(
            connection,
            hazard_id,
            action="提交整改",
            from_status=STATUS_RECTIFYING,
            to_status=target_status,
            operator=payload.operator,
            comment=payload.rectification_result,
        )
        updated = _load_or_404(connection, hazard_id)
        updated["flow_logs"] = fetch_flow_logs(connection, hazard_id)
    return updated


def accept_hazard(hazard_id: int, payload: AcceptanceRequest) -> Dict[str, Any]:
    with get_connection() as connection:
        hazard = _load_or_404(connection, hazard_id)
        _require_status(hazard, STATUS_PENDING_ACCEPTANCE, "验收")
        action = "验收通过" if payload.decision == "pass" else "验收退回"
        target_status = TRANSITIONS[STATUS_PENDING_ACCEPTANCE][action]
        connection.execute(
            "UPDATE hazards SET acceptance_comment = ?, status = ?, updated_at = ? WHERE id = ?",
            (payload.acceptance_comment, target_status, now_text(), hazard_id),
        )
        add_flow_log(
            connection,
            hazard_id,
            action=action,
            from_status=STATUS_PENDING_ACCEPTANCE,
            to_status=target_status,
            operator=payload.operator,
            comment=payload.acceptance_comment,
        )
        updated = _load_or_404(connection, hazard_id)
        updated["flow_logs"] = fetch_flow_logs(connection, hazard_id)
    return updated


def get_statistics() -> Dict[str, Any]:
    today = date.today()
    overdue = 0
    trend_start = (today - timedelta(days=6)).isoformat()

    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS total FROM hazards").fetchone()["total"]
        status_rows = connection.execute(
            "SELECT status AS name, COUNT(*) AS count FROM hazards GROUP BY status"
        ).fetchall()
        level_rows = connection.execute(
            "SELECT hazard_level AS name, COUNT(*) AS count FROM hazards "
            "GROUP BY hazard_level "
            "ORDER BY CASE hazard_level WHEN '重大' THEN 1 WHEN '较大' THEN 2 "
            "WHEN '一般' THEN 3 ELSE 4 END"
        ).fetchall()
        type_rows = connection.execute(
            "SELECT hazard_type AS name, COUNT(*) AS count FROM hazards "
            "GROUP BY hazard_type ORDER BY count DESC, name ASC"
        ).fetchall()
        trend_rows = connection.execute(
            "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count FROM hazards "
            "WHERE substr(created_at, 1, 10) >= ? GROUP BY day",
            (trend_start,),
        ).fetchall()
        overdue = connection.execute(
            "SELECT COUNT(*) AS total FROM hazards WHERE status != ? AND due_date < ?",
            (STATUS_CLOSED, today.isoformat()),
        ).fetchone()["total"]

    status_counts = {row["name"]: row["count"] for row in status_rows}
    trend_counts = {row["day"]: row["count"] for row in trend_rows}
    closed = status_counts.get(STATUS_CLOSED, 0)

    trend = [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "count": trend_counts.get((today - timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(6, -1, -1)
    ]

    return {
        "total": total,
        "pending_review": status_counts.get(STATUS_PENDING_REVIEW, 0),
        "rectifying": status_counts.get(STATUS_RECTIFYING, 0),
        "pending_acceptance": status_counts.get(STATUS_PENDING_ACCEPTANCE, 0),
        "closed": closed,
        "overdue": overdue,
        "closing_rate": round(closed / total * 100, 1) if total else 0.0,
        "by_status": [{"name": name, "count": status_counts.get(name, 0)} for name in ALL_STATUSES],
        "by_level": [{"name": row["name"], "count": row["count"]} for row in level_rows],
        "by_type": [{"name": row["name"], "count": row["count"]} for row in type_rows],
        "trend": trend,
    }


def get_dictionaries() -> Dict[str, Any]:
    return {
        "hazard_types": HAZARD_TYPES,
        "hazard_levels": HAZARD_LEVELS,
        "statuses": ALL_STATUSES,
        "owners": OWNER_CANDIDATES,
    }
