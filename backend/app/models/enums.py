"""隐患类型、等级、状态及状态机定义。

数据库与接口统一使用中文业务枚举值，前端展示无需额外映射，
避免出现"码头值不一致"导致的筛选与状态判断偏差。
"""

from enum import Enum


class HazardType(str, Enum):
    """隐患类型。"""

    FIRE = "消防安全"
    ELECTRIC = "电气安全"
    EQUIPMENT = "设备设施"
    OPERATION = "作业行为"
    OCCUPATIONAL_HEALTH = "职业健康"
    ENVIRONMENT = "环境环保"
    OTHER = "其他"


class HazardLevel(str, Enum):
    """隐患等级。"""

    GENERAL = "一般"
    MAJOR = "较大"
    CRITICAL = "重大"


class HazardStatus(str, Enum):
    """隐患状态。"""

    PENDING_REVIEW = "待审核"
    RECTIFYING = "整改中"
    PENDING_ACCEPTANCE = "待验收"
    CLOSED = "已关闭"


# 状态机：当前状态 -> {动作: 下一状态}，与需求 6.6 状态规则一致。
STATUS_TRANSITIONS: dict[str, dict[str, str]] = {
    HazardStatus.PENDING_REVIEW.value: {
        "assign": HazardStatus.RECTIFYING.value,
    },
    HazardStatus.RECTIFYING.value: {
        "submit_rectification": HazardStatus.PENDING_ACCEPTANCE.value,
    },
    HazardStatus.PENDING_ACCEPTANCE.value: {
        "accept": HazardStatus.CLOSED.value,
        "reject": HazardStatus.RECTIFYING.value,
    },
}

ACTION_LABELS: dict[str, str] = {
    "create": "上报隐患",
    "assign": "审核并分派",
    "submit_rectification": "提交整改",
    "accept": "验收通过并关闭",
    "reject": "验收退回",
}
