"""
元数据 MySQL Repository 模块

本模块实现对元数据（Meta）MySQL 数据库的访问操作，负责表信息、字段信息、指标信息的持久化。

功能说明：
1. 批量保存表信息（save_table_infos）
2. 批量保存字段信息（save_column_infos）
3. 批量保存指标信息（save_metric_infos）
4. 保存指标 - 字段关联关系（save_column_metrics）
5. 根据 ID 查询字段信息（get_column_info_by_id）
6. 根据 ID 查询表信息（get_table_info_by_id）
7. 查询表的关键字段（get_key_columns_by_table_id）

Repository 模式说明：
- Repository: 数据仓库模式，封装数据访问逻辑
- 位于 Service 层之下，直接操作数据库
- 使用 Mapper 进行 Entity ↔ Model 转换
- 与 MySQL 会话绑定，通过依赖注入获取

Entity vs Model：
- Entity (entities/): 业务实体，用于业务逻辑层
- Model (models/): 数据库模型，用于 ORM 映射
- Mapper: 负责 Entity 和 Model 之间的转换

方法详解：
【save_table_infos / save_column_infos / save_metric_infos】
- 用途：批量保存元数据到数据库
- 参数：Entity 对象列表
- 过程：Entity → Model → SQLAlchemy add_all()
- 事务：需要调用方管理事务提交

【get_column_info_by_id / get_table_info_by_id】
- 用途：根据 ID 查询元数据
- 参数：ID（如 "fact_order.sales_amount"）
- 返回：Entity 对象或 None
- 过程：Model → Entity

【get_key_columns_by_table_id】
- 用途：查询表的主键和外键字段
- SQL: SELECT * FROM column_info WHERE table_id=? AND role IN ('primary_key','foreign_key')
- 返回：ColumnInfo 列表
- 用途：SQL 生成时需要自动关联主外键

在智能问数中的作用：
- 元数据管理：build_meta_knowledge.py 保存解析后的元数据
- 信息补充：merge_retrieved_info 节点补充缺失的字段信息
- 关键列获取：为生成的 SQL 自动添加主外键关联

数据来源：
- build_meta_knowledge.py 从配置文件导入
- 人工在元数据库中维护

使用方法：
    # 通过依赖注入获取
    async with meta_mysql_client_manager.session_factory() as session:
        repo = MetaMySQLRepository(session)
        
        # 保存表信息（需要事务）
        async with repo.session.begin():
            repo.save_table_infos(table_infos)
            repo.save_column_infos(column_infos)
        
        # 查询字段信息
        column_info = await repo.get_column_info_by_id("fact_order.sales_amount")
        
        # 查询关键列
        key_columns = await repo.get_key_columns_by_table_id("fact_order")
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.models.column_info import ColumnInfoMySQL
from app.models.table_info import TableInfoMySQL
from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
from app.repositories.mysql.meta.mappers.column_metric_mapper import ColumnMetricMapper
from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper


class MetaMySQLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def save_table_infos(self, table_infos: list[TableInfo]):
        self.session.add_all([TableInfoMapper.to_model(table_info) for table_info in table_infos])

    def save_column_infos(self, column_infos: list[ColumnInfo]):
        self.session.add_all([ColumnInfoMapper.to_model(column_info) for column_info in column_infos])

    def save_metric_infos(self, metric_infos: list[MetricInfo]):
        self.session.add_all([MetricInfoMapper.to_model(metric_info) for metric_info in metric_infos])

    def save_column_metrics(self, column_metrics: list[ColumnMetric]):
        self.session.add_all([ColumnMetricMapper.to_model(column_metric) for column_metric in column_metrics])

    async def get_column_info_by_id(self, id: str) -> ColumnInfo | None:
        column_info: ColumnInfoMySQL | None = await self.session.get(ColumnInfoMySQL, id)
        if column_info:
            return ColumnInfoMapper.to_entity(column_info)
        else:
            return None

    async def get_table_info_by_id(self, id: str) -> TableInfo | None:
        table_info: TableInfoMySQL | None = await self.session.get(TableInfoMySQL, id)
        if table_info:
            return TableInfoMapper.to_entity(table_info)
        else:
            return None

    async def get_key_columns_by_table_id(self, table_id: str) -> list[ColumnInfo]:
        sql = "select * from column_info where table_id = :table_id and role in ('primary_key','foreign_key')"
        result = await self.session.execute(text(sql), {"table_id": table_id})
        return [ColumnInfo(**dict(row)) for row in result.mappings().fetchall()]
