"""隐患接口的请求与响应模型，集中做字段校验。"""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.hazard import HAZARD_LEVELS, HAZARD_TYPES


def _ensure_not_past(value: date) -> date:
    if value < date.today():
        raise ValueError("整改期限不能早于今天")
    return value


class HazardCreate(BaseModel):
    hazard_type: str = Field(..., description="隐患类型")
    hazard_level: str = Field(..., description="隐患等级")
    location: str = Field(..., min_length=1, max_length=100, description="隐患位置")
    description: str = Field(..., min_length=5, max_length=500, description="隐患描述")
    reporter: str = Field(..., min_length=1, max_length=30, description="上报人")
    due_date: date = Field(..., description="整改期限")
    image_url: Optional[str] = Field(None, max_length=300, description="模拟附件图片 URL")

    @field_validator("hazard_type")
    @classmethod
    def check_type(cls, value: str) -> str:
        if value not in HAZARD_TYPES:
            raise ValueError(f"隐患类型必须是：{'、'.join(HAZARD_TYPES)}")
        return value

    @field_validator("hazard_level")
    @classmethod
    def check_level(cls, value: str) -> str:
        if value not in HAZARD_LEVELS:
            raise ValueError(f"隐患等级必须是：{'、'.join(HAZARD_LEVELS)}")
        return value

    @field_validator("location", "description", "reporter")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("内容不能为空白")
        return stripped

    @field_validator("due_date")
    @classmethod
    def check_due_date(cls, value: date) -> date:
        return _ensure_not_past(value)


class AssignRequest(BaseModel):
    owner: str = Field(..., min_length=1, max_length=30, description="整改责任人")
    due_date: date = Field(..., description="整改期限")
    auditor: str = Field("安全管理员", min_length=1, max_length=30, description="审核人")
    comment: Optional[str] = Field(None, max_length=200, description="审核意见")

    @field_validator("owner", "auditor")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("内容不能为空白")
        return stripped

    @field_validator("due_date")
    @classmethod
    def check_due_date(cls, value: date) -> date:
        return _ensure_not_past(value)


class RectificationRequest(BaseModel):
    rectification_measure: str = Field(..., min_length=2, max_length=500, description="整改措施")
    rectification_result: str = Field(..., min_length=2, max_length=500, description="整改完成情况")
    operator: str = Field(..., min_length=1, max_length=30, description="提交人（责任人）")

    @field_validator("rectification_measure", "rectification_result", "operator")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("内容不能为空白")
        return stripped


class AcceptanceRequest(BaseModel):
    decision: Literal["pass", "reject"] = Field(..., description="pass=验收通过并关闭，reject=退回整改")
    acceptance_comment: str = Field(..., min_length=2, max_length=300, description="验收意见")
    operator: str = Field("安全管理员", min_length=1, max_length=30, description="验收人")

    @field_validator("acceptance_comment", "operator")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("内容不能为空白")
        return stripped


class FlowLogOut(BaseModel):
    id: int
    hazard_id: int
    action: str
    from_status: Optional[str] = None
    to_status: str
    operator: str
    comment: Optional[str] = None
    created_at: str


class HazardOut(BaseModel):
    id: int
    hazard_no: str
    hazard_type: str
    hazard_level: str
    location: str
    description: str
    reporter: str
    owner: Optional[str] = None
    due_date: str
    status: str
    rectification_measure: Optional[str] = None
    rectification_result: Optional[str] = None
    acceptance_comment: Optional[str] = None
    image_url: Optional[str] = None
    is_overdue: bool = False
    created_at: str
    updated_at: str
    flow_logs: List[FlowLogOut] = Field(default_factory=list)


class HazardListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[HazardOut]


class CountItem(BaseModel):
    name: str
    count: int


class TrendItem(BaseModel):
    date: str
    count: int


class StatisticsOut(BaseModel):
    total: int
    pending_review: int
    rectifying: int
    pending_acceptance: int
    closed: int
    overdue: int
    closing_rate: float
    by_status: List[CountItem]
    by_level: List[CountItem]
    by_type: List[CountItem]
    trend: List[TrendItem]


class DictionaryOut(BaseModel):
    hazard_types: List[str]
    hazard_levels: List[str]
    statuses: List[str]
    owners: List[str]
