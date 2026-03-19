"""
FastAPI 依赖注入模块

本模块定义 API 路由中使用的各种依赖项，实现依赖的集中管理和自动注入。

功能说明：
1. 定义数据库会话管理函数（get_meta_session, get_dw_session）
2. 定义 Repository 层的依赖注入函数
3. 定义客户端依赖（embedding_client）
4. 组合依赖：构建 QueryService 所需的完整依赖链

什么是依赖注入：
- FastAPI 的核心特性之一
- 自动创建和管理对象的生命周期
- 通过 Depends() 声明依赖关系
- 支持依赖的嵌套和组合

依赖类型：
1. 会话级依赖（需要清理）：
   - get_meta_session: MySQL 元数据会话
   - get_dw_session: MySQL 数据仓库会话
   - 使用 yield 提供资源，请求结束后自动关闭

2. 单例级依赖（无需清理）：
   - get_embedding_client: 嵌入模型客户端
   - get_*_repository: 各种 Repository 实例
   - 直接从全局管理器获取

3. 组合依赖：
   - get_query_service: 依赖多个底层服务组合而成
   - 自动解析依赖树并注入

为什么使用依赖注入：
- 解耦代码：路由函数不直接创建依赖对象
- 便于测试：可以轻松替换 Mock 依赖
- 生命周期管理：自动处理资源的创建和销毁
- 代码复用：公共依赖只需定义一次

使用方法：
    @app.post("/query")
    async def query(
        service: Annotated[QueryService, Depends(get_query_service)]
    ):
        # FastAPI 会自动注入所有依赖
        return await service.query("...")
        # 请求结束后，会话会自动关闭
"""
from typing import Annotated

from fastapi import Depends
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.query_service import QueryService


async def get_meta_session():
    async with meta_mysql_client_manager.session_factory() as meta_session:
        yield meta_session


async def get_meta_mysql_repository(session: Annotated[AsyncSession, Depends(get_meta_session)]) -> MetaMySQLRepository:
    return MetaMySQLRepository(session)


async def get_embedding_client() -> HuggingFaceEndpointEmbeddings:
    return embedding_client_manager.client


async def get_dw_session():
    async with dw_mysql_client_manager.session_factory() as dw_session:
        yield dw_session


async def get_dw_mysql_repository(session: Annotated[AsyncSession, Depends(get_dw_session)]) -> DWMySQLRepository:
    return DWMySQLRepository(session)


async def get_column_qdrant_repository() -> ColumnQdrantRepository:
    return ColumnQdrantRepository(qdrant_client_manager.client)


async def get_metric_qdrant_repository() -> MetricQdrantRepository:
    return MetricQdrantRepository(qdrant_client_manager.client)


async def get_value_es_repository() -> ValueESRepository:
    return ValueESRepository(es_client_manager.client)


async def get_query_service(
        meta_mysql_repository: Annotated[MetaMySQLRepository, Depends(get_meta_mysql_repository)],
        embedding_client: Annotated[HuggingFaceEndpointEmbeddings, Depends(get_embedding_client)],
        dw_mysql_repository: Annotated[DWMySQLRepository, Depends(get_dw_mysql_repository)],
        column_qdrant_repository: Annotated[ColumnQdrantRepository, Depends(get_column_qdrant_repository)],
        metric_qdrant_repository: Annotated[MetricQdrantRepository, Depends(get_metric_qdrant_repository)],
        value_es_repository: Annotated[ValueESRepository, Depends(get_value_es_repository)]
) -> QueryService:
    return QueryService(
        meta_mysql_repository=meta_mysql_repository,
        embedding_client=embedding_client,
        dw_mysql_repository=dw_mysql_repository,
        column_qdrant_repository=column_qdrant_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        value_es_repository=value_es_repository
    )
