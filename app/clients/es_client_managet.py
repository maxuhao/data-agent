from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig,app_config


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


if __name__ == "__main__":
    import asyncio



    async def main():
        # 初始化客户端
        await es_client_manager.init()
            
        index_name = "test_index"
            
        try:
            # 1. 创建索引并写入数据
            print("=" * 60)
            print("📝 写入测试数据")
            print("=" * 60)
                
            doc = {
                "text": "Elasticsearch 测试数据",
                "score": 95,
                "tags": ["测试", "ES", "数据库"]
            }
                
            response = await es_client_manager.client.index(
                index=index_name,
                document=doc
            )
            print(f"✓ 写入成功，ID: {response['_id']}")
            print()
                
            # 2. 查询所有数据
            print("=" * 60)
            print("🔍 查询所有数据")
            print("=" * 60)
                
            query = {
                "query": {
                    "match_all": {}
                }
            }
                
            result = await es_client_manager.client.search(
                index=index_name,
                body=query
            )
                
            hits = result['hits']['hits']
            print(f"✓ 查询到 {len(hits)} 条数据:\n")
            for hit in hits:
                print(f"ID: {hit['_id']}, 分数：{hit['_score']}")
                print(f"  数据：{hit['_source']}")
                print()
                
            print("\n✓ 测试完成！Elasticsearch 读写正常")
                
        except Exception as e:
            print(f"✗ 发生错误：{e}")
            import traceback
            traceback.print_exc()
        finally:
            await es_client_manager.close()

    asyncio.run(main())


