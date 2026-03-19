"""
表信息 Mapper 模块

本模块实现 TableInfo 实体与 TableInfoMySQL 模型之间的转换。

功能说明：
1. Entity → Model 转换（to_entity）
2. Model → Entity 转换（to_model）
3. 解耦业务逻辑层与数据访问层

Mapper 模式说明：
- Mapper: 数据映射器，负责 Entity 和 Model 之间的转换
- Entity (entities/): 业务实体，用于业务逻辑层
- Model (models/): 数据库模型，用于 ORM 映射
- 分层架构：
  * Controller/API 层 → Entity
  * Service 层 → Entity
  * Repository 层 → Model
  * Mapper → Entity ↔ Model 转换

转换方法：
【to_entity】
- 输入：TableInfoMySQL（数据库模型）
- 输出：TableInfo（业务实体）
- 用途：查询结果转换为 Entity 返回给 Service 层
- 场景：MetaMySQLRepository.get_table_info_by_id()

【to_model】
- 输入：TableInfo（业务实体）
- 输出：TableInfoMySQL（数据库模型）
- 用途：Entity 转换为 Model 保存到数据库
- 场景：MetaMySQLRepository.save_table_infos()
- 实现：使用 dataclasses.asdict() 将 Entity → dict，再解包到 Model

转换示例：
    # Entity → Model
    table_info = TableInfo(
        id="fact_order",
        name="fact_order",
        role="fact",
        description="订单事实表，包含所有订单交易记录"
    )
    model = TableInfoMapper.to_model(table_info)
    # → TableInfoMySQL(id="fact_order", name="fact_order", role="fact", ...)
    
    # Model → Entity
    entity = TableInfoMapper.to_entity(model)
    # → TableInfo(id="fact_order", name="fact_order", role="fact", ...)

在智能问数中的应用：
- MetaMySQLRepository 保存/查询表信息时使用
- build_meta_knowledge.py 批量导入元数据
- merge_retrieved_info 节点补充缺失的表信息

使用方法：
    from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper
    
    # Entity → Model
    model = TableInfoMapper.to_model(table_info)
    
    # Model → Entity
    entity = TableInfoMapper.to_entity(model)
"""
from dataclasses import asdict

from app.entities.table_info import TableInfo
from app.models.table_info import TableInfoMySQL


class TableInfoMapper:
    @staticmethod
    def to_entity(table_info_mysql: TableInfoMySQL) -> TableInfo:
        return TableInfo(
            id=table_info_mysql.id,
            name=table_info_mysql.name,
            role=table_info_mysql.role,
            description=table_info_mysql.description
        )

    @staticmethod
    def to_model(table_info: TableInfo) -> TableInfoMySQL:
        return TableInfoMySQL(**asdict(table_info))
