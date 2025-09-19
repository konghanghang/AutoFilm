from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends, Body
from app.api.models import (
    TaskTriggerRequest,
    TaskTriggerResponse,
    TaskResponse,
    TaskInfo,
    TaskStatus,
    DirectoryTriggerRequest,
    DirectoriesTriggerRequest,
    QuickStrmRequest
)
from app.api.dependencies import verify_api_key, get_task_manager
from app.core import logger

router = APIRouter(prefix="/api", tags=["tasks"])


@router.get("/tasks", response_model=Dict[str, TaskInfo])
async def get_all_tasks(
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    获取所有任务列表和状态
    """
    return task_manager.get_all_tasks()


@router.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task_info(
    task_id: str,
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    获取指定任务信息
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return TaskInfo(
        task_id=task_id,
        task_type=task["type"],
        description=task["config"].get("id", task_id),
        cron=task["config"].get("cron"),
        status=task["status"],
        last_run=task["last_run"].isoformat() if task["last_run"] else None,
        next_run=None,
        config=task["config"]
    )


@router.post("/tasks/trigger/{task_type}/{task_id}", response_model=TaskTriggerResponse)
async def trigger_task(
    task_type: str,
    task_id: str,
    request: TaskTriggerRequest = TaskTriggerRequest(),
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    立即触发指定任务

    :param task_type: 任务类型 (alist2strm, ani2alist, libraryposter)
    :param task_id: 任务ID
    :param request: 触发请求参数
    """
    try:
        result = await task_manager.trigger_task(task_id, request.override_config)

        return TaskTriggerResponse(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.RUNNING,
            message=result["message"],
            started_at=result.get("started_at")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    获取任务执行状态
    """
    status = task_manager.get_task_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return {"task_id": task_id, "status": status}


@router.get("/tasks/{task_id}/history")
async def get_task_history(
    task_id: str,
    limit: int = 10,
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    获取任务执行历史
    """
    history = task_manager.get_task_history(task_id, limit)
    return {"task_id": task_id, "history": history}


# Alist2Strm 专用接口
@router.post("/alist2strm/{task_id}/directory")
async def trigger_directory(
    task_id: str,
    request: DirectoryTriggerRequest,
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    触发特定目录的 STRM 文件生成

    :param task_id: Alist2Strm 任务ID
    :param request: 目录触发请求
    """
    try:
        result = await task_manager.trigger_directory(
            task_id=task_id,
            directory=request.directory,
            sync_mode=request.sync_mode,
            overwrite=request.overwrite
        )

        return {
            "status": "success",
            "message": result["message"],
            "task_id": task_id,
            "directory": request.directory,
            "started_at": result.get("started_at")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process directory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alist2strm/{task_id}/directories")
async def trigger_directories(
    task_id: str,
    request: DirectoriesTriggerRequest,
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    批量触发多个目录的 STRM 文件生成

    :param task_id: Alist2Strm 任务ID
    :param request: 批量目录触发请求
    """
    results = []
    for directory in request.directories:
        try:
            result = await task_manager.trigger_directory(
                task_id=task_id,
                directory=directory,
                sync_mode=request.sync_mode,
                overwrite=request.overwrite
            )
            results.append({
                "directory": directory,
                "status": "started",
                "message": result["message"]
            })
        except Exception as e:
            results.append({
                "directory": directory,
                "status": "failed",
                "message": str(e)
            })

    return {
        "status": "success",
        "task_id": task_id,
        "results": results
    }


@router.post("/alist2strm/quick")
async def quick_strm_generation(
    request: QuickStrmRequest,
    _: bool = Depends(verify_api_key),
    task_manager=Depends(get_task_manager)
):
    """
    快速生成 STRM 文件（无需预先配置）

    直接提供 Alist 服务器信息和目录信息，立即生成 STRM 文件
    """
    try:
        config = request.dict()
        result = await task_manager.create_quick_strm(config)

        return {
            "status": result["status"],
            "message": result["message"],
            "result": result.get("result")
        }
    except Exception as e:
        logger.error(f"Quick STRM generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))