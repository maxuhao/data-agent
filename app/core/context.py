"""
异步上下文变量模块

本模块定义用于在异步环境中传递请求级数据的 ContextVar。

功能说明：
1. 定义 request_id_context_var 用于存储当前请求的唯一标识
2. 在异步任务间传递上下文，避免显式参数传递
3. 支持日志追踪、错误定位等场景

什么是 ContextVar：
- Python 3.7+ 引入的上下文变量（类似线程本地存储）
- 每个异步任务有独立的变量副本
- 自动继承：asyncio.create_task() 会携带上下文
- 线程安全：不同线程互不干扰

为什么需要 request_id：
- 请求追踪：为每个用户请求分配唯一 ID
- 日志关联：同一请求的所有日志都包含相同 request_id
- 问题定位：可以通过 request_id 串联完整调用链
- 调试友好：并发环境下区分不同请求的日志

使用场景：
1. 日志记录：每条日志自动包含 request_id
2. 错误上报：Sentry 等错误追踪系统携带 request_id
3. 性能分析：统计特定请求的处理耗时
4. 审计日志：记录关键操作的执行者

使用方法：
    from app.core.context import request_id_context_var
    
    # 设置 request_id (通常在中间件中)
    request_id = generate_request_id()
    request_id_context_var.set(request_id)
    
    # 获取 request_id (在任何地方)
    current_request_id = request_id_context_var.get()
    logger.info(f"处理请求 {current_request_id}")
    
    # 异步环境中自动继承
    async def sub_task():
        # 不需要显式传递，可以直接获取
        request_id = request_id_context_var.get()
"""
from sentry_sdk.utils import ContextVar

request_id_context_var: ContextVar[str] = ContextVar('request_id', default='1')
