"""
字段 Qdrant Repository 模块

本模块实现对 Qdrant 向量数据库中字段信息的访问操作，提供字段的语义检索能力。

功能说明：
1. 确保集合存在（ensure_collection）
2. 批量插入/更新字段向量数据（upsert）
3. 向量相似度搜索（search）

Repository 模式说明：
- Repository: 数据仓库模式，封装数据访问逻辑
- 位于 Service 层之下，直接操作 Qdrant 客户端
- 提供粗粒度的向量数据操作方法
- 与 Qdrant 客户端绑定，通过依赖注入获取

Qdrant 集合配置：
- collection_name: "column_info_collection"
- vector_size: 1024（由 BGE-large-zh 模型决定）
- distance: COSINE（余弦相似度）
  - 值范围：[-1, 1]，越接近 1 越相似
  - 适合文本语义匹配

方法详解：
【ensure_collection】
- 用途：检查并创建 Qdrant 集合
- 逻辑：如果集合不存在则创建
- 配置：使用 app_config.qdrant.embedding_size
- 幂等性：多次调用不会重复创建

【upsert】
- 用途：批量插入或更新向量数据
- 参数：
  * ids: 向量 ID 列表（UUID）
  * embeddings: 向量数据列表（1024 维浮点数）
  * payloads: 负载数据列表（ColumnInfo 的字典形式）
  * batch_size: 批量大小（默认 10，避免单次请求过大）
- 过程：
  1. 组合 id + embedding + payload → PointStruct
  2. 分批调用 client.upsert()
- 特点：支持增量更新（相同 ID 会覆盖）

【search】
- 用途：向量相似度搜索
- 参数：
  * embedding: 查询向量（1024 维）
  * score_threshold: 相似度阈值（默认 0.6，过滤低质量匹配）
  * limit: 返回数量限制（默认 20 个）
- 返回：ColumnInfo 实体列表
- 过程：
  1. 调用 client.query_points() 查询
  2. 过滤低于阈值的結果
  3. payload → ColumnInfo 实体

在智能问数中的作用：
- 语义检索：recall_column 节点召回相关字段
- 解决语义鸿沟：用户说 "销售" 匹配 "sales_amount"
- 别名支持：字段的名称、描述、别名都向量化

向量数据来源：
- build_meta_knowledge.py 批量生成
- 为字段名、描述、每个别名分别生成向量
- 批量向量化（每批 20 个）避免内存溢出

使用方法：
    # 通过依赖注入获取
    repo = ColumnQdrantRepository(qdrant_client_manager.client)
    
    # 确保集合存在
    await repo.ensure_collection()
    
    # 批量插入向量
    await repo.upsert(ids, embeddings, payloads, batch_size=10)
    
    # 向量搜索
    embedding = await embedding_client.aembed_query("销售额")
    results = await repo.search(embedding, score_threshold=0.6, limit=20)
    # 返回：[ColumnInfo(name="sales_amount", ...), ...]
"""
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import VectorParams, Distance

from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:
    collection_name = "column_info_collection"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=app_config.qdrant.embedding_size, distance=Distance.COSINE)
            )

    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[dict], batch_size: int = 10):
        points: list[PointStruct] = [PointStruct(id=id, vector=embedding, payload=payload) for id, embedding, payload in
                                     zip(ids, embeddings, payloads)]
        for i in range(0, len(points), batch_size):
            await self.client.upsert(collection_name=self.collection_name, points=points[i:i + batch_size])

    async def search(self, embedding: list[float], score_threshold: float = 0.6, limit: int = 20) -> list[ColumnInfo]:
        # 查询数据
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        return [ColumnInfo(**point.payload) for point in result.points]
