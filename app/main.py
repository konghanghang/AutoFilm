from asyncio import get_event_loop, create_task
from sys import path
from os.path import dirname
from threading import Thread

path.append(dirname(dirname(__file__)))

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type:ignore
from apscheduler.triggers.cron import CronTrigger  # type:ignore

from app.core import settings, logger
from app.extensions import LOGO
from app.modules import Alist2Strm, Ani2Alist, LibraryPoster

# 全局 scheduler 实例，可被 API 访问
scheduler = AsyncIOScheduler()


def print_logo() -> None:
    """
    打印 Logo
    """

    print(LOGO)
    print(f" {settings.APP_NAME} {settings.APP_VERSION} ".center(65, "="))
    print("")


async def run_api_server():
    """
    运行 API 服务器
    """
    import uvicorn
    from app.api.server import app

    api_config = settings.APIConfig
    if not api_config.get("enabled", True):
        logger.info("API 功能未启用")
        return

    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8080)

    logger.info(f"启动 API 服务器: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/api/docs")

    config = uvicorn.Config(
        "app.api.server:app",
        host=host,
        port=port,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=settings.DEBUG
    )
    server = uvicorn.Server(config)
    await server.serve()


def setup_scheduler():
    """
    设置定时任务
    """
    # 初始化任务管理器（必须在这里导入，确保循环引用正常）
    from app.core.task_manager import task_manager

    if settings.AlistServerList:
        logger.info("检测到 Alist2Strm 模块配置，正在添加至后台任务")
        for server in settings.AlistServerList:
            cron = server.get("cron")
            if cron:
                # 创建任务实例并添加到调度器
                task_instance = Alist2Strm(**server)
                scheduler.add_job(
                    task_instance.run,
                    trigger=CronTrigger.from_crontab(cron),
                    id=f"alist2strm_{server.get('id', '')}"
                )
                logger.info(f"{server['id']} 已被添加至后台任务")
            else:
                logger.warning(f"{server['id']} 未设置 cron")
    else:
        logger.warning("未检测到 Alist2Strm 模块配置")

    if settings.Ani2AlistList:
        logger.info("检测到 Ani2Alist 模块配置，正在添加至后台任务")
        for server in settings.Ani2AlistList:
            cron = server.get("cron")
            if cron:
                task_instance = Ani2Alist(**server)
                scheduler.add_job(
                    task_instance.run,
                    trigger=CronTrigger.from_crontab(cron),
                    id=f"ani2alist_{server.get('id', '')}"
                )
                logger.info(f"{server['id']} 已被添加至后台任务")
            else:
                logger.warning(f"{server['id']} 未设置 cron")
    else:
        logger.warning("未检测到 Ani2Alist 模块配置")

    if settings.LibraryPosterList:
        logger.info("检测到 LibraryPoster 模块配置，正在添加至后台任务")
        for poster in settings.LibraryPosterList:
            cron = poster.get("cron")
            if cron:
                task_instance = LibraryPoster(**poster)
                scheduler.add_job(
                    task_instance.run,
                    trigger=CronTrigger.from_crontab(cron),
                    id=f"libraryposter_{poster.get('id', '')}"
                )
                logger.info(f"{poster['id']} 已被添加至后台任务")
            else:
                logger.warning(f"{poster['id']} 未设置 cron")
    else:
        logger.warning("未检测到 LibraryPoster 模块配置")


async def main():
    """
    主函数
    """
    print_logo()

    logger.info(f"AutoFilm {settings.APP_VERSION} 启动中...")
    logger.debug(f"是否开启 DEBUG 模式: {settings.DEBUG}")

    # 设置定时任务
    setup_scheduler()
    scheduler.start()
    logger.info("AutoFilm 定时任务启动完成")

    # 启动 API 服务器（如果启用）
    if settings.APIConfig.get("enabled", True):
        # 在同一个事件循环中运行 API
        api_task = create_task(run_api_server())
        logger.info("AutoFilm API 服务启动完成")


if __name__ == "__main__":
    try:
        loop = get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("AutoFilm 程序退出！")