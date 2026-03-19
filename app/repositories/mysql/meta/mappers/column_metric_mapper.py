"""
指标 - 字段关联 Mapper 模块

本模块实现 ColumnMetric 实体与 ColumnMetricMySQL 模型之间的转换。

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
- 输入：ColumnMetricMySQL（数据库模型）
- 输出：ColumnMetric（业务实体）
- 用途：查询结果转换为 Entity 返回给 Service 层
- 场景：查询指标与字段的关联关系

【to_model】
- 输入：ColumnMetric（业务实体）
- 输出：ColumnMetricMySQL（数据库模型）
- 用途：Entity 转换为 Model 保存到数据库
- 场景：MetaMySQLRepository.save_column_metrics()
- 实现：使用 dataclasses.asdict() 将 Entity → dict，再解包到 Model

转换示例：
    # Entity → Model
    column_metric = ColumnMetric(
        column_id="fact_order.sales_amount",
        metric_id="sales_amount"
    )
    model = ColumnMetricMapper.to_model(column_metric)
    # → ColumnMetricMySQL(column_id="fact_order.sales_amount", metric_id="sales_amount")
    
    # Model → Entity
    entity = ColumnMetricMapper.to_entity(model)
    # → ColumnMetric(column_id="fact_order.sales_amount", metric_id="sales_amount")

在智能问数中的应用：
- MetaMySQLRepository 保存指标 - 字段关联关系时使用
- build_meta_knowledge.py 批量导入元数据
- 快速定位指标涉及的字段

使用方法：
    from app.repositories.mysql.meta.mappers.column_metric_mapper import ColumnMetricMapper
    
    # Entity → Model
    model = ColumnMetricMapper.to_model(column_metric)
    
    # Model → Entity
    entity = ColumnMetricMapper.to_entity(model)
"""
from dataclasses import asdict

from app.entities.column_metric import ColumnMetric
from app.models.column_metric import ColumnMetricMySQL


class ColumnMetricMapper:
    @staticmethod
    def to_entity(column_metric_mysql: ColumnMetricMySQL):
        return ColumnMetric(
            column_id=column_metric_mysql.column_id,
            metric_id=column_metric_mysql.metric_id
        )

    @staticmethod
    def to_model(column_metric: ColumnMetric):
        return ColumnMetricMySQL(**asdict(column_metric))
