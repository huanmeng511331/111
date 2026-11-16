"""隐患相关请求与响应模型。"""

from __future__ import annotations

from datetime import date, datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import HazardLevel, HazardStatus, HazardType


def _validate_attachment_url(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("附件地址必须是 http/https 开头的合法链接")
    return value


def _validate_due_date(value: date | None) -> date | None:
    if value is not None and value < date.today():
        raise ValueError("整改期限不能早于今天")
    return value


class HazardCreate(BaseModel):
    """上报隐患请求。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    hazard_type: HazardType
    hazard_level: HazardLevel
    location: str = Field(min_length=2, max_length=100, description="隐患位置")
    description: str = Field(min_length=5, max_length=500, description="隐患描述")
    reporter: str = Field(min_length=2, max_length=30, description="上报人")
    due_date: date = Field(description="整改期限")
    attachment_url: str | None = Field(default=None, max_length=500)

    @field_validator("attachment_url")
    @classmethod
    def _check_url(cls, value: str | None) -> str | None:
        return _validate_attachment_url(value)

    @field_validator("due_date")
    @classmethod
    def _check_due_date(cls, value: date | None) -> date | None:
        return _validate_due_date(value)


class HazardAssignRequest(BaseModel):
    """审核并分派请求。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    owner: str = Field(min_length=2, max_length=30, description="责任人")
    due_date: date | None = Field(default=None, description="调整后的整改期限")
    operator: str = Field(default="安全管理员", min_length=2, max_length=30)
    comment: str | None = Field(default=None, max_length=200)

    @field_validator("due_date")
    @classmethod
    def _check_due_date(cls, value: date | None) -> date | None:
        return _validate_due_date(value)


class HazardRectificationRequest(BaseModel):
    """提交整改请求。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    rectification_measure: str = Field(min_length=5, max_length=500, description="整改措施")
    rectification_result: str = Field(min_length=5, max_length=500, description="整改完成情况")
    operator: str = Field(default="责任人", min_length=2, max_length=30)
    attachment_url: str | None = Field(default=None, max_length=500)

    @field_validator("attachment_url")
    @classmethod
    def _check_url(cls, value: str | None) -> str | None:
        return _validate_attachment_url(value)


class HazardAcceptanceRequest(BaseModel):
    """验收请求：通过后关闭，退回则回到整改中。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    approved: bool = Field(description="true 表示验收通过，false 表示退回整改")
    acceptance_comment: str = Field(min_length=2, max_length=300, description="验收意见")
    operator: str = Field(default="安全管理员", min_length=2, max_length=30)


class HazardLogOut(BaseModel):
    """状态流转记录。"""

    id: int
    action: str
    action_label: str
    from_status: str | None
    to_status: str
    operator: str | None
    comment: str | None
    created_at: datetime


class HazardOut(BaseModel):
    """隐患记录（列表与操作响应）。"""

    id: int
    hazard_no: str
    hazard_type: str
    hazard_level: str
    location: str
    description: str
    reporter: str
    owner: str | None
    due_date: date
    status: str
    rectification_measure: str | None
    rectification_result: str | None
    acceptance_comment: str | None
    attachment_url: str | None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool


class HazardDetail(HazardOut):
    """隐患详情，附带状态流转记录。"""

    logs: list[HazardLogOut]


class HazardListResponse(BaseModel):
    """分页列表响应。"""

    items: list[HazardOut]
    total: int
    page: int
    page_size: int


class TrendPoint(BaseModel):
    """按日趋势点。"""

    date: date
    count: int


class HazardStatistics(BaseModel):
    """统计看板数据。"""

    total: int
    status_counts: dict[str, int]
    level_counts: dict[str, int]
    type_counts: dict[str, int]
    overdue_count: int
    closed_rate: float
    recent_7_days: list[TrendPoint]


class HazardOptions(BaseModel):
    """枚举选项，供前端筛选与表单使用。"""

    types: list[str]
    levels: list[str]
    statuses: list[str]

    @classmethod
    def build(cls) -> "HazardOptions":
        return cls(
            types=[item.value for item in HazardType],
            levels=[item.value for item in HazardLevel],
            statuses=[item.value for item in HazardStatus],
        )
