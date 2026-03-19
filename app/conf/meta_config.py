"""
元知识配置模块

本模块定义 meta_config.yaml 配置文件的结构，用于描述表、字段、指标等元数据的配置信息。

功能说明：
1. 使用 dataclass 定义配置文件的强类型结构
2. 支持 Optional 类型（可为空的配置项）
3. 通过 OmegaConf 进行配置验证和加载

配置类说明：
【ColumnConfig - 字段配置】
- name: 字段名称（数据库列名）
- role: 字段角色（primary_key, foreign_key, measure, dimension）
- description: 字段业务描述（中文说明）
- alias: 字段别名列表（同义词）
- sync: 是否同步到 ES（用于维度取值检索）

【TableConfig - 表配置】
- name: 表名称（数据库表名）
- role: 表类型（fact: 事实表，dim: 维度表）
- description: 表业务描述
- columns: 字段配置列表（ColumnConfig）

【MetricConfig - 指标配置】
- name: 指标名称（业务术语）
- description: 指标描述（计算公式、统计口径）
- relevant_columns: 相关字段 ID 列表（计算该指标需要的字段）
- alias: 指标别名列表（同义词）

【MetaConfig - 根配置】
- tables: 表配置列表（可选）
- metrics: 指标配置列表（可选）

配置文件示例（meta_config.yaml）：
    tables:
      - name: fact_order
        role: fact
        description: 订单事实表
        columns:
          - name: order_id
            role: primary_key
            description: 订单编号
            alias: ["订单号", "单据号"]
            sync: false
          - name: sales_amount
            role: measure
            description: 订单销售金额
            alias: ["销售额", "营收"]
            sync: false
          - name: region_name
            role: dimension
            description: 销售地区
            alias: ["地区", "区域"]
            sync: true  # 同步到 ES，支持模糊匹配
    
    metrics:
      - name: sales_amount
        description: 订单销售金额总和，不含税
        relevant_columns: ["fact_order.sales_amount"]
        alias: ["销售额", "营收", "收入"]
      
      - name: profit_margin
        description: 利润占销售额的百分比
        relevant_columns: ["fact_order.sales_amount", "fact_order.cost_amount"]
        alias: ["毛利率", "利润率", "盈利比率"]

为什么需要配置类：
- 类型安全：编译时类型检查
- 配置验证：OmegaConf 自动验证配置格式
- IDE 友好：自动补全和错误提示
- 文档化：清晰的字段说明便于理解

使用方法：
    from omegaconf import OmegaConf
    from app.conf.meta_config import MetaConfig
    
    # 加载并验证配置
    context = OmegaConf.load("conf/meta_config.yaml")
    schema = OmegaConf.structured(MetaConfig)
    meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
    
    # 访问配置
    for table in meta_config.tables:
        print(f"表：{table.name}, 类型：{table.role}")
        for column in table.columns:
            print(f"  字段：{column.name}, 角色：{column.role}")
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnConfig:
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool


@dataclass
class TableConfig:
    name: str
    role: str
    description: str
    columns: list[ColumnConfig]


@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


@dataclass
class MetaConfig:
    tables: Optional[list[TableConfig]] = None
    metrics: Optional[list[MetricConfig]] = None
