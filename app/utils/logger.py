"""统一日志配置模块"""
import logging
import sys

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

# 添加处理器
if not logger.handlers:
    logger.addHandler(handler)
    

