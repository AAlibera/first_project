#!/usr/bin/env python3
"""
PCB缺陷检测系统 - 路径管理模块

统一管理项目所有路径，支持从任意子模块定位项目根目录。
采用 Marker File 模式，确保路径配置的可移植性和可维护性。

使用示例:
    from app.utils.paths import Paths
    
    # 获取项目根目录
    root = Paths.root()
    
    # 获取模型目录
    models_dir = Paths.models()
    
    # 获取静态文件目录
    static_dir = Paths.static()
    
    # 确保目录存在
    Paths.ensure_dir(Paths.results())
"""

from pathlib import Path
from typing import Optional, List
import inspect
import logging

logger = logging.getLogger(__name__)


def find_project_root(
    start_path: Optional[Path] = None, 
    marker_file: str = ".pcb_platform"
) -> Path:
    """
    从当前位置向上查找项目根目录（通过查找 marker file）
    
    核心算法:
        1. 从当前文件所在目录开始
        2. 逐级向上遍历父目录
        3. 找到 marker file 则停止，返回该目录
    
    Args:
        start_path: 起始查找路径，默认为调用此函数的文件所在目录
        marker_file: marker 文件名，用于标识项目根目录
    
    Returns:
        Path: 项目根目录路径
    
    Raises:
        FileNotFoundError: 找不到 marker file
    
    Example:
        # 从 backend/app/services/deep/module.py 调用
        # 会向上查找: app/ -> backend/ -> 项目根目录（找到 .pcb_platform）
        root = find_project_root()
    """
    if start_path is None:
        frame = inspect.stack()[1]
        start_path = Path(frame.filename).parent
    
    current = Path(start_path).resolve()
    
    for parent in [current] + list(current.parents):
        marker_path = parent / marker_file
        if marker_path.exists():
            return parent
    
    raise FileNotFoundError(
        f"Could not find {marker_file} in {current} or any parent directory. "
        f"Please ensure the marker file exists in the project root."
    )


class Paths:
    """
    项目路径管理类
    
    所有路径统一在此定义，避免硬编码。采用懒加载模式，
    第一次访问时才计算并缓存根目录路径。
    
    设计原则:
        - 单一职责: 只负责路径管理
        - 懒加载: 首次使用时才初始化
        - 缓存: 避免重复查找
        - 跨平台: 使用 pathlib 处理路径分隔符
    
    Attributes:
        _root: 缓存的项目根目录
        _initialized: 是否已初始化
    """
    
    _root: Optional[Path] = None
    _initialized: bool = False
    
    @classmethod
    def root(cls) -> Path:
        """
        获取项目根目录（first_project 目录）
        
        通过查找 .pcb_platform marker file 定位项目根目录。
        
        Returns:
            Path: 项目根目录路径（first_project/）
        """
        if cls._root is None:
            cls._root = find_project_root()
            cls._initialized = True
            logger.debug(f"Project root initialized: {cls._root}")
        return cls._root
    
    @classmethod
    def backend(cls) -> Path:
        """
        获取 backend 目录
        
        Returns:
            Path: backend 目录路径（first_project/backend/）
        """
        return cls.root() / "backend"
    
    @classmethod
    def app(cls) -> Path:
        """
        获取 app 目录
        
        Returns:
            Path: app 目录路径
        """
        return cls.backend() / "app"
    
    @classmethod
    def static(cls) -> Path:
        """
        获取静态文件目录
        
        Returns:
            Path: static 目录路径
        """
        return cls.backend() / "static"
    
    @classmethod
    def uploads(cls) -> Path:
        """
        获取上传文件目录
        
        Returns:
            Path: uploads 目录路径
        """
        return cls.static() / "uploads"
    
    @classmethod
    def results(cls) -> Path:
        """
        获取检测结果输出目录
        
        Returns:
            Path: results 目录路径
        """
        return cls.static() / "results"
    
    @classmethod
    def models(cls) -> Path:
        """
        获取模型文件目录
        
        Returns:
            Path: models 目录路径
        """
        return cls.backend() / "models"
    
    @classmethod
    def logs(cls) -> Path:
        """
        获取日志文件目录
        
        Returns:
            Path: logs 目录路径
        """
        return cls.backend() / "logs"
    
    @classmethod
    def data(cls) -> Path:
        """
        获取数据目录
        
        Returns:
            Path: data 目录路径
        """
        return cls.backend() / "data"
    
    @classmethod
    def config(cls) -> Path:
        """
        获取配置文件目录
        
        Returns:
            Path: 配置文件目录路径
        """
        return cls.backend()
    
    @classmethod
    def ensure_dir(cls, path: Path) -> Path:
        """
        确保目录存在，不存在则创建
        
        Args:
            path: 目录路径
        
        Returns:
            Path: 确保存在的目录路径
        
        Example:
            output_dir = Paths.ensure_dir(Paths.results() / "batch_001")
        """
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        return path
    
    @classmethod
    def init_all_dirs(cls) -> List[Path]:
        """
        初始化所有必要的目录结构
        
        创建项目运行所需的所有目录，适用于首次部署或环境初始化。
        
        Returns:
            List[Path]: 创建的目录列表
        """
        dirs_to_create = [
            cls.static(),
            cls.uploads(),
            cls.results(),
            cls.models(),
            cls.logs(),
            cls.data(),
        ]
        
        created_dirs = []
        for dir_path in dirs_to_create:
            if not dir_path.exists():
                cls.ensure_dir(dir_path)
                created_dirs.append(dir_path)
                logger.info(f"Initialized directory: {dir_path}")
        
        if created_dirs:
            logger.info(f"Initialized {len(created_dirs)} directories")
        else:
            logger.debug("All directories already exist")
        
        return created_dirs
    
    @classmethod
    def get_relative_path(cls, absolute_path: Path) -> Path:
        """
        将绝对路径转换为相对于项目根目录的相对路径
        
        Args:
            absolute_path: 绝对路径
        
        Returns:
            Path: 相对路径
        
        Example:
            abs_path = Paths.models() / "best.pt"
            rel_path = Paths.get_relative_path(abs_path)
            # rel_path = Path("models/best.pt")
        """
        try:
            return absolute_path.relative_to(cls.root())
        except ValueError:
            return absolute_path
    
    @classmethod
    def validate_path(cls, path: Path, must_exist: bool = True) -> bool:
        """
        验证路径是否有效
        
        Args:
            path: 要验证的路径
            must_exist: 是否必须存在
        
        Returns:
            bool: 路径是否有效
        """
        if must_exist and not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return False
        
        if not path.is_absolute():
            logger.warning(f"Path is not absolute: {path}")
            return False
        
        return True
    
    @classmethod
    def reset(cls) -> None:
        """
        重置缓存的路径（主要用于测试）
        
        清除缓存的根目录，下次访问时会重新查找。
        """
        cls._root = None
        cls._initialized = False
        logger.debug("Paths cache reset")


def get_project_root() -> Path:
    """
    便捷函数：获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    return Paths.root()


def ensure_directory(path: Path) -> Path:
    """
    便捷函数：确保目录存在
    
    Args:
        path: 目录路径
    
    Returns:
        Path: 确保存在的目录路径
    """
    return Paths.ensure_dir(path)
