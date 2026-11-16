"""FastAPI 应用入口：注册路由、CORS、异常处理并在启动时初始化演示数据。"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import API_PREFIX, CORS_ORIGINS
from app.db import init_db
from app.routers.hazards import router as hazards_router
from app.services.errors import HazardError
from app.services.seed import seed_demo_data

logger = logging.getLogger("hse")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    seeded = seed_demo_data()
    logger.info("数据库初始化完成，写入演示数据 %s 条", seeded)
    yield


app = FastAPI(
    title="HSE 隐患上报与闭环 Demo API",
    description="演示用隐患上报、审核分派、整改与验收闭环接口（模拟数据）。",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HazardError)
async def handle_hazard_error(_: Request, exc: HazardError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        messages.append(f"{field}: {error.get('msg', '参数不合法')}" if field else str(error.get("msg")))
    return JSONResponse(
        status_code=422,
        content={"detail": "；".join(messages), "code": "VALIDATION_ERROR"},
    )


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health() -> dict:
    return {"status": "ok", "service": "hse-hazard-demo"}


app.include_router(hazards_router, prefix=API_PREFIX)
