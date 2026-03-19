"""
嵌入模型客户端管理器模块

本模块实现 Hugging Face 嵌入模型服务的管理，提供文本向量化功能。

功能说明：
1. 封装 LangChain 的 HuggingFaceEndpointEmbeddings 客户端
2. 管理嵌入模型服务的连接和配置
3. 提供文本 → 向量（Embedding）的转换能力

什么是 Embedding：
- 将文本转换为固定长度的向量表示
- 语义相似的文本向量距离更近
- 用于语义搜索、相似度匹配等场景

使用的模型：
- BGE-large-zh-v1.5：智源中文嵌入模型
- 向量维度：1024
- 擅长中文语义理解

技术栈：
- LangChain HuggingFace: 集成 HF 平台的嵌入模型
- HTTP API: 通过 REST API 调用嵌入服务
- Docker 部署：本地运行 HF Inference Endpoint

为什么需要向量化：
- 语义检索：用户说 "销售" 可以匹配 "销售额"、"营收"等
- 解决同义词问题：不同表达相同概念
- 模糊匹配：不依赖精确字面匹配

使用方法：
    # 初始化
    embedding_client_manager.init()
    
    # 向量化单个文本
    vector = await embedding_client_manager.client.aembed_query("销售额")
    
    # 向量化多个文本
    vectors = await embedding_client_manager.client.aembed_documents(["文本 1", "文本 2"])
"""
import asyncio

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: HuggingFaceEndpointEmbeddings | None = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())

embedding_client_manager = EmbeddingClientManager(app_config.embedding)


if __name__ == '__main__':
    embedding_client_manager.init()
    client = embedding_client_manager.client

    async def test():
        text = "What is deep learning?"
        query_result = await client.aembed_query(text)
        print(query_result[:3])

    asyncio.run(test())