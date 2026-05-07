"""统一日志模块

提供 get_logger(name) 工厂函数，所有模块统一使用。
日志同时输出到控制台（INFO）和文件（DEBUG）。
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


_initialized = False


def _setup():
    """初始化根 logger 配置（只执行一次）"""
    global _initialized
    if _initialized:
        return

    # 日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 根 logger
    root = logging.getLogger("qa_agent")
    root.setLevel(logging.DEBUG)

    # 防止重复添加 handler
    if root.handlers:
        _initialized = True
        return

    # 控制台 handler — INFO 级别，简洁格式
    console = StreamHandlerWithColor()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(console)

    # 文件 handler — DEBUG 级别，详细格式
    log_file = os.path.join(log_dir, f"qa_agent_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例

    Args:
        name: 模块名称，如 "router"、"analyze"
    Returns:
        Logger 实例
    """
    _setup()
    return logging.getLogger(f"qa_agent.{name}")


class StreamHandlerWithColor(logging.StreamHandler):
    """控制台 handler，带简单的级别颜色标记"""
    LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",     # 青色
        logging.INFO: "\033[32m",      # 绿色
        logging.WARNING: "\033[33m",   # 黄色
        logging.ERROR: "\033[31m",     # 红色
        logging.CRITICAL: "\033[1;31m", # 粗红
    }
    RESET = "\033[0m"

    def format(self, record):
        text = super().format(record)
        color = self.LEVEL_COLORS.get(record.levelno, "")
        if color:
            text = f"{color}{text}{self.RESET}"
        return text
