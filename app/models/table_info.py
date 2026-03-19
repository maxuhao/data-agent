"""
表信息模型模块

本模块定义 table_info 表的 ORM 模型，用于存储数据库表的元数据信息。

功能说明：
1. 映射 database 中的 table_info 表
2. 存储表的物理结构定义
3. 支持表类型标识（事实表/维度表）

表结构说明：
- id: 表编号（主键）
- name: 表名称（如 "fact_order", "dim_region"）
- role: 表类型
  * fact: 事实表（存储业务数据，如订单、销售）
  * dim: 维度表（存储参考数据，如地区、产品）
- description: 表描述（中文业务说明）

在智能问数中的作用：
- 元数据管理：记录所有可用表的信息
- SQL 生成参考：LLM 根据表描述理解表用途
- 表过滤：根据表类型筛选相关表

数据来源：
- 通过 build_meta_knowledge.py 从配置文件导入
- 人工在元数据库中维护

使用方法：
    # 查询所有事实表
    from app.models.table_info import TableInfoMySQL
    fact_tables = await session.execute(
        select(TableInfoMySQL).where(TableInfoMySQL.role == "fact")
    )
    
    # 创建新表信息
    table = TableInfoMySQL(
        id="fact_order",
        name="fact_order",
        role="fact",
        description="订单事实表，包含所有订单交易记录"
    )
"""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class TableInfoMySQL(Base):
    __tablename__ = "table_info"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="表编号"
    )
    name: Mapped[str | None] = mapped_column(
        String(128),
        comment="表名称"
    )
    role: Mapped[str | None] = mapped_column(
        String(32),
        comment="表类型(fact/dim)"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="表描述"
    )
