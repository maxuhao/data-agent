from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:

    def __init__(self, config: EmbeddingConfig):
        self.client: HuggingFaceEndpointEmbeddings | None = None
        self.config: EmbeddingConfig = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())


embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == '__main__':
    embedding_client_manager.init()
    client = embedding_client_manager.client
    import asyncio


    async def test():
        query = await client.aembed_query("hello")
        print(query[:3])

    asyncio.run(test())
