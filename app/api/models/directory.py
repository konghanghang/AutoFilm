from pydantic import BaseModel
from typing import Optional, List


class DirectoryTriggerRequest(BaseModel):
    """目录触发请求"""
    directory: str
    recursive: bool = True
    sync_mode: Optional[bool] = None
    overwrite: bool = False


class DirectoriesTriggerRequest(BaseModel):
    """批量目录触发请求"""
    directories: List[str]
    recursive: bool = True
    sync_mode: Optional[bool] = None
    overwrite: bool = False


class QuickStrmRequest(BaseModel):
    """快速 STRM 生成请求（无需预配置）"""
    alist_url: str
    username: str
    password: str
    token: str = ""
    source_dir: str
    target_dir: str
    mode: str = "AlistURL"
    flatten_mode: bool = False
    subtitle: bool = False
    image: bool = False
    nfo: bool = False
    other_ext: str = ""
    max_workers: int = 50
    max_downloaders: int = 5
    wait_time: float = 0
    sync_server: bool = False
    sync_ignore: Optional[str] = None