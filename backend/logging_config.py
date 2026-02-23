"""
日志统一配置模块
- 控制台 + 文件双输出
- 文件按天切分，保留 14 天，UTF-8 编码
- 调用方：在 main.py 最顶部 `import logging_config` 即可
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from config import settings

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# 第三方库噪音日志降级
_QUIET_LOGGERS = {
    "httpcore": logging.WARNING,
    "httpx": logging.WARNING,
    "openai": logging.INFO,
    "uvicorn.access": logging.INFO,
}


def setup() -> None:
    log_level = logging.getLevelName(settings.log_level.upper())
    log_file = os.path.join(settings.log_dir, "app.log")

    os.makedirs(settings.log_dir, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",       # 每天零点切分
        interval=1,
        backupCount=14,        # 保留 14 天
        encoding="utf-8",
        utc=False,
    )
    file_handler.suffix = "%Y-%m-%d"

    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    # 避免重复添加（uvicorn reload 时会多次调用）
    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    # 把 uvicorn 自带的 handler 清掉，走根 logger
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx", "openai"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # 降低第三方库日志级别
    for name, level in _QUIET_LOGGERS.items():
        logging.getLogger(name).setLevel(level)
