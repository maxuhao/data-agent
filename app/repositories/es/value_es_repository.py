"""
字段取值 Elasticsearch Repository 模块

本模块实现对 Elasticsearch 中维度字段取值的访问操作，提供全文检索和模糊匹配能力。

功能说明：
1. 确保索引存在（ensure_index）
2. 批量索引字段取值（index）
3. 全文检索匹配取值（search）

Repository 模式说明：
- Repository: 数据仓库模式，封装数据访问逻辑
- 位于 Service 层之下，直接操作 ES 客户端
- 提供粗粒度的全文检索操作方法
- 与 ES 客户端绑定，通过依赖注入获取

Elasticsearch 索引配置：
- index_name: "value_index"
- analyzer: "ik_max_word"（中文分词器）
  - ik_max_word: 最细粒度分词，适合搜索
  - 例："华为技术有限公司" → ["华为", "技术", "有限公司", "华为技术", ...]
- mappings:
  * id: keyword（精确匹配，不分词）
  * value: text + IK 分词（全文检索）
  * column_id: keyword（精确匹配）

方法详解：
【ensure_index】
- 用途：检查并创建 ES 索引
- 逻辑：如果索引不存在则创建
- 配置：使用预定义的 index_mappings
- 幂等性：多次调用不会重复创建

【index】
- 用途：批量索引字段取值
- 参数：
  * value_infos: ValueInfo 实体列表
  * batch_size: 批量大小（默认 20）
- 过程：
  1. 分批处理（避免单次请求过大）
  2. 构建 bulk operations（index 指令 + 文档）
  3. 调用 client.bulk() 批量写入
- 特点：
  * 支持海量数据（百万级）
  * 自动分词（IK analyzer）
  * 支持模糊匹配、同义词

【search】
- 用途：全文检索匹配的取值
- 参数：
  * keyword: 搜索关键词
  * score_threshold: 相关性阈值（默认 0.6）
  * limit: 返回数量限制（默认 20）
- 查询类型：match query（全文匹配）
- 返回：ValueInfo 实体列表
- 过程：
  1. 调用 client.search() 查询
  2. 过滤低于阈值的結果
  3. 解析 _source → ValueInfo 实体

在智能问数中的作用：
- 模糊匹配：recall_value 节点召回用户提到的具体值
- 解决歧义："北京" → 匹配 "北京市"、"北京区"、"北京市分公司"
- 同义词识别："华为" → 匹配 "华为技术"、"华为终端"、"华为公司"

分词效果示例：
    用户搜索："华为"
    ES 分词：["华为"]
    匹配结果：
    - "华为技术有限公司" (score: 0.95)
    - "华为终端有限公司" (score: 0.85)
    - "华为云" (score: 0.75)

数据来源：
- build_meta_knowledge.py 从 DW 库查询
- 只对 sync=True 的字段建立索引
- 每个字段最多取 100000 条记录

使用方法：
    # 通过依赖注入获取
    repo = ValueESRepository(es_client_manager.client)
    
    # 确保索引存在
    await repo.ensure_index()
    
    # 批量索引取值
    await repo.index(value_infos, batch_size=20)
    
    # 全文检索
    results = await repo.search("华为", score_threshold=0.6, limit=20)
    # 返回：[ValueInfo(value="华为技术有限公司"), ValueInfo(value="华为云"), ...]
"""
from dataclasses import asdict

from elasticsearch import AsyncElasticsearch

from app.entities.value_info import ValueInfo


class ValueESRepository:
    index_name = "value_index"
    index_mappings = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "column_id": {"type": "keyword"}
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def ensure_index(self):
        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(
                index=self.index_name,
                mappings=self.index_mappings
            )

    async def index(self, value_infos: list[ValueInfo], batch_size=20):
        for i in range(0, len(value_infos), batch_size):
            batch_value_infos = value_infos[i:i + batch_size]
            batch_operations = []
            for value_info in batch_value_infos:
                batch_operations.append(
                    {
                        "index": {
                            "_index": self.index_name
                        }
                    }
                )
                batch_operations.append(asdict(value_info))
            await self.client.bulk(operations=batch_operations)

    async def search(self, keyword: str, score_threshold: float = 0.6, limit: int = 20) -> list[ValueInfo]:
        resp = await self.client.search(
            index=self.index_name,
            query={
                "match": {
                    "value": keyword
                }
            },
            size=limit,
            min_score=score_threshold
        )
        return [ValueInfo(**hit['_source']) for hit in resp['hits']['hits']]
