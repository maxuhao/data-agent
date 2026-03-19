"""智能问数系统主入口模块

本模块是 FastAPI 应用的启动入口，负责：
- 创建 FastAPI 应用实例并配置生命周期管理
- 注册 API 路由（查询路由器）
- 添加 HTTP 中间件用于生成和传递 request_id
- 实现请求追踪链路，便于日志记录和调试

主要功能:
    1. 初始化 FastAPI 应用，配置 lifespan 管理数据库连接等资源
    2. 注册 query_router 处理用户查询请求
    3. 通过中间件为每个请求生成唯一的 UUID 作为 request_id
    4. 使用 contextvar 在异步上下文中传递 request_id，确保日志追踪的完整性

示例:
    启动应用:
        >>> fastapi dev main.py
        或
        >>> uvicorn main:app --reload

依赖项:
    - FastAPI: Web 框架
    - uuid: 生成唯一请求 ID
    - app.api.lifespan: 应用生命周期管理
    - app.api.routers.query_router: 查询 API 路由
    - app.core.context: 请求上下文变量管理

作者：智能问数团队
版本：1.0.0
"""
import uuid

from fastapi import FastAPI, Request

from app.api.lifespan import lifespan
from app.api.routers.query_router import query_router
from app.core.context import request_id_context_var

# 创建 FastAPI 应用实例，配置 lifespan 进行资源管理（数据库连接、向量库客户端等）
app = FastAPI(lifespan=lifespan)

# 注册查询路由器，包含所有与用户查询相关的 API 端点
app.include_router(query_router)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """HTTP 请求中间件：为每个请求生成并注入唯一的 request_id
    
    该中间件在请求处理前生成 UUID 作为请求 ID，并通过 contextvar 设置到当前
    异步上下文中，使得整个请求链路中的所有日志记录都可以携带该 request_id，
    便于问题追踪和调试。
    
    工作流程:
        1. 接收 HTTP 请求
        2. 生成唯一的 UUID 作为 request_id
        3. 将 request_id 设置到 contextvar 中（线程安全）
        4. 调用后续处理链（包括路由、业务逻辑等）
        5. 返回响应（request_id 在整个处理过程中可用）
    
    Args:
        request (Request): FastAPI 请求对象，包含请求的所有信息
        call_next (Callable): 下一个中间件或路由处理函数
    
    Returns:
        Response: 处理后的 HTTP 响应对象
    
    注意:
        - request_id 通过 contextvar 在异步上下文中传递，避免显式参数传递
        - 每个请求都有独立的 request_id，即使在高并发场景下也不会冲突
        - 日志系统会自动从 contextvar 读取 request_id 并记录到日志中
    """
    # 请求被处理之前：生成唯一的请求 ID
    request_id = uuid.uuid4()
    # 将 request_id 设置到当前异步上下文中，供后续业务逻辑和日志系统使用
    request_id_context_var.set(request_id)
    # 调用后续处理链（其他中间件、路由处理器等）
    response = await call_next(request)
    # 请求被处理之后：返回响应（此时 request_id 仍然可在日志中使用）
    return response
