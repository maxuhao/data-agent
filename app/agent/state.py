"""
智能问数 Agent 的状态定义模块

本模块使用 TypedDict 定义了 LangGraph 工作流中传递的状态数据结构，确保类型安全和数据一致性。

状态分类：
1. 基础状态类（用于结构化存储）：
   - MetricInfoState: 指标信息状态（名称、描述、相关字段、别名）
   - ColumnInfoState: 字段信息状态（名称、类型、角色、示例、描述、别名）
   - TableInfoState: 表信息状态（名称、角色、描述、字段列表）
   - DateInfoState: 日期信息状态（日期、星期、季度）
   - DBInfoState: 数据库信息状态（方言、版本）

2. 核心状态类：
   - DataAgentState: Agent 工作流的完整状态，包含所有节点共享的数据
     * 输入：query (用户查询)
     * 中间状态：keywords, retrieved_*_infos, table_infos, metric_infos, date_info, db_info
     * 输出：sql (生成的 SQL), error (错误信息)

设计考虑：
- 使用 TypedDict 而非 dataclass，因为 LangGraph 内部将状态作为字典处理
- 支持部分更新：每个节点只需返回需要更新的字段
- 类型检查：在编译时检测字段类型错误和拼写错误

示例用法：
    state: DataAgentState = {
        "query": "统计华北地区销售额",
        "keywords": ["华北", "销售"],
        "retrieved_column_infos": [...],
        "sql": "SELECT SUM(sales) FROM fact_order WHERE region='华北'",
        "error": None
    }
"""
from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str


class DataAgentState(TypedDict):
    query: str  # 用户输入的查询
    keywords: list[str]  # 抽取的关键词

    retrieved_column_infos: list[ColumnInfo]  # 检索到的字段信息
    retrieved_metric_infos: list[MetricInfo]  # 检索到的指标信息
    retrieved_value_infos: list[ValueInfo]  # 检索到的取值信息

    table_infos: list[TableInfoState]  # 表信息
    metric_infos: list[MetricInfoState]  # 指标信息

    date_info: DateInfoState  # 日期信息
    db_info: DBInfoState  # 数据库信息

    sql: str  # 生成的SQL

    error: str  # 校验SQL时出现的错误信息
