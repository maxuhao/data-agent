"""
指标信息模型模块

本模块定义 metric_info 表的 ORM 模型，用于存储预定义的业务指标。

功能说明：
1. 映射 database 中的 metric_info 表
2. 存储业务指标的定义和计算逻辑
3. 支持指标别名和关联字段配置

表结构说明：
- id: 指标编码（主键，如 "sales_amount", "profit_margin"）
- name: 指标名称（中文业务术语）
- description: 指标描述（计算公式、统计口径、业务范围）
- relevant_columns: 关联字段（JSON 数组，计算该指标需要的字段 ID 列表）
- alias: 指标别名（JSON 数组，同义词列表）

什么是业务指标：
- 预定义的度量标准，有明确的计算逻辑
- 统一统计口径，避免歧义
- 可能涉及多个字段的组合计算

指标示例：
【销售额】
- id: "sales_amount"
- name: "销售额"
- description: "订单销售金额总和，不含税，基于 fact_order.sales_amount 聚合"
- relevant_columns: ["fact_order.sales_amount"]
- alias: ["营收", "收入", "销售收入", "业绩"]

【利润率】
- id: "profit_margin"
- name: "利润率"
- description: "利润占销售额的百分比，计算公式：(销售额 - 成本) / 销售额 * 100%"
- relevant_columns: ["fact_order.sales_amount", "fact_order.cost_amount"]
- alias: ["毛利率", "盈利比率"]

为什么需要指标模型：
- 统一口径：避免不同人对同一指标理解不一致
- 简化 SQL 生成：LLM 直接使用预定义的计算逻辑
- 业务语义层：连接技术实现和业务语言
- 别名支持：识别用户的不同表达方式

在智能问数中的应用：
- 用户问 "销售额是多少" → 匹配 sales_amount 指标
- 用户问 "利润率怎么样" → 匹配 profit_margin 指标
- LLM 根据 relevant_columns 生成正确的聚合 SQL

数据来源：
- 人工在 meta_config.yaml 中配置
- 通过 build_meta_knowledge.py 导入到数据库

使用方法：
    # 查询所有指标
    from app.models.metric_info import MetricInfoMySQL
    metrics = await session.execute(select(MetricInfoMySQL))
    
    # 查询某指标的关联字段
    metric = await session.get(MetricInfoMySQL, "sales_amount")
    print(metric.relevant_columns)  # ["fact_order.sales_amount"]
"""
from sqlalchemy import String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class MetricInfoMySQL(Base):
    __tablename__ = "metric_info"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="指标编码"
    )
    name: Mapped[str | None] = mapped_column(
        String(128),
        comment="指标名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="指标描述"
    )
    relevant_columns: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="关联字段"
    )
    alias: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="指标别名"
    )
