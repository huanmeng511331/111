"""业务异常：由路由层转换为统一 JSON 错误响应。"""


class HazardError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
