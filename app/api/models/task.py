from pydantic import BaseModel
from typing import Optional, Any, Dict
from enum import Enum


class TaskStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskTriggerRequest(BaseModel):
    """任务触发请求"""
    run_immediately: bool = True
    override_config: Optional[Dict[str, Any]] = None


class TaskTriggerResponse(BaseModel):
    """任务触发响应"""
    task_id: str
    task_type: str
    status: TaskStatus
    message: str
    started_at: Optional[str] = None


class TaskResponse(BaseModel):
    """任务执行结果响应"""
    task_id: str
    task_type: str
    status: TaskStatus
    message: str
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str
    task_type: str
    description: str
    cron: Optional[str] = None
    status: TaskStatus
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    config: Dict[str, Any]