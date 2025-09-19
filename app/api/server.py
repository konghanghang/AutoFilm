from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings, logger
from app.api.routers import tasks, health
from app.version import APP_VERSION

# 创建 FastAPI 应用
app = FastAPI(
    title="AutoFilm API",
    description="API for AutoFilm - A tool for Emby/Jellyfin servers to provide direct streaming",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置 CORS
api_config = getattr(settings, 'APIConfig', {})
cors_origins = api_config.get('cors_origins', ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(tasks.router)


@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    logger.info(f"AutoFilm API v{APP_VERSION} 正在启动...")
    logger.info(f"API 文档地址: /api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件
    """
    logger.info("AutoFilm API 正在关闭...")