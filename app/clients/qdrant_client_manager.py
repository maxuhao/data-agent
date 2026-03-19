"""
Qdrant 向量数据库客户端管理器模块

本模块实现异步 Qdrant 向量数据库客户端的管理，提供语义相似度搜索能力。

功能说明：
1. 封装 AsyncQdrantClient 异步客户端
2. 管理 Qdrant 服务连接和集合配置
3. 存储和检索字段/指标的向量表示

技术栈：
- Qdrant: 开源向量数据库（Rust 编写，高性能）
- AsyncQdrantClient: 官方异步 Python 客户端
- gRPC 协议：高效的二进制通信协议
- REST API：备选通信方式

在智能问数中的作用：
- 字段信息检索：存储字段的向量化表示，支持语义搜索
- 指标信息检索：存储业务指标的向量化表示
- 解决语义鸿沟：用户用语 vs 数据库命名

向量配置：
- embedding_size: 1024 (由 BGE-large-zh 模型决定)
- distance: COSINE (余弦相似度)
  - 值范围：[-1, 1], 越接近 1 越相似
  - 适合文本语义匹配

数据结构：
- Collection: column_info / metric_info
- Point 结构：
  {
    "id": "fact_order.sales_amount",
    "vector": [0.12, -0.45, ..., 0.89],  # 1024 维
    "payload": {  # 元数据
      "name": "销售额",
      "type": "decimal",
      "table_id": "fact_order",
      "description": "...",
      "alias": ["营收", "收入"]
    }
  }

为什么使用 Qdrant：
- 高性能：支持亿级向量毫秒检索
- 过滤灵活：支持向量 + 元数据组合查询
- 易于部署：Docker 一键启动
- 生态完善：与 LangChain 深度集成

使用方法：
    # 初始化
    qdrant_client_manager.init()
    
    # 向量搜索
    results = await qdrant_client_manager.client.query_points(
        collection_name="column_info",
        query=embedding_vector,
        limit=10
    )
    
    # 关闭连接
    await qdrant_client_manager.close()
"""
import asyncio

from qdrant_client import AsyncQdrantClient

from app.conf.app_config import QdrantConfig, app_config
from qdrant_client.models import Distance, VectorParams


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.client: AsyncQdrantClient | None = None
        self.config: QdrantConfig = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncQdrantClient(url=self._get_url())

    async def close(self):
        await self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == '__main__':
    qdrant_client_manager.init()
    client = qdrant_client_manager.client


    async def test():
        # 创建集合
        await client.create_collection(
            collection_name="test_collection_async",
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )

        # 写入数据
        from qdrant_client.models import PointStruct

        await client.upsert(
            collection_name="test_collection_async",
            wait=True,
            points=[
                PointStruct(id=1, vector=[0.05, 0.61, 0.76, 0.74], payload={"city": "Berlin"}),
                PointStruct(id=2, vector=[0.19, 0.81, 0.75, 0.11], payload={"city": "London"}),
                PointStruct(id=3, vector=[0.36, 0.55, 0.47, 0.94], payload={"city": "Moscow"}),
                PointStruct(id=4, vector=[0.18, 0.01, 0.85, 0.80], payload={"city": "New York"}),
                PointStruct(id=5, vector=[0.24, 0.18, 0.22, 0.44], payload={"city": "Beijing"}),
                PointStruct(id=6, vector=[0.35, 0.08, 0.11, 0.44], payload={"city": "Mumbai"}),
            ],
        )

        # 查询数据
        search_result = await client.query_points(
            collection_name="test_collection_async",
            query=[0.2, 0.1, 0.9, 0.7],
            with_payload=False,
            limit=3
        )

        print(search_result.points)

        await qdrant_client_manager.close()


    asyncio.run(test())
