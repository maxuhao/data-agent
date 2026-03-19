"""
MySQL 客户端管理器模块

本模块实现异步 MySQL 数据库连接的管理，提供连接池和会话工厂。

功能说明：
1. 封装 SQLAlchemy 异步引擎的创建和管理
2. 提供统一的数据库连接配置
3. 管理两个独立的数据库连接：
   - meta_mysql: 元数据库（表结构、指标定义等）
   - dw_mysql: 数据仓库（业务数据）

技术栈：
- SQLAlchemy Async: Python SQL 工具包的异步版本
- asyncmy: 高性能的异步 MySQL 驱动
- 连接池：避免频繁创建/销毁连接，提高性能

设计考虑：
- 单例模式：每个数据库一个全局管理器实例
- 懒加载：需要时才初始化连接
- 异步支持：使用 async/await 提高并发性能
- 字符集：使用 utf8mb4 支持中文和 emoji

为什么分开两个数据库：
- 职责分离：元数据 vs 业务数据
- 性能优化：不同的查询负载
- 安全隔离：元数据修改频率低，业务数据访问频繁

使用方法：
    # 初始化
    mysql_client_manager.init()
    
    # 创建会话并执行查询
    async with mysql_client_manager.session_factory() as session:
        result = await session.execute(text("SELECT * FROM table"))
        rows = result.fetchall()
    
    # 关闭连接
    await mysql_client_manager.close()
"""
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from app.conf.app_config import DBConfig, app_config


class MySQLClientManager:
    def __init__(self, config: DBConfig):
        self.engine: AsyncEngine | None = None
        self.session_factory = None
        self.config = config

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init(self):
        self.engine = create_async_engine(self._get_url(), pool_size=10, pool_pre_ping=True)
        self.session_factory= async_sessionmaker(self.engine, autoflush=True, expire_on_commit=False)

    async def close(self):
        await self.engine.dispose()


meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)
dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)

if __name__ == '__main__':
    dw_mysql_client_manager.init()


    async def test():
        async with dw_mysql_client_manager.session_factory() as session:
            sql = "select * from fact_order limit 10"
            result = await session.execute(text(sql))

            rows = result.mappings().fetchall()

            print(type(rows))
            print(type(rows[0]))
            print(rows[0]['order_id'])


    asyncio.run(test())
