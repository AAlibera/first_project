#!/usr/bin/env python3
"""
PCB缺陷检测系统 - 日志管理模块

统一管理项目所有日志记录，支持多输出目标、日志轮转、结构化日志等功能。

设计原则:
    - 分层设计: 控制台输出简洁格式，文件输出完整格式
    - 日志轮转: 自动切割日志文件，避免占用过多磁盘空间
    - 结构化输出: 支持JSON格式，便于日志分析
    - 请求追踪: 支持请求ID追踪，便于问题定位
    - 可配置性: 通过配置文件灵活调整日志行为

使用示例:
    from app.utils.logging import get_logger
    
    logger = get_logger(__name__)
    
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误")
    
    # 使用请求上下文
    with logger.context(request_id="req-123"):
        logger.info("处理请求")
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from contextvars import ContextVar
import json
from copy import copy

from app.utils.paths import Paths

REQUEST_ID: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIDFilter(logging.Filter):
    """
    请求ID过滤器
    
    在日志记录中添加请求ID，便于追踪请求链路。
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        添加请求ID到日志记录
        
        Args:
            record: 日志记录对象
        
        Returns:
            bool: 是否允许记录
        """
        record.request_id = REQUEST_ID.get() or "N/A"
        return True


class JsonFormatter(logging.Formatter):
    """
    JSON格式日志格式化器
    
    将日志记录转换为JSON格式，便于日志收集和分析。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON字符串
        
        Args:
            record: 日志记录对象
        
        Returns:
            str: JSON格式的日志字符串
        """
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "N/A"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    带颜色的控制台日志格式化器
    
    根据日志级别显示不同颜色，提高可读性。
    """
    
    COLORS = {
        logging.DEBUG: "\033[94m",      # 蓝色
        logging.INFO: "\033[92m",       # 绿色
        logging.WARNING: "\033[93m",    # 黄色
        logging.ERROR: "\033[91m",      # 红色
        logging.CRITICAL: "\033[41m",   # 红色背景
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录，添加颜色
        
        Args:
            record: 日志记录对象
        
        Returns:
            str: 带颜色的日志字符串
        """
        color = self.COLORS.get(record.levelno, "")
        reset = self.RESET
        
        record.levelname = f"{color}{record.levelname}{reset}"
        record.name = f"{color}{record.name}{reset}"
        
        return super().format(record)


class LoggerWithContext:
    """
    带上下文的日志记录器
    
    支持通过上下文管理器添加请求ID等上下文信息。
    """
    
    def __init__(self, logger: logging.Logger):
        """
        初始化
        
        Args:
            logger: 基础日志记录器
        """
        self._logger = logger
    
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录DEBUG级别日志"""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录INFO级别日志"""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录WARNING级别日志"""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录ERROR级别日志"""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录CRITICAL级别日志"""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录异常信息"""
        self._logger.exception(msg, *args, **kwargs)
    
    def context(self, **kwargs: Any) -> "LogContext":
        """
        创建日志上下文管理器
        
        Args:
            **kwargs: 上下文参数
        
        Returns:
            LogContext: 上下文管理器
        """
        return LogContext(**kwargs)


class LogContext:
    """
    日志上下文管理器
    
    用于在特定上下文中添加请求ID等信息。
    """
    
    def __init__(self, **kwargs: Any):
        """
        初始化
        
        Args:
            **kwargs: 上下文参数，如 request_id
        """
        self._kwargs = kwargs
        self._previous_values: Dict[str, Any] = {}
    
    def __enter__(self) -> "LogContext":
        """进入上下文"""
        if "request_id" in self._kwargs:
            self._previous_values["request_id"] = REQUEST_ID.get()
            REQUEST_ID.set(self._kwargs["request_id"])
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文"""
        if "request_id" in self._previous_values:
            REQUEST_ID.set(self._previous_values["request_id"])


def get_logger(name: str) -> LoggerWithContext:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，通常使用 __name__
    
    Returns:
        LoggerWithContext: 带上下文的日志记录器
    """
    return LoggerWithContext(logging.getLogger(name))


def configure_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 10,
    enable_json: bool = False,
) -> None:
    """
    配置日志系统
    
    配置控制台和文件输出，支持日志轮转和结构化输出。
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录，默认使用 Paths.logs()
        max_file_size: 单个日志文件最大大小（字节），默认10MB
        backup_count: 保留的日志文件数量，默认10个
        enable_json: 是否启用JSON格式输出
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    
    root_logger.handlers.clear()
    
    if log_dir is None:
        log_dir = Paths.logs()
    Paths.ensure_dir(log_dir)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level.upper())
    
    console_format = (
        "%(asctime)s | %(request_id)s | %(levelname)s | %(name)s | %(message)s"
    )
    
    if enable_json:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter(console_format))
    
    console_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(console_handler)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level.upper())
    
    file_format = (
        "%(asctime)s | %(request_id)s | %(levelname)s | %(name)s | "
        "%(module)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    
    if enable_json:
        file_handler.setFormatter(JsonFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(file_format))
    
    file_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(file_handler)
    
    error_file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.error.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    
    if enable_json:
        error_file_handler.setFormatter(JsonFormatter())
    else:
        error_file_handler.setFormatter(logging.Formatter(file_format))
    
    error_file_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(error_file_handler)
    
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def set_request_id(request_id: str) -> None:
    """
    设置当前请求ID
    
    Args:
        request_id: 请求唯一标识
    """
    REQUEST_ID.set(request_id)


def get_request_id() -> Optional[str]:
    """
    获取当前请求ID
    
    Returns:
        Optional[str]: 当前请求ID
    """
    return REQUEST_ID.get()


def clear_request_id() -> None:
    """清除当前请求ID"""
    REQUEST_ID.set(None)


class LogMetrics:
    """
    日志指标收集器
    
    用于收集日志相关的统计信息。
    """
    
    def __init__(self):
        """初始化指标收集器"""
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, list] = {}
    
    def increment(self, name: str, value: int = 1) -> None:
        """
        增加计数器
        
        Args:
            name: 计数器名称
            value: 增加的值
        """
        self._counters[name] = self._counters.get(name, 0) + value
    
    def record_time(self, name: str, duration: float) -> None:
        """
        记录耗时
        
        Args:
            name: 计时器名称
            duration: 耗时（秒）
        """
        if name not in self._timers:
            self._timers[name] = []
        self._timers[name].append(duration)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "counters": copy(self._counters),
            "timers": {},
        }
        
        for name, values in self._timers.items():
            if values:
                stats["timers"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
        
        return stats
    
    def reset(self) -> None:
        """重置所有指标"""
        self._counters.clear()
        self._timers.clear()


log_metrics = LogMetrics()
