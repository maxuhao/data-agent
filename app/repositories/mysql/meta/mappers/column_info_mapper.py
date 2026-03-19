"""
字段信息 Mapper 模块

本模块实现 ColumnInfo 实体与 ColumnInfoMySQL 模型之间的转换。

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

为什么需要 Mapper：
- 职责分离：业务逻辑不直接依赖数据库模型
- 代码可维护性：Entity 和 Model 的变化互不影响
- 类型安全：明确的转换逻辑
- 易于测试：可以独立测试各层

转换方法：
【to_entity】
- 输入：ColumnInfoMySQL（数据库模型）
- 输出：ColumnInfo（业务实体）
- 用途：查询结果转换为 Entity 返回给 Service 层
- 场景：MetaMySQLRepository.get_column_info_by_id()

【to_model】
- 输入：ColumnInfo（业务实体）
- 输出：ColumnInfoMySQL（数据库模型）
- 用途：Entity 转换为 Model 保存到数据库
- 场景：MetaMySQLRepository.save_column_infos()
- 实现：使用 dataclasses.asdict() 将 Entity → dict，再解包到 Model

转换示例：
    # Entity → Model
    column_info = ColumnInfo(
        id="fact_order.sales_amount",
        name="sales_amount",
        type="decimal(10,2)",
        role="measure",
        examples=[100.50, 2000.00],
        description="销售金额",
        alias=["销售额", "营收"],
        table_id="fact_order"
    )
    model = ColumnInfoMapper.to_model(column_info)
    # → ColumnInfoMySQL(id="fact_order.sales_amount", ...)
    
    # Model → Entity
    entity = ColumnInfoMapper.to_entity(model)
    # → ColumnInfo(id="fact_order.sales_amount", ...)

在智能问数中的应用：
- MetaMySQLRepository 保存/查询字段信息时使用
- build_meta_knowledge.py 批量导入元数据
- merge_retrieved_info 节点补充缺失的字段信息

使用方法：
    from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
    
    # Entity → Model
    model = ColumnInfoMapper.to_model(column_info)
    
    # Model → Entity
    entity = ColumnInfoMapper.to_entity(model)
"""
from dataclasses import asdict

from app.entities.column_info import ColumnInfo
from app.models.column_info import ColumnInfoMySQL


class ColumnInfoMapper:
    @staticmethod
    def to_entity(column_info_mysql: ColumnInfoMySQL) -> ColumnInfo:
        return ColumnInfo(
            id=column_info_mysql.id,
            name=column_info_mysql.name,
            type=column_info_mysql.type,
            role=column_info_mysql.role,
            examples=column_info_mysql.examples,
            description=column_info_mysql.description,
            alias=column_info_mysql.alias,
            table_id=column_info_mysql.table_id,
        )

    @staticmethod
    def to_model(column_info: ColumnInfo) -> ColumnInfoMySQL:
        return ColumnInfoMySQL(**asdict(column_info))
