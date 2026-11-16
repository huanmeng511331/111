"""FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import init_db, resolve_db_path
from app.errors import DomainError
from app.routers import hazards


def create_app(db_path: Path | None = None) -> FastAPI:
    """创建应用实例，测试可传入独立数据库文件路径。"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(app.state.db_path)
        yield

    app = FastAPI(
        title="HSE 隐患上报与闭环管理 API",
        description="现场隐患上报、审核分派、整改、验收关闭与统计的演示接口。",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.db_path = Path(db_path) if db_path else resolve_db_path()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(hazards.router)

    @app.get("/api/health", tags=["系统"], summary="健康检查")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
