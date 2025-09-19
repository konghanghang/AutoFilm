from typing import Dict, Any, Optional, List
from datetime import datetime
from asyncio import create_task, Task as AsyncTask
from enum import Enum

from app.core import settings, logger
from app.modules import Alist2Strm, Ani2Alist, LibraryPoster
from app.api.models.task import TaskStatus, TaskInfo


class TaskType(str, Enum):
    ALIST2STRM = "alist2strm"
    ANI2ALIST = "ani2alist"
    LIBRARYPOSTER = "libraryposter"


class TaskManager:
    """
    任务管理器，管理所有任务实例和执行状态
    """

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running_tasks: Dict[str, AsyncTask] = {}
        self.task_history: List[Dict[str, Any]] = []
        self._initialize_tasks()

    def _initialize_tasks(self):
        """初始化配置文件中的任务"""
        # 初始化 Alist2Strm 任务
        for config in settings.AlistServerList:
            task_id = config.get("id", f"alist2strm_{len(self.tasks)}")
            self.tasks[task_id] = {
                "type": TaskType.ALIST2STRM,
                "config": config,
                "status": TaskStatus.IDLE,
                "last_run": None,
                "instance": None
            }

        # 初始化 Ani2Alist 任务
        for config in settings.Ani2AlistList:
            task_id = config.get("id", f"ani2alist_{len(self.tasks)}")
            self.tasks[task_id] = {
                "type": TaskType.ANI2ALIST,
                "config": config,
                "status": TaskStatus.IDLE,
                "last_run": None,
                "instance": None
            }

        # 初始化 LibraryPoster 任务
        for config in settings.LibraryPosterList:
            task_id = config.get("id", f"libraryposter_{len(self.tasks)}")
            self.tasks[task_id] = {
                "type": TaskType.LIBRARYPOSTER,
                "config": config,
                "status": TaskStatus.IDLE,
                "last_run": None,
                "instance": None
            }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """获取所有任务信息"""
        result = {}
        for task_id, task in self.tasks.items():
            result[task_id] = TaskInfo(
                task_id=task_id,
                task_type=task["type"],
                description=task["config"].get("id", task_id),
                cron=task["config"].get("cron"),
                status=task["status"],
                last_run=task["last_run"].isoformat() if task["last_run"] else None,
                next_run=None,  # TODO: 从 scheduler 获取下次运行时间
                config=task["config"]
            )
        return result

    def create_task_instance(self, task_type: TaskType, config: Dict[str, Any]):
        """创建任务实例"""
        if task_type == TaskType.ALIST2STRM:
            return Alist2Strm(**config)
        elif task_type == TaskType.ANI2ALIST:
            return Ani2Alist(**config)
        elif task_type == TaskType.LIBRARYPOSTER:
            return LibraryPoster(**config)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def trigger_task(self, task_id: str, override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """触发任务执行"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task["status"] == TaskStatus.RUNNING:
            return {
                "status": "error",
                "message": f"Task {task_id} is already running"
            }

        # 合并配置
        config = {**task["config"]}
        if override_config:
            config.update(override_config)

        # 创建任务实例
        instance = self.create_task_instance(task["type"], config)
        task["instance"] = instance
        task["status"] = TaskStatus.RUNNING
        task["last_run"] = datetime.now()

        # 异步执行任务
        async_task = create_task(self._run_task(task_id, instance))
        self.running_tasks[task_id] = async_task

        return {
            "status": "started",
            "message": f"Task {task_id} started",
            "task_id": task_id,
            "started_at": task["last_run"].isoformat()
        }

    async def _run_task(self, task_id: str, instance):
        """执行任务并更新状态"""
        task = self.tasks[task_id]
        try:
            logger.info(f"Starting task {task_id}")
            result = await instance.run()

            task["status"] = TaskStatus.COMPLETED
            self.task_history.append({
                "task_id": task_id,
                "status": TaskStatus.COMPLETED,
                "started_at": task["last_run"],
                "completed_at": datetime.now(),
                "result": result
            })
            logger.info(f"Task {task_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            task["status"] = TaskStatus.FAILED
            self.task_history.append({
                "task_id": task_id,
                "status": TaskStatus.FAILED,
                "started_at": task["last_run"],
                "completed_at": datetime.now(),
                "error": str(e)
            })
            raise

        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            task["instance"] = None

    async def trigger_directory(self, task_id: str, directory: str, **kwargs) -> Dict[str, Any]:
        """触发指定目录的处理（仅适用于 Alist2Strm）"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task["type"] != TaskType.ALIST2STRM:
            raise ValueError(f"Task {task_id} is not an Alist2Strm task")

        if task["status"] == TaskStatus.RUNNING:
            return {
                "status": "error",
                "message": f"Task {task_id} is already running"
            }

        # 创建任务实例
        config = {**task["config"]}
        instance = Alist2Strm(**config)

        task["status"] = TaskStatus.RUNNING
        task["last_run"] = datetime.now()

        # 异步执行任务
        async_task = create_task(self._run_directory_task(task_id, instance, directory, **kwargs))
        self.running_tasks[task_id] = async_task

        return {
            "status": "started",
            "message": f"Processing directory {directory}",
            "task_id": task_id,
            "directory": directory,
            "started_at": task["last_run"].isoformat()
        }

    async def _run_directory_task(self, task_id: str, instance: Alist2Strm, directory: str, **kwargs):
        """执行目录级别的任务"""
        task = self.tasks[task_id]
        try:
            logger.info(f"Processing directory {directory} for task {task_id}")

            # 调用实例的目录处理方法
            sync_mode = kwargs.get("sync_mode")
            overwrite = kwargs.get("overwrite", False)

            # 临时覆盖实例配置
            if sync_mode is not None:
                original_sync = instance.sync_server
                instance.sync_server = sync_mode
            if overwrite:
                original_overwrite = instance.overwrite
                instance.overwrite = overwrite

            result = await instance.run(specific_dir=directory)

            # 恢复原始配置
            if sync_mode is not None:
                instance.sync_server = original_sync
            if overwrite:
                instance.overwrite = original_overwrite

            task["status"] = TaskStatus.COMPLETED
            logger.info(f"Directory {directory} processed successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to process directory {directory}: {str(e)}")
            task["status"] = TaskStatus.FAILED
            raise

        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def create_quick_strm(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """快速创建 STRM 文件（无需预配置）"""
        try:
            instance = Alist2Strm(**config)
            result = await instance.run()
            return {
                "status": "success",
                "message": "Quick STRM generation completed",
                "result": result
            }
        except Exception as e:
            logger.error(f"Quick STRM generation failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.get_task(task_id)
        return task["status"] if task else None

    def get_task_history(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务历史记录"""
        if task_id:
            history = [h for h in self.task_history if h["task_id"] == task_id]
        else:
            history = self.task_history

        return history[-limit:]


# 全局任务管理器实例
task_manager = TaskManager()