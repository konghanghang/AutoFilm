from fastapi import APIRouter
from datetime import datetime
from app.version import APP_VERSION

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/version")
async def get_version():
    """
    获取版本信息
    """
    return {
        "version": APP_VERSION,
        "app_name": "AutoFilm"
    }