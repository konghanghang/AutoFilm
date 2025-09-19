from typing import Optional
from fastapi import Header, HTTPException, status
from app.core import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    验证 API 密钥

    :param x_api_key: API 密钥
    :return: 验证是否通过
    """
    # 如果配置中没有设置 API Key，则不需要验证
    api_config = getattr(settings, 'APIConfig', {})
    if not api_config:
        return True

    required_api_key = api_config.get('api_key')
    if not required_api_key:
        return True

    # 验证 API Key
    if not x_api_key or x_api_key != required_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return True


def get_task_manager():
    """
    获取任务管理器实例

    :return: TaskManager 实例
    """
    from app.core.task_manager import task_manager
    return task_manager