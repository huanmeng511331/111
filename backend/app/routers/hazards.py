"""隐患相关 REST API。"""

from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.hazard import (
    AcceptanceRequest,
    AssignRequest,
    DictionaryOut,
    HazardCreate,
    HazardListOut,
    HazardOut,
    RectificationRequest,
    StatisticsOut,
)
from app.services import hazard_service

router = APIRouter(prefix="/hazards", tags=["隐患管理"])


@router.get("", response_model=HazardListOut, summary="查询隐患列表（支持筛选/分页/排序）")
def list_hazards(
    status: Optional[str] = Query(None, description="状态：待审核/整改中/待验收/已关闭"),
    hazard_level: Optional[str] = Query(None, alias="level", description="隐患等级"),
    hazard_type: Optional[str] = Query(None, alias="type", description="隐患类型"),
    keyword: Optional[str] = Query(None, description="编号/位置/描述/责任人关键字"),
    overdue_only: bool = Query(False, description="仅看已超期隐患"),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    sort_by: str = Query("created_at", description="排序字段：created_at/due_date/status/hazard_level/hazard_no"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
) -> HazardListOut:
    return hazard_service.list_hazards(
        status=status,
        hazard_level=hazard_level,
        hazard_type=hazard_type,
        keyword=keyword,
        overdue_only=overdue_only,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("", response_model=HazardOut, status_code=201, summary="上报隐患")
def create_hazard(payload: HazardCreate) -> HazardOut:
    return hazard_service.create_hazard(payload)


@router.get("/statistics", response_model=StatisticsOut, summary="查询隐患统计数据")
def get_statistics() -> StatisticsOut:
    return hazard_service.get_statistics()


@router.get("/dictionaries", response_model=DictionaryOut, summary="查询筛选项字典")
def get_dictionaries() -> DictionaryOut:
    return hazard_service.get_dictionaries()


@router.get("/{hazard_id}", response_model=HazardOut, summary="查询隐患详情（含流转记录）")
def get_hazard(hazard_id: int) -> HazardOut:
    return hazard_service.get_hazard(hazard_id)


@router.patch("/{hazard_id}/assign", response_model=HazardOut, summary="审核并分派责任人")
def assign_hazard(hazard_id: int, payload: AssignRequest) -> HazardOut:
    return hazard_service.assign_hazard(hazard_id, payload)


@router.patch(
    "/{hazard_id}/rectification",
    response_model=HazardOut,
    summary="提交整改措施与整改结果",
)
def submit_rectification(hazard_id: int, payload: RectificationRequest) -> HazardOut:
    return hazard_service.submit_rectification(hazard_id, payload)


@router.patch(
    "/{hazard_id}/acceptance",
    response_model=HazardOut,
    summary="验收并关闭或退回整改",
)
def accept_hazard(hazard_id: int, payload: AcceptanceRequest) -> HazardOut:
    return hazard_service.accept_hazard(hazard_id, payload)
