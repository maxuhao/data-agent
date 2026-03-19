"""
字段信息实体模块

本模块定义数据库字段的完整信息结构，用于在系统各层之间传递字段元数据。

功能说明：
1. 使用 dataclass 定义不可变的字段信息数据结构
2. 包含字段的完整元数据（名称、类型、角色、示例等）
3. 支持字段别名，增强语义理解

字段角色说明：
- primary_key: 主键字段（如 id, order_id）
- foreign_key: 外键字段（如 region_id, product_id）
- measure: 度量字段（可聚合的数值，如 sales_amount, quantity）
- dimension: 维度字段（用于分组/过滤，如 region_name, date）

数据结构：
- id: 全局唯一标识（格式："表名。字段名"，如 "fact_order.sales_amount"）
- name: 字段物理名称（数据库中的列名）
- type: 数据类型（varchar, int, decimal, date 等）
- role: 字段角色（primary_key, foreign_key, measure, dimension）
- examples: 取值示例列表（用于帮助 LLM 理解字段含义）
- description: 字段业务描述（中文说明）
- alias: 字段别名列表（同义词，如 "销售额" = ["营收", "销售收入"]）
- table_id: 所属表的标识

为什么需要实体类：
- 数据传输：在 Repository、Service、Agent 之间传递结构化数据
- 类型安全：dataclass 提供编译时类型检查
- 序列化友好：可以轻松转换为 JSON/YAML
- 文档化：清晰的字段说明便于理解和使用

数据来源：
- 元数据库 (meta_mysql): 表结构定义
- 向量检索 (Qdrant): 语义匹配的字段信息
- 人工标注：业务描述和别名

使用方法：
    # 创建字段信息实例
    column = ColumnInfo(
        id="fact_order.sales_amount",
        name="sales_amount",
        type="decimal(10,2)",
        role="measure",
        examples=[100.50, 2000.00, 50000.00],
        description="订单销售金额（不含税）",
        alias=["销售额", "营收", "收入"],
        table_id="fact_order"
    )
    
    # 访问字段
    print(column.name)  # "sales_amount"
    print(f"{column.table_id}.{column.name}")  # "fact_order.sales_amount"
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class ColumnInfo:
    id: str
    name: str
    type: str
    role: str
    examples: list[Any]
    description: str
    alias: list[str]
    table_id: str
