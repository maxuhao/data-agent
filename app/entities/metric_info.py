"""
指标信息实体模块

本模块定义业务指标的完整信息结构，用于传递预定义的度量标准。

功能说明：
1. 使用 dataclass 定义业务指标的数据结构
2. 包含指标的名称、描述、相关字段和别名
3. 支持指标的同义词表达

什么是业务指标：
- 预定义的度量标准（如销售额、利润率、订单量）
- 有明确的计算逻辑和统计口径
- 可能涉及多个字段的组合计算

数据结构：
- id: 指标唯一标识（如 "sales_amount", "profit_margin"）
- name: 指标名称（中文业务术语）
- description: 指标详细描述（计算公式、统计范围等）
- relevant_columns: 相关字段 ID 列表（计算该指标需要的字段）
  示例：["fact_order.sales_amount", "fact_order.cost_amount"]
- alias: 指标别名列表（同义词）
  示例：["销售额", "营收", "销售收入"]

指标 vs 字段的区别：
- 字段 (Column): 数据库中的原始列
- 指标 (Metric): 业务层面的度量，可能由多个字段计算得出
  例："利润率" = "利润" / "销售额" * 100%

为什么需要指标信息：
- 统一口径：避免不同人对同一指标理解不一致
- 简化 SQL 生成：LLM 直接使用预定义的计算逻辑
- 业务语义层：连接技术实现和业务语言

数据来源：
- 人工配置：在元数据库中预先定义
- 向量检索：通过 Qdrant 语义匹配

使用方法：
    # 创建指标实例
    metric = MetricInfo(
        id="sales_amount",
        name="销售额",
        description="订单销售金额总和，不含税",
        relevant_columns=["fact_order.sales_amount"],
        alias=["销售额", "营收", "销售收入", "业绩"]
    )
    
    # 访问指标信息
    print(f"{metric.name}: {metric.description}")
    print(f"需要同义问法：{metric.alias}")
"""
from dataclasses import dataclass

@dataclass
class MetricInfo:
    id: str
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]
