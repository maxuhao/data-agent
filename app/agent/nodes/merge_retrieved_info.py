"""
信息合并节点模块

本模块实现将三个召回源（字段、指标、取值）的信息进行整合和结构化，为后续过滤和 SQL 生成做准备。

功能说明：
1. 合并来自 recall_column、recall_metric、recall_value 的信息
2. 补充关联信息：
   - 根据指标的相关字段，补充缺失的列信息
   - 根据取值的列 ID，补充对应的列信息并添加示例值
3. 按表分组：将字段信息组织成表结构
4. 补充关键字段：自动添加主键、外键等关键列
5. 转换为状态格式：ColumnInfo → ColumnInfoState，MetricInfo → MetricInfoState

为什么需要合并：
- 信息孤岛：三个召回节点独立工作，信息分散
- 上下文完整性：SQL 生成需要完整的表结构和字段关系
- 消除冗余：同一字段可能被多次召回，需要去重

处理流程：
1. 建立字段 ID 映射表
2. 遍历指标信息，补充相关字段（如果缺失）
3. 遍历取值信息，补充对应字段并添加示例值
4. 按表 ID 分组字段，构建表结构
5. 查询并添加关键字段（主键、外键）
6. 从数据库查询表的元数据（名称、描述、角色）
7. 组装成 TableInfoState 和 MetricInfoState

示例：
    输入：
    - retrieved_column_infos: [dim_region.region_name, dim_region.region_id]
    - retrieved_metric_infos: [MetricInfo("销售额", relevant_columns=["fact_order.sales_amount", "fact_order.order_id"])]
    - retrieved_value_infos: [ValueInfo("北京", column_id="dim_region.region_name")]
    
    合并后：
    - 补充 fact_order.order_id（因为指标需要）
    - 在 dim_region.region_name.examples 中添加 "北京"
    - 补充 dim_region.region_id（主键）
    
    输出：
    - table_infos: [
        TableInfoState(name="dim_region", columns=[region_name, region_id]),
        TableInfoState(name="fact_order", columns=[sales_amount, order_id])
      ]
    - metric_infos: [MetricInfoState(name="销售额", ...)]

在 LangGraph 中的位置：
    [recall_column, recall_value, recall_metric] → merge_retrieved_info → [filter_table, filter_metric]
"""
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, MetricInfoState, ColumnInfoState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "合并召回信息"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        retrieved_column_infos: list[ColumnInfo] = state["retrieved_column_infos"]
        retrieved_metric_infos: list[MetricInfo] = state["retrieved_metric_infos"]
        retrieved_value_infos: list[ValueInfo] = state["retrieved_value_infos"]

        meta_mysql_repository = runtime.context["meta_mysql_repository"]

        retrieved_column_infos_map: dict[str, ColumnInfo] = {
            retrieved_column_info.id: retrieved_column_info for retrieved_column_info in retrieved_column_infos
        }
        for retrieved_metric_info in retrieved_metric_infos:
            for relevant_column in retrieved_metric_info.relevant_columns:
                if relevant_column not in retrieved_column_infos_map:
                    column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(relevant_column)
                    retrieved_column_infos_map[relevant_column] = column_info

        for retrieved_value_info in retrieved_value_infos:
            value = retrieved_value_info.value
            column_id = retrieved_value_info.column_id
            if column_id not in retrieved_column_infos_map:
                column_info = await meta_mysql_repository.get_column_info_by_id(column_id)
                retrieved_column_infos_map[column_id] = column_info
            if value not in retrieved_column_infos_map[column_id].examples:
                retrieved_column_infos_map[column_id].examples.append(value)

        table_to_columns_map: dict[str, list[ColumnInfo]] = {}
        for column_info in retrieved_column_infos_map.values():
            table_id = column_info.table_id
            if table_id not in table_to_columns_map:
                table_to_columns_map[table_id] = []
            table_to_columns_map[table_id].append(column_info)

        for table_id in table_to_columns_map.keys():
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_columns_by_table_id(table_id)
            column_ids = [column_info.id for column_info in table_to_columns_map[table_id]]
            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_to_columns_map[table_id].append(key_column)

        table_infos: list[TableInfoState] = []
        for table_id, column_infos in table_to_columns_map.items():
            table_info: TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            columns = [
                ColumnInfoState(
                    name=column_info.name,
                    type=column_info.type,
                    role=column_info.role,
                    examples=column_info.examples,
                    description=column_info.description,
                    alias=column_info.alias,
                )
                for column_info in column_infos
            ]
            table_info_state = TableInfoState(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                columns=columns,
            )
            table_infos.append(table_info_state)

        metric_infos: list[MetricInfoState] = [
            MetricInfoState(
                name=retrieved_metric_info.name,
                description=retrieved_metric_info.description,
                relevant_columns=retrieved_metric_info.relevant_columns,
                alias=retrieved_metric_info.alias,
            )
            for retrieved_metric_info in retrieved_metric_infos
        ]

        writer({"type": "progress", "step": step, "status": "success"})
        return {
            "table_infos": table_infos,
            "metric_infos": metric_infos,
        }
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
