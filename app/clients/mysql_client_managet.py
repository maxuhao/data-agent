import asyncio
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine

from app.conf.app_config import DBConfig,app_config


class MySqlClientManager:
    def __init__(self, config: DBConfig):
        self.engine : AsyncEngine | None =  None
        self.confing: DBConfig = config

    def _get_url(self):
        return f"mysql+asyncmy://{self.confing.user}:{self.confing.password}@{self.confing.host}:{self.confing.port}/{self.confing.database}?charset=utf8mb4"

    def init(self):
        self.engine = create_async_engine(self._get_url(),pool_size=10,pool_pre_ping=True)

    def close(self):
        self.engine.dispose()


meta_mysql_client_manager = MySqlClientManager(app_config.db_meta)
dw_mysql_client_manager = MySqlClientManager(app_config.db_dw)


if __name__ == '__main__':
    dw_mysql_client_manager.init()
    engine = dw_mysql_client_manager.engine

    async def test():
        async with AsyncSession(engine,autoflush=True, expire_on_commit=False) as session:
            sql = "select * from fact_order limit 10"
            result = await session.execute(text(sql))

            rows = result.mappings().fetchall()

            print(type(rows))
            print(type(rows[0]))
            print(rows)
            print(rows[0]["order_id"])


    asyncio.run(test())








