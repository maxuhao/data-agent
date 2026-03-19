"""
查询服务模块

本模块实现智能问数系统的核心业务逻辑，将用户自然语言查询转换为 SQL 执行并返回结果。

功能说明：
1. 接收用户自然语言查询
2. 构建 Agent 状态和上下文
3. 驱动 LangGraph 工作流执行
4. 以 SSE 格式流式返回处理进度和结果
5. 异常处理和错误格式化

技术栈：
- LangGraph: 编排多阶段 Agent 工作流
- SSE (Server-Sent Events): 服务器推送实时数据
- JSON 序列化：将 Python 对象转换为 JSON 格式
- ensure_ascii=False: 保留中文字符

工作流程：
1. 创建初始状态 DataAgentState(query=用户输入)
2. 准备上下文 DataAgentContext(注入所有 Repository 和 Client)
3. 调用 graph.astream() 启动工作流
4. 遍历每个输出块并格式化为 SSE
5. 捕获异常并返回友好的错误消息

SSE 数据格式：
    data: {"type": "progress", "step": "抽取关键词", "status": "running"}
    data: {"type": "progress", "step": "生成 SQL", "status": "success"}
    data: {"type": "result", "data": [{"sales": 1000000}]}
    data: {"type": "error", "message": "SQL 语法错误..."}

为什么使用异步生成器：
- 非阻塞：不会占用整个事件循环
- 流式输出：逐步返回结果，降低用户等待焦虑
- 内存友好：不需要缓存所有结果
- 符合 FastAPI 的 StreamingResponse 要求

依赖注入：
通过构造函数注入所有需要的 Repository：
- meta_mysql_repository: 读取表结构元数据
- dw_mysql_repository: 执行业务 SQL
- column_qdrant_repository: 语义检索字段信息
- metric_qdrant_repository: 语义检索指标信息
- value_es_repository: 模糊匹配维度取值
- embedding_client: 文本向量化

使用方法：
    # API 层调用
    @app.post("/api/query")
    async def query_handler(query: QuerySchema, service: QueryService):
        return StreamingResponse(
            service.query(query.query),
            media_type="text/event-stream"
        )
"""
import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(self,
                 meta_mysql_repository: MetaMySQLRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 dw_mysql_repository: DWMySQLRepository,
                 column_qdrant_repository: ColumnQdrantRepository,
                 metric_qdrant_repository: MetricQdrantRepository,
                 value_es_repository: ValueESRepository
                 ):
        self.meta_mysql_repository = meta_mysql_repository
        self.embedding_client = embedding_client
        self.dw_mysql_repository = dw_mysql_repository

        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.value_es_repository = value_es_repository

    async def query(self, query: str):
        state = DataAgentState(query=query)
        context = DataAgentContext(column_qdrant_repository=self.column_qdrant_repository,
                                   embedding_client=self.embedding_client,
                                   metric_qdrant_repository=self.metric_qdrant_repository,
                                   value_es_repository=self.value_es_repository,
                                   meta_mysql_repository=self.meta_mysql_repository,
                                   dw_mysql_repository=self.dw_mysql_repository)
        try:
            async for chunk in graph.astream(input=state, context=context, stream_mode='custom'):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            error = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error, ensure_ascii=False, default=str)}\n\n"
