"""
日志配置模块

本模块使用 Loguru 配置统一的日志系统，支持请求 ID 追踪和灵活的输出策略。

功能说明：
1. 配置日志格式：时间、级别、request_id、模块信息、消息
2. 支持双路输出：控制台 + 文件
3. 集成 request_id 实现分布式追踪
4. 自动日志轮转和过期清理

技术栈：
- Loguru: 现代化 Python 日志库（无需手动 getLogger）
- asyncio contextvars: 异步环境下的请求上下文
- 彩色终端输出：不同级别不同颜色，便于调试

日志格式说明：
    2026-03-15 10:30:45.123 | INFO     | request_id - abc123 | app.agent.graph:build:42 - Generated SQL
    └────日期时间────┘   └─级别─┘   └──请求 ID──┘ └─────────模块位置─────────┘   └─消息─┘

为什么需要 request_id：
- 并发请求追踪：多个请求同时处理时区分日志
- 问题定位：通过 request_id 串联单个请求的完整流程
- 调试友好：可以过滤特定请求的所有日志

输出配置：
1. 控制台输出：
   - sink: sys.stdout
   - 彩色显示：INFO(绿), ERROR(红), WARNING(黄)
   - 开发调试用

2. 文件输出：
   - sink: logs/app.log
   - rotation: "00:00" (每天轮转)
   - retention: "7 days" (保留 7 天)
   - encoding: utf-8 (支持中文)
   - 生产归档用

使用方法：
    from app.core.log import logger
    
    # 记录日志
    logger.info("操作成功")
    logger.error(f"操作失败：{error}")
    logger.debug(f"详细参数：{params}")
    
    # 在异步环境中自动携带 request_id
    async def handle_request():
        request_id_context_var.set("req-123")
        logger.info("开始处理请求")  # 会自动包含 request_id
"""
import asyncio
import sys
from pathlib import Path

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import request_id_context_var

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 注入request_id到日志记录中
def inject_request_id(record):
    request_id = request_id_context_var.get()
    record["extra"]["request_id"] = request_id

logger.remove()

# 给日志打补丁，使其支持注入request_id
logger = logger.patch(inject_request_id)
if app_config.logging.console.enable:
    logger.add(sink=sys.stdout, level=app_config.logging.console.level, format=log_format)
if app_config.logging.file.enable:
    path = Path(app_config.logging.file.path)
    path.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=path / "app.log",
        level=app_config.logging.file.level,
        format=log_format,
        rotation=app_config.logging.file.rotation,
        retention=app_config.logging.file.retention,
        encoding="utf-8"
    )
