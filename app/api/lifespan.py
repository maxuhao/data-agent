"""
FastAPI 应用生命周期管理模块

本模块定义 FastAPI 应用的启动和关闭时的资源管理逻辑，确保所有外部服务连接正确初始化和释放。

功能说明：
1. 使用 @asynccontextmanager 装饰器定义异步上下文管理器
2. 在应用启动时初始化所有客户端连接：
   - Qdrant 向量数据库客户端
   - Embedding 嵌入模型客户端
   - Elasticsearch 搜索引擎客户端
   - Meta MySQL 元数据库连接
   - DW MySQL 数据仓库连接
3. 在应用关闭时优雅地关闭所有连接，释放资源

为什么需要生命周期管理：
- 资源优化：避免连接泄漏，确保连接池正确关闭
- 单例初始化：全局共享的客户端只需初始化一次
- 优雅关闭：确保未完成的请求处理完毕后再关闭连接
- 错误预防：防止应用已关闭但连接仍在使用的情况

FastAPI 生命周期流程：
1. 应用启动前 → 执行 lifespan 的前置代码（init）
2. 应用运行中 → yield 将控制权交给 FastAPI
3. 应用关闭时 → 执行 lifespan 的后置代码（close）

使用方法：
    from fastapi import FastAPI
    from app.api.lifespan import lifespan
    
    app = FastAPI(lifespan=lifespan)
    # 应用启动时会自动调用 init()
    # 应用关闭时会自动调用 close()
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    yield # 进入应用运行中
    await qdrant_client_manager.close()
    await es_client_manager.close()
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
