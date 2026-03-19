"""
智能问数 Agent 的上下文定义模块

本模块定义了 LangGraph 工作流的上下文数据结构，用于存储所有节点共享的依赖注入对象。

上下文与状态的区别：
- State (状态): 存储动态变化的数据（如查询、关键词、SQL 等）
- Context (上下文): 存储静态的依赖对象（如数据库连接、向量库客户端等）

设计优势：
1. 依赖注入：所有 Repository 和 Client 在图初始化时传入，避免重复创建
2. 资源共享：所有节点共享同一个数据库连接和客户端实例
3. 类型安全：使用 TypedDict 确保上下文字段类型正确
4. 易于测试：可以轻松替换 Mock 对象进行单元测试

包含的依赖：
- column_qdrant_repository: Qdrant 向量数据库 - 字段信息检索
- metric_qdrant_repository: Qdrant 向量数据库 - 指标信息检索
- value_es_repository: Elasticsearch - 维度字段取值检索
- embedding_client: BGE 嵌入模型客户端 - 文本向量化
- meta_mysql_repository: MySQL - 元数据库访问（存储表结构、指标定义等）
- dw_mysql_repository: MySQL - 数据仓库访问（存储业务数据）

示例用法：
    context: DataAgentContext = {
        "column_qdrant_repository": ColumnQdrantRepository(client),
        "embedding_client": embedding_model,
        "meta_mysql_repository": MetaMySQLRepository(session)
    }
    async for chunk in graph.astream(input=state, context=context):
        ...
"""
from typing import TypedDict

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class DataAgentContext(TypedDict):
    column_qdrant_repository: ColumnQdrantRepository
    embedding_client: HuggingFaceEndpointEmbeddings
    metric_qdrant_repository: MetricQdrantRepository
    value_es_repository: ValueESRepository
    meta_mysql_repository: MetaMySQLRepository
    dw_mysql_repository: DWMySQLRepository
