"""
查询 API 路由模块

本模块定义智能问数系统的核心查询接口，提供自然语言到 SQL 的转换和执行功能。

功能说明：
1. 定义 POST /api/query 端点
2. 接收用户查询请求（QuerySchema）
3. 使用流式响应返回处理进度和最终结果
4. 依赖注入 QueryService 处理业务逻辑

技术栈：
- FastAPI Router: 组织 API 路由
- StreamingResponse: 服务器发送事件 (SSE)
- media_type="text/event-stream": SSE 标准格式

为什么使用流式响应：
- 实时反馈：用户可以立即看到每个处理步骤
- 降低等待焦虑：展示处理进度（如"抽取关键词"、"生成 SQL"等）
- 逐步输出：不需要等待所有步骤完成才开始返回
- 更好的用户体验：类似打字机效果

SSE 数据格式示例：
    data: {"type": "progress", "step": "抽取关键词", "status": "running"}
    data: {"type": "progress", "step": "抽取关键词", "status": "success"}
    data: {"type": "progress", "step": "召回字段信息", "status": "running"}
    ...
    data: {"type": "result", "data": [{"sales": 1000000}]}

请求示例：
    POST /api/query
    Content-Type: application/json
    
    {"query": "统计华北地区 2025 年的销售额"}

响应流程：
1. 解析请求体 → QuerySchema
2. 注入 QueryService → get_query_service()
3. 调用 query_service.query() → 异步生成器
4. 流式返回每个 chunk → SSE 格式

使用方法：
    # 前端调用示例
    const eventSource = new EventSource('/api/query', {
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: '...'})
    });
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

query_router = APIRouter()


@query_router.post("/api/query")
async def query_handler(query: QuerySchema, query_service: Annotated[QueryService, Depends(get_query_service)]):
    return StreamingResponse(query_service.query(query.query), media_type="text/event-stream")
