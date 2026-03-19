"""
指标 - 字段关联模型模块

本模块定义 column_metric 表的 ORM 模型，用于建立指标与字段之间的关联关系。

功能说明：
1. 映射 database 中的 column_metric 表
2. 记录指标与字段的关联关系（多对多）
3. 支持复合指标（涉及多个字段）

表结构说明：
- column_id: 字段编号（主键之一，外键引用 column_info）
- metric_id: 指标编号（主键之一，外键引用 metric_info）
- 复合主键：(column_id, metric_id) 确保关联唯一性

为什么需要关联表：
【场景 1：单一指标】
- 销售额 = SUM(fact_order.sales_amount)
- 只涉及一个字段，直接关联即可

【场景 2：复合指标】
- 利润率 = (销售额 - 成本) / 销售额 * 100%
- 涉及多个字段：sales_amount, cost_amount
- 需要多条关联记录：
  * (fact_order.sales_amount, profit_margin)
  * (fact_order.cost_amount, profit_margin)

【场景 3：多对多关系】
- 一个字段可能参与多个指标：
  * sales_amount → 销售额、毛利率、客单价
- 一个指标可能涉及多个字段：
  * 利润率 → sales_amount, cost_amount

关系示例：
    column_metric 表数据：
    +----------------------+---------------+
    | column_id            | metric_id     |
    +----------------------+---------------+
    | fact_order.sales_amount | sales_amount |
    | fact_order.sales_amount | profit_margin |
    | fact_order.cost_amount  | profit_margin |
    | fact_order.order_id     | order_count   |
    +----------------------+---------------+

在智能问数中的作用：
- 快速定位：给定指标，快速找到相关字段
- SQL 生成：LLM 根据关联字段构建计算逻辑
- 指标解析：识别复合指标涉及的所有字段

数据来源：
- 从 metric_info.relevant_columns 自动推导
- build_meta_knowledge.py 批量导入

使用方法：
    # 查询某指标涉及的所有字段
    from app.models.column_metric import ColumnMetricMySQL
    columns = await session.execute(
        select(ColumnMetricMySQL.column_id)
        .where(ColumnMetricMySQL.metric_id == "profit_margin")
    )
    # 返回：["fact_order.sales_amount", "fact_order.cost_amount"]
    
    # 查询某字段参与的所有指标
    metrics = await session.execute(
        select(ColumnMetricMySQL.metric_id)
        .where(ColumnMetricMySQL.column_id == "fact_order.sales_amount")
    )
    # 返回：["sales_amount", "profit_margin"]
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class ColumnMetricMySQL(Base):
    __tablename__ = "column_metric"

    column_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="列编号"
    )
    metric_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="指标编号"
    )
