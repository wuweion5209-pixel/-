"""统一日志配置模块"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 配置日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 创建日志处理器
logger = logging.getLogger("ai_agent")
logger.setLevel(logging.INFO)

# 创建控制台处理器
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# 设置格式
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
handler.setFormatter(formatter)

# 文件处理器（最大 5MB，保留 3 个备份）
file_handler = RotatingFileHandler(
    LOG_DIR / "app.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# 添加处理器
if not logger.handlers:
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    

