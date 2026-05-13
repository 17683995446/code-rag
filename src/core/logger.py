"""
产品级日志系统 - 无依赖版本
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from .settings import get_settings


def setup_logging():
    """配置日志系统"""
    settings = get_settings()
    
    log_level = getattr(logging, settings.logging.level, logging.INFO)
    
    # 配置根logger
    logger = logging.getLogger("code_rag")
    logger.setLevel(log_level)
    
    # 清除已有的handlers
    logger.handlers = []
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(settings.logging.format)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果配置了）
    if settings.logging.file:
        try:
            file_path = Path(settings.logging.file)
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法配置文件日志: {e}")
    
    return logger


# 获取logger的便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取logger"""
    return logging.getLogger(f"code_rag.{name}")


# 主logger
_logger: Optional[logging.Logger] = None


def get_root_logger() -> logging.Logger:
    """获取根logger"""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


@contextmanager
def log_context(operation: str):
    """日志上下文管理器"""
    logger = get_root_logger()
    logger.info(f"开始: {operation}")
    try:
        yield
        logger.info(f"完成: {operation}")
    except Exception as e:
        logger.error(f"失败: {operation} - {e}", exc_info=True)
        raise
