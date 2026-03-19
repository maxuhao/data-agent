"""
指标 - 字段关联实体模块

本模块定义指标与字段之间关联关系的数据结构，用于存储指标计算涉及的字段。

功能说明：
1. 使用 dataclass 定义指标 - 字段关联的实体
2. 记录指标计算需要哪些字段
3. 支持复合指标（涉及多个字段）

数据结构：
- column_id: 字段 ID（如 "fact_order.sales_amount"）
- metric_id: 指标 ID（如 "sales_amount", "profit_margin"）

什么是关联关系：
- 一个指标可能涉及多个字段
  例："利润率" 需要 "sales_amount" 和 "cost_amount" 两个字段
- 一个字段可能参与多个指标
  例："sales_amount" 可用于 "销售额"、"毛利率"、"客单价" 等指标

示例：
    # 销售额指标（单一字段）
    ColumnMetric(column_id="fact_order.sales_amount", metric_id="sales_amount")
    
    # 利润率指标（多个字段）
    ColumnMetric(column_id="fact_order.sales_amount", metric_id="profit_margin")
    ColumnMetric(column_id="fact_order.cost_amount", metric_id="profit_margin")

在智能问数中的作用：
- 快速定位：给定指标，快速找到相关字段
- SQL 生成：LLM 根据关联字段构建计算逻辑
- 指标解析：识别复合指标涉及的所有字段

数据来源：
- 从 metric_info.relevant_columns 自动推导
- build_meta_knowledge.py 批量导入

使用方法：
    # 创建关联关系
    relation = ColumnMetric(
        column_id="fact_order.sales_amount",
        metric_id="sales_amount"
    )
"""
from dataclasses import dataclass

@dataclass
class ColumnMetric:
    column_id: str
    metric_id: str
