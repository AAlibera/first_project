"""
PCB缺陷检测系统 - 模型管理服务

负责模型的加载、卸载、切换和管理。
采用路径管理模块确保路径配置的可移植性。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from app.utils.paths import Paths
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ModelStatus(Enum):
    """模型状态枚举"""
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"
    UNLOADED = "unloaded"


@dataclass
class ModelInfo:
    """
    模型信息数据类
    
    存储单个模型的元数据信息。
    
    Attributes:
        name: 模型名称
        path: 模型文件路径
        version: 模型版本
        status: 模型状态
        description: 模型描述
        created_at: 创建时间
        metrics: 模型性能指标
        config: 模型配置
        last_used: 最后使用时间
        class_names: 类别名称列表
    """
    name: str
    path: str
    version: str
    status: ModelStatus
    description: str = ""
    created_at: str = ""
    metrics: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    last_used: Optional[str] = None
    class_names: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            **asdict(self),
            'status': self.status.value,
            'metrics': self.metrics or {},
            'config': self.config or {}
        }


class ModelManager:
    """
    模型管理器
    
    负责管理所有 AI 模型的生命周期，包括扫描、注册、切换、删除等操作。
    使用路径管理模块统一管理所有路径。
    
    Attributes:
        SUPPORTED_EXTENSIONS: 支持的模型文件扩展名
        DEFAULT_CLASS_NAMES: 默认的缺陷类别名称
    """
    
    SUPPORTED_EXTENSIONS: set = {'.pt', '.pth', '.onnx', '.h5'}
    DEFAULT_CLASS_NAMES: List[str] = [
        "scratch",
        "crack",
        "hole",
        "deformation",
        "missing",
        "solder"
    ]

    def __init__(self, models_dir: Optional[Path] = None):
        """
        初始化模型管理器
        
        Args:
            models_dir: 模型文件夹路径，默认使用 Paths.models()
        """
        self._models_dir = models_dir
        self._models_cache: Dict[str, Any] = {}
        self._models_info: Dict[str, ModelInfo] = {}
        self._current_model_name: Optional[str] = None
        
        self._init_models_dir()
        self._load_models_info()
        
        logger.info(f"模型管理器初始化完成，模型目录: {self.models_dir}")

    @property
    def models_dir(self) -> Path:
        """获取模型目录，确保目录存在"""
        if self._models_dir is None:
            self._models_dir = Paths.models()
        Paths.ensure_dir(self._models_dir)
        return self._models_dir

    @property
    def config_file(self) -> Path:
        """获取配置文件路径"""
        return self.models_dir / "models_config.json"

    def _init_models_dir(self) -> None:
        """初始化模型目录"""
        Paths.ensure_dir(self.models_dir)
        cache_dir = self.models_dir / ".cache"
        Paths.ensure_dir(cache_dir)

    def _load_models_info(self) -> None:
        """加载模型信息"""
        if not self.config_file.exists():
            logger.debug("模型配置文件不存在，将创建新配置")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            for name, info in config.items():
                info['status'] = ModelStatus(info.get('status', 'unloaded'))
                self._models_info[name] = ModelInfo(**info)
                
            logger.info(f"已加载 {len(self._models_info)} 个模型的配置信息")
            
        except json.JSONDecodeError as e:
            logger.error(f"模型配置文件格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"加载模型配置失败: {str(e)}")

    def _save_models_info(self) -> None:
        """保存模型信息到配置文件"""
        try:
            config = {
                name: info.to_dict()
                for name, info in self._models_info.items()
            }
            
            Paths.ensure_dir(self.config_file.parent)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            logger.info("模型配置信息已保存")
            
        except Exception as e:
            logger.error(f"保存模型配置失败: {str(e)}")

    def scan_models(self) -> List[ModelInfo]:
        """
        扫描模型文件夹，获取所有可用模型
        
        Returns:
            List[ModelInfo]: 可用模型列表
        """
        available_models = []
        
        for model_file in self.models_dir.iterdir():
            if not model_file.is_file():
                continue
                
            if model_file.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            
            model_name = model_file.stem
            
            if model_name not in self._models_info:
                relative_path = Paths.get_relative_path(model_file)
                model_info = ModelInfo(
                    name=model_name,
                    path=str(relative_path),
                    version="1.0.0",
                    status=ModelStatus.UNLOADED,
                    description=f"模型文件: {model_file.name}",
                    created_at=datetime.now().isoformat(),
                    class_names=self.DEFAULT_CLASS_NAMES.copy()
                )
                self._models_info[model_name] = model_info
            
            available_models.append(self._models_info[model_name])
        
        if available_models:
            self._save_models_info()
        
        logger.info(f"扫描到 {len(available_models)} 个可用模型")
        return available_models

    def register_model(
        self,
        name: str,
        path: str,
        version: str = "1.0.0",
        description: str = "",
        class_names: Optional[List[str]] = None
    ) -> ModelInfo:
        """
        注册新模型
        
        Args:
            name: 模型名称
            path: 模型文件路径
            version: 模型版本
            description: 模型描述
            class_names: 类别名称列表
        
        Returns:
            ModelInfo: 注册的模型信息
        
        Raises:
            ValueError: 模型名称已存在
        """
        if name in self._models_info:
            logger.warning(f"模型名称已存在，将更新: {name}")
        
        model_info = ModelInfo(
            name=name,
            path=path,
            version=version,
            status=ModelStatus.UNLOADED,
            description=description,
            created_at=datetime.now().isoformat(),
            class_names=class_names or self.DEFAULT_CLASS_NAMES.copy()
        )
        
        self._models_info[name] = model_info
        self._save_models_info()
        
        logger.info(f"模型注册成功: {name}")
        return model_info

    def get_model(self, name: str) -> Optional[ModelInfo]:
        """
        获取模型信息
        
        Args:
            name: 模型名称
        
        Returns:
            Optional[ModelInfo]: 模型信息，不存在则返回 None
        """
        return self._models_info.get(name)

    def get_current_model(self) -> Optional[ModelInfo]:
        """
        获取当前使用的模型
        
        Returns:
            Optional[ModelInfo]: 当前模型信息
        """
        if self._current_model_name:
            return self._models_info.get(self._current_model_name)
        return None

    def set_current_model(self, name: str) -> bool:
        """
        设置当前使用的模型
        
        Args:
            name: 模型名称
        
        Returns:
            bool: 是否设置成功
        """
        if name not in self._models_info:
            logger.error(f"模型不存在: {name}")
            return False
        
        self._current_model_name = name
        model_info = self._models_info[name]
        model_info.last_used = datetime.now().isoformat()
        self._save_models_info()
        
        logger.info(f"当前模型已切换为: {name}")
        return True

    def list_models(self) -> List[ModelInfo]:
        """
        列出所有注册的模型
        
        Returns:
            List[ModelInfo]: 模型信息列表
        """
        return list(self._models_info.values())

    def update_model_info(self, name: str, **kwargs) -> bool:
        """
        更新模型信息
        
        Args:
            name: 模型名称
            **kwargs: 要更新的字段
        
        Returns:
            bool: 是否更新成功
        """
        if name not in self._models_info:
            logger.error(f"模型不存在: {name}")
            return False
        
        model_info = self._models_info[name]
        
        for key, value in kwargs.items():
            if hasattr(model_info, key):
                setattr(model_info, key, value)
        
        self._save_models_info()
        logger.info(f"模型信息已更新: {name}")
        return True

    def delete_model(self, name: str) -> bool:
        """
        删除模型
        
        Args:
            name: 模型名称
        
        Returns:
            bool: 是否删除成功
        """
        if name not in self._models_info:
            logger.error(f"模型不存在: {name}")
            return False
        
        if name in self._models_cache:
            del self._models_cache[name]
        
        model_info = self._models_info[name]
        model_path = Path(model_info.path)
        
        if model_path.exists():
            try:
                model_path.unlink()
                logger.info(f"模型文件已删除: {model_path}")
            except Exception as e:
                logger.error(f"删除模型文件失败: {str(e)}")
        
        del self._models_info[name]
        self._save_models_info()
        
        if self._current_model_name == name:
            self._current_model_name = None
        
        logger.info(f"模型已删除: {name}")
        return True

    def get_cache_path(self, name: str) -> Optional[Path]:
        """
        获取模型的缓存路径
        
        Args:
            name: 模型名称
        
        Returns:
            Optional[Path]: 缓存路径
        """
        if name not in self._models_info:
            return None
        
        cache_dir = self.models_dir / ".cache" / name
        Paths.ensure_dir(cache_dir)
        return cache_dir

    def model_exists(self, name: str) -> bool:
        """
        检查模型是否存在
        
        Args:
            name: 模型名称
        
        Returns:
            bool: 模型是否存在
        """
        return name in self._models_info

    def get_model_path(self, name: str) -> Optional[Path]:
        """
        获取模型文件路径
        
        Args:
            name: 模型名称
        
        Returns:
            Optional[Path]: 模型文件路径
        """
        model_info = self.get_model(name)
        if model_info:
            return Path(model_info.path)
        return None


model_manager = ModelManager()
