"""
指标信息 Mapper 模块

本模块实现 MetricInfo 实体与 MetricInfoMySQL 模型之间的转换。

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
- 输入：MetricInfoMySQL（数据库模型）
- 输出：MetricInfo（业务实体）
- 用途：查询结果转换为 Entity 返回给 Service 层
- 场景：查询指标信息

【to_model】
- 输入：MetricInfo（业务实体）
- 输出：MetricInfoMySQL（数据库模型）
- 用途：Entity 转换为 Model 保存到数据库
- 场景：MetaMySQLRepository.save_metric_infos()
- 实现：使用 dataclasses.asdict() 将 Entity → dict，再解包到 Model

转换示例：
    # Entity → Model
    metric_info = MetricInfo(
        id="sales_amount",
        name="销售额",
        description="订单销售金额总和，不含税",
        relevant_columns=["fact_order.sales_amount"],
        alias=["销售额", "营收", "收入"]
    )
    model = MetricInfoMapper.to_model(metric_info)
    # → MetricInfoMySQL(id="sales_amount", name="销售额", ...)
    
    # Model → Entity
    entity = MetricInfoMapper.to_entity(model)
    # → MetricInfo(id="sales_amount", name="销售额", ...)

在智能问数中的应用：
- MetaMySQLRepository 保存/查询指标信息时使用
- build_meta_knowledge.py 批量导入元数据
- recall_metric 节点召回相关指标

使用方法：
    from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
    
    # Entity → Model
    model = MetricInfoMapper.to_model(metric_info)
    
    # Model → Entity
    entity = MetricInfoMapper.to_entity(model)
"""
from dataclasses import asdict

from app.entities.metric_info import MetricInfo
from app.models.metric_info import MetricInfoMySQL

class MetricInfoMapper:
    @staticmethod
    def to_entity(model: MetricInfoMySQL) -> MetricInfo:
        return MetricInfo(
            id=model.id,
            name=model.name,
            description=model.description,
            relevant_columns=model.relevant_columns,
            alias=model.alias
        )

    @staticmethod
    def to_model(entity: MetricInfo):
        return MetricInfoMySQL(**asdict(entity))
