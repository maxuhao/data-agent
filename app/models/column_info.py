"""
字段信息模型模块

本模块定义 column_info 表的 ORM 模型，用于存储数据库字段的详细元数据。

功能说明：
1. 映射 database 中的 column_info 表
2. 存储字段的完整定义信息
3. 支持字段角色分类和别名配置

表结构说明：
- id: 字段编号（主键，格式："表名。字段名"）
- name: 字段名称（数据库列名）
- type: 数据类型（varchar, int, decimal, date 等）
- role: 字段角色
  * primary_key: 主键
  * foreign_key: 外键
  * measure: 度量字段（可聚合的数值）
  * dimension: 维度字段（用于分组/过滤）
- examples: 取值示例（JSON 数组，帮助 LLM 理解字段含义）
- description: 字段描述（中文业务说明）
- alias: 字段别名（JSON 数组，同义词列表）
- table_id: 所属表编号（外键）

字段角色详解：
【measure - 度量字段】
- 可聚合的数值型字段
- 用于 SUM, AVG, COUNT 等聚合函数
- 例：sales_amount（销售额）, quantity（数量）

【dimension - 维度字段】
- 用于分组（GROUP BY）或过滤（WHERE）
- 通常是字符串或日期类型
- 例：region_name（地区）, product_name（产品名）

【primary_key - 主键】
- 唯一标识每行记录
- 例：order_id, user_id

【foreign_key - 外键】
- 关联其他表的主键
- 例：region_id（关联 dim_region 表）

在智能问数中的作用：
- SQL 生成核心：LLM 根据字段信息构建正确的 SQL
- 语义理解：通过描述和别名理解字段业务含义
- 类型推断：确保生成的 SQL 符合数据类型要求

数据来源：
- build_meta_knowledge.py 从 DW 库自动采集
- 人工在配置文件中定义角色和别名

使用方法：
    # 查询某表的所有字段
    from app.models.column_info import ColumnInfoMySQL
    columns = await session.execute(
        select(ColumnInfoMySQL).where(ColumnInfoMySQL.table_id == "fact_order")
    )
    
    # 查询所有度量字段
    measures = await session.execute(
        select(ColumnInfoMySQL).where(ColumnInfoMySQL.role == "measure")
    )
"""
from sqlalchemy import String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class ColumnInfoMySQL(Base):
    __tablename__ = "column_info"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="列编号"
    )
    name: Mapped[str | None] = mapped_column(
        String(128),
        comment="列名称"
    )
    type: Mapped[str | None] = mapped_column(
        String(64),
        comment="数据类型"
    )
    role: Mapped[str | None] = mapped_column(
        String(32),
        comment="列类型(primary_key,foreign_key,measure,dimension)"
    )
    examples: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="数据示例"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="列描述"
    )
    alias: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="列别名"
    )
    table_id: Mapped[str | None] = mapped_column(
        String(64),
        comment="所属表编号"
    )
