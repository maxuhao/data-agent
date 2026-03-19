"""
数据仓库 MySQL Repository 模块

本模块实现对数据仓库（DW）MySQL 数据库的访问操作，提供表结构查询、数据取样等功能。

功能说明：
1. 查询表的字段类型信息（get_column_types）
2. 查询字段的取值示例（get_column_values）
3. 获取数据库版本信息（get_db_info）
4. 验证 SQL 语法（validate）
5. 执行 SQL 查询（run）

Repository 模式说明：
- Repository: 数据仓库模式，封装数据访问逻辑
- 位于 Service 层之下，直接操作数据库
- 提供粗粒度的数据操作方法
- 与 MySQL 会话绑定，通过依赖注入获取

方法详解：
【get_column_types】
- 用途：查询表的字段类型定义
- SQL: SHOW COLUMNS FROM table_name
- 返回：{字段名：类型} 字典
- 示例：{"order_id": "varchar(30)", "sales_amount": "decimal(10,2)"}

【get_column_values】
- 用途：查询字段的不重复取值（用于示例）
- SQL: SELECT DISTINCT column FROM table LIMIT n
- 参数：limit 控制返回数量（默认 10 个）
- 示例：["北京", "上海", "广州"]

【get_db_info】
- 用途：获取数据库方言和版本号
- 返回：{"dialect": "mysql", "version": "8.0.35"}
- 用于 SQL 生成时适配数据库特性

【validate】
- 用途：验证 SQL 语法是否正确
- 方法：使用 EXPLAIN 执行计划验证
- 成功：无异常
- 失败：抛出 SQLAlchemy 异常

【run】
- 用途：执行 SQL 查询并返回结果
- 返回：字典列表（每行一个字典）
- 示例：[{"order_id": "001", "sales": 100}, ...]

在智能问数中的作用：
- 元数据采集：build_meta_knowledge.py 采集表结构和数据
- SQL 验证：validate_sql 节点验证生成的 SQL
- SQL 执行：run_sql 节点执行最终查询
- 数据取样：为字段信息提供示例值

使用方法：
    # 通过依赖注入获取
    async with dw_mysql_client_manager.session_factory() as session:
        repo = DWMySQLRepository(session)
        
        # 查询字段类型
        types = await repo.get_column_types("fact_order")
        
        # 查询取值示例
        values = await repo.get_column_values("fact_order", "region_name", limit=10)
        
        # 验证 SQL
        await repo.validate("SELECT * FROM fact_order")
        
        # 执行 SQL
        results = await repo.run("SELECT SUM(sales) FROM fact_order")
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DWMySQLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        result_dict = result.mappings().fetchall()
        # [{Field:order_id,Type:varchar(30),Null:No},{Field:customer_id,Type:varchar(20),Null:YES}]

        return {row['Field']: row['Type'] for row in result_dict}
        # {order_id:varchar(30),customer_id:varchar(30)}

    async def get_column_values(self, table_name, column_name, limit=10):
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return [row[0] for row in result.fetchall()]

    async def get_db_info(self):
        sql = "select version()"
        result = await self.session.execute(text(sql))
        version = result.scalar()

        dialect = self.session.bind.dialect.name
        return {"dialect": dialect, "version": version}

    async def validate(self, sql: str):
        sql = f"explain {sql}"
        await self.session.execute(text(sql))

    async def run(self, sql: str) -> list[dict]:
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]
