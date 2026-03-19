"""
Elasticsearch 客户端管理器模块

本模块实现异步 Elasticsearch 客户端的管理，提供全文检索和模糊匹配能力。

功能说明：
1. 封装 AsyncElasticsearch 异步客户端
2. 管理 ES 服务连接和索引配置
3. 提供维度字段取值的模糊搜索

技术栈：
- Elasticsearch 8.x: 分布式搜索引擎
- AsyncElasticsearch: 官方异步 Python 客户端
- IK 分词器：中文分词插件（elasticsearch-analysis-ik）

在智能问数中的作用：
- 存储维度字段的所有取值（如地区名、产品名、公司名等）
- 支持模糊匹配和同义词扩展
- 快速检索包含关键词的取值记录

为什么使用 ES 而不是数据库 LIKE：
- 性能优势：倒排索引，适合海量数据检索
- 分词能力：中文自动分词（"华为技术" → ["华为", "技术"]）
- 模糊搜索：支持拼音、错别字容错
- 聚合统计：可以快速计算取值频次

索引结构：
- index_name: value_index (配置文件指定)
- document 结构：
  {
    "column_id": "dim_region.region_name",
    "value": "北京市",
    "count": 5000,
    "examples": [...]
  }

使用方法：
    # 初始化
    es_client_manager.init()
    
    # 搜索取值
    results = await es_client_manager.client.search(
        index="value_index",
        query={"match": {"value": "北京"}}
    )
    
    # 关闭连接
    await es_client_manager.close()
"""
import asyncio

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, config: ESConfig):
        self.client: AsyncElasticsearch | None = None
        self.config: ESConfig = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        await self.client.close()


es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':
    es_client_manager.init()
    client = es_client_manager.client


    async def test():
        # 创建索引
        # await client.indices.create(
        #     index="books",
        # )

        # 写入数据
        await client.index(
            index="books",
            document={
                "name": "Snow Crash",
                "author": "Neal Stephenson",
                "release_date": "1992-06-01",
                "page_count": 470
            },
        )

        # 查询数据
        resp = await client.search(
            index="books",
        )
        print(resp)

        await es_client_manager.close()

    asyncio.run(test())
