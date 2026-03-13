from qdrant_client import QdrantClient

from app.conf.app_config import QdrantConfig,app_config


class QdrantClientManager:

    def __init__(self, config: QdrantConfig):
        self.client: QdrantClient | None = None
        self.config: QdrantConfig = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = QdrantClient(url=self._get_url())

    def close(self):
        self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == "__main__":
    from qdrant_client.models import Distance, VectorParams, PointStruct
    
    # 初始化客户端
    qdrant_client_manager.init()
    
    collection_name = "test_collection"
    embedding_size = qdrant_client_manager.config.embedding_size
    
    try:
        # 1. 创建集合
        collections = qdrant_client_manager.client.get_collections().collections
        collection_exists = any(col.name == collection_name for col in collections)
        
        if not collection_exists:
            qdrant_client_manager.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE) # 向量参数 设置为向量维度和距离算法
            )
            print(f"✓ 集合 '{collection_name}' 创建成功")
        else:
            print(f"✓ 集合 '{collection_name}' 已存在")
        
        # 2. 写入测试数据
        test_points = [
            PointStruct(id=1, vector=[0.1] * embedding_size, payload={"text": "测试数据 1", "score": 95}),
            PointStruct(id=2, vector=[0.2] * embedding_size, payload={"text": "测试数据 2", "score": 88}),
            PointStruct(id=3, vector=[0.3] * embedding_size, payload={"text": "测试数据 3", "score": 92}),
        ]
        
        response = qdrant_client_manager.client.upsert(collection_name=collection_name, points=test_points)
        print(f"✓ 写入 {len(test_points)} 条数据，状态：{response.status}")
        
        # 3. 查询所有数据
        all_points, _ = qdrant_client_manager.client.scroll(collection_name=collection_name, limit=10) # _ 忽略返回的统计信息
        print(f"✓ 查询到 {len(all_points)} 条数据:")
        for point in all_points:
            print(f"  - ID: {point.id}, Payload: {point.payload}")
        
        # 4. 向量搜索
        query_vector = [0.2] * embedding_size
        results = qdrant_client_manager.client.search(collection_name=collection_name, query_vector=query_vector, limit=3)
        print(f"\n✓ 向量搜索结果 (最相似的 {len(results)} 条):")
        for result in results:
            print(f"  - ID: {result.id}, 分数：{result.score:.4f}, Payload: {result.payload}")
        
        print("\n✓ 测试完成！Qdrant 读写正常")
        
    except Exception as e:
        print(f"✗ 发生错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        qdrant_client_manager.close()


