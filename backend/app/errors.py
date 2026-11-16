"""领域异常定义，由接口层统一转换为 JSON 错误响应。"""


class DomainError(Exception):
    """业务异常基类。"""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class HazardNotFound(DomainError):
    """隐患记录不存在。"""

    status_code = 404


class InvalidTransition(DomainError):
    """当前状态不允许执行该操作。"""

    status_code = 409
