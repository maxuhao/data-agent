"""
表信息实体模块

本模块定义数据库表的完整信息结构，用于在系统各层之间传递表元数据。

功能说明：
1. 使用 dataclass 定义不可变的表信息数据结构
2. 包含表的完整元数据（名称、类型、描述）
3. 支持表类型标识（事实表/维度表）

数据结构：
- id: 全局唯一标识（如 "fact_order", "dim_region"）
- name: 表名称（数据库中的表名）
- role: 表类型
  * fact: 事实表（存储业务数据，如订单、销售）
  * dim: 维度表（存储参考数据，如地区、产品）
- description: 表描述（中文业务说明）

表类型说明：
【事实表（fact）】
- 存储业务过程的记录
- 通常是数值型、可聚合
- 例：fact_order（订单表）、fact_sales（销售表）
- 字段：order_id, sales_amount, quantity, date_id

【维度表（dim）】
- 存储业务实体的属性
- 通常是字符串、用于分组/过滤
- 例：dim_region（地区表）、dim_product（产品表）
- 字段：region_id, region_name, province, city

为什么需要实体类：
- 数据传输：在 Repository、Service、Agent 之间传递结构化数据
- 类型安全：dataclass 提供编译时类型检查
- 序列化友好：可以轻松转换为 JSON/YAML
- 文档化：清晰的字段说明便于理解和使用

数据来源：
- 元数据库 (meta_mysql): 表结构定义
- 向量检索 (Qdrant): 语义匹配的表信息
- 人工标注：业务描述和类型

使用方法：
    # 创建表信息实例
    table = TableInfo(
        id="fact_order",
        name="fact_order",
        role="fact",
        description="订单事实表，包含所有订单交易记录，用于分析销售趋势"
    )
    
    # 访问字段
    print(f"{table.name}: {table.description}")
    print(f"表类型：{table.role}")
"""
from dataclasses import dataclass

@dataclass
class TableInfo:
    id: str
    name: str
    role: str
    description: str
