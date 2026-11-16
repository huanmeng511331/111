"""隐患 API 路由。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, status

from app.db import connect
from app.models.enums import HazardLevel, HazardStatus, HazardType
from app.schemas.hazard import (
    HazardAcceptanceRequest,
    HazardAssignRequest,
    HazardCreate,
    HazardDetail,
    HazardListResponse,
    HazardOptions,
    HazardRectificationRequest,
    HazardStatistics,
)
from app.services import hazard_service

router = APIRouter(prefix="/api/hazards", tags=["隐患管理"])


def get_db(request: Request):
    """每个请求使用独立连接，请求结束即关闭。"""

    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


@router.get(
    "/options",
    response_model=HazardOptions,
    summary="查询隐患类型、等级、状态枚举",
)
def get_options() -> HazardOptions:
    return HazardOptions.build()


@router.get(
    "/statistics",
    response_model=HazardStatistics,
    summary="查询隐患统计数据",
)
def get_statistics(conn=Depends(get_db)) -> HazardStatistics:
    return hazard_service.get_statistics(conn)


@router.get("", response_model=HazardListResponse, summary="查询隐患列表")
@router.get("/", response_model=HazardListResponse, include_in_schema=False)
def list_hazards(
    status_filter: HazardStatus | None = Query(default=None, alias="status"),
    hazard_type: HazardType | None = Query(default=None, alias="type"),
    level: HazardLevel | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=50),
    overdue: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: Literal["hazard_no", "due_date", "created_at", "updated_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    conn=Depends(get_db),
) -> HazardListResponse:
    """支持按状态、等级、类型、关键字、是否超期筛选，并分页排序。"""

    return hazard_service.list_hazards(
        conn,
        status=status_filter.value if status_filter else None,
        hazard_type=hazard_type.value if hazard_type else None,
        level=level.value if level else None,
        keyword=keyword.strip() if keyword else None,
        overdue=overdue,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "",
    response_model=HazardDetail,
    status_code=status.HTTP_201_CREATED,
    summary="上报隐患",
)
@router.post(
    "/",
    response_model=HazardDetail,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_hazard(payload: HazardCreate, conn=Depends(get_db)) -> HazardDetail:
    return hazard_service.create_hazard(conn, payload)


@router.get("/{hazard_id}", response_model=HazardDetail, summary="查询隐患详情")
def get_hazard(hazard_id: int, conn=Depends(get_db)) -> HazardDetail:
    return hazard_service.get_hazard(conn, hazard_id)


@router.patch(
    "/{hazard_id}/assign",
    response_model=HazardDetail,
    summary="审核并分派责任人",
)
def assign_hazard(
    hazard_id: int, payload: HazardAssignRequest, conn=Depends(get_db)
) -> HazardDetail:
    return hazard_service.assign_hazard(conn, hazard_id, payload)


@router.patch(
    "/{hazard_id}/rectification",
    response_model=HazardDetail,
    summary="提交整改措施与整改结果",
)
def submit_rectification(
    hazard_id: int, payload: HazardRectificationRequest, conn=Depends(get_db)
) -> HazardDetail:
    return hazard_service.submit_rectification(conn, hazard_id, payload)


@router.patch(
    "/{hazard_id}/acceptance",
    response_model=HazardDetail,
    summary="验收并关闭或退回整改",
)
def accept_hazard(
    hazard_id: int, payload: HazardAcceptanceRequest, conn=Depends(get_db)
) -> HazardDetail:
    return hazard_service.accept_hazard(conn, hazard_id, payload)
