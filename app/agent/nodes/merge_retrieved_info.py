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
    """
    合并召回信息节点函数
    
    将来自 recall_column、recall_value、recall_metric 三个召回源的信息进行整合，
    为后续的表过滤和 SQL 生成提供完整的上下文信息。
    
    Args:
        state (DataAgentState): Agent 状态，包含已召回的字段、取值、指标信息
        runtime (Runtime[DataAgentContext]): 运行时上下文，提供 Repository 等依赖
    
    Returns:
        dict: 包含合并后的表信息列表和指标信息列表
        - table_infos: List[TableInfoState] 按表分组的字段信息
        - metric_infos: List[MetricInfoState] 召回的指标信息
    """
    writer = runtime.stream_writer
    step = "合并召回信息"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        # 从 state 中获取三个召回源的結果
        retrieved_column_infos: list[ColumnInfo] = state["retrieved_column_infos"]
        retrieved_metric_infos: list[MetricInfo] = state["retrieved_metric_infos"]
        retrieved_value_infos: list[ValueInfo] = state["retrieved_value_infos"]

        # ========== 输入数据日志开始 ==========
        logger.info("=" * 80)
        logger.info("【合并召回信息】输入数据")
        logger.info("=" * 80)
        
        logger.info(f"\n1. 召回的字段信息 (retrieved_column_infos) - 共 {len(retrieved_column_infos)} 条:")
        for idx, column_info in enumerate(retrieved_column_infos, 1):
            logger.info(f"  [{idx}] {column_info.id}")
            logger.info(f"      名称：{column_info.name}")
            logger.info(f"      表 ID: {column_info.table_id}")
            logger.info(f"      类型：{column_info.type}")
            logger.info(f"      角色：{column_info.role}")
            logger.info(f"      描述：{column_info.description}")
            logger.info(f"      别名：{column_info.alias}")
            logger.info(f"      示例：{column_info.examples}")
        
        logger.info(f"\n2. 召回的指标信息 (retrieved_metric_infos) - 共 {len(retrieved_metric_infos)} 条:")
        for idx, metric_info in enumerate(retrieved_metric_infos, 1):
            logger.info(f"  [{idx}] {metric_info.name}")
            logger.info(f"      描述：{metric_info.description}")
            logger.info(f"      别名：{metric_info.alias}")
            logger.info(f"      相关字段：{metric_info.relevant_columns}")
        
        logger.info(f"\n3. 召回的取值信息 (retrieved_value_infos) - 共 {len(retrieved_value_infos)} 条:")
        for idx, value_info in enumerate(retrieved_value_infos, 1):
            logger.info(f"  [{idx}] 值：{value_info.value}")
            logger.info(f"      字段 ID: {value_info.column_id}")
        
        logger.info("=" * 80)
        # ========== 输入数据日志结束 ==========
        
        # 记录初始召回的数据量
        logger.info(f"初始召回 - 字段数：{len(retrieved_column_infos)}, 指标数：{len(retrieved_metric_infos)}, 取值数：{len(retrieved_value_infos)}")
        logger.debug(f"初始字段 ID 列表：{[col.id for col in retrieved_column_infos]}")
        logger.debug(f"初始取值列表：{[(v.value, v.column_id) for v in retrieved_value_infos]}")

        # 获取元数据库 Repository，用于查询补充信息
        meta_mysql_repository = runtime.context["meta_mysql_repository"]

        # 【步骤 1】建立字段 ID 映射表，便于快速查找和去重
        retrieved_column_infos_map: dict[str, ColumnInfo] = {
            retrieved_column_info.id: retrieved_column_info for retrieved_column_info in retrieved_column_infos
        }
        
        # 【步骤 2】遍历指标信息，补充缺失的相关字段
        # 例如：如果召回了"销售额"指标，它需要 fact_order.sales_amount 字段
        # 如果该字段不在映射表中，则从数据库查询并添加
        added_columns_from_metrics = []
        for retrieved_metric_info in retrieved_metric_infos:
            for relevant_column in retrieved_metric_info.relevant_columns:
                if relevant_column not in retrieved_column_infos_map:
                    column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(relevant_column)
                    retrieved_column_infos_map[relevant_column] = column_info
                    added_columns_from_metrics.append(relevant_column)
        
        if added_columns_from_metrics:
            logger.info(f"从指标补充字段：{added_columns_from_metrics}")

        # 【步骤 3】遍历取值信息，补充对应字段并添加示例值
        # 例如：如果召回了 ValueInfo(value="华北", column_id="dim_region.region_name")
        # 则需要：
        # 1. 确保 dim_region.region_name 字段在映射表中
        # 2. 将"华北"添加到该字段的 examples 列表中
        added_examples = []
        for retrieved_value_info in retrieved_value_infos:
            value = retrieved_value_info.value
            column_id = retrieved_value_info.column_id
            # 如果字段不存在，从数据库查询
            if column_id not in retrieved_column_infos_map:
                column_info = await meta_mysql_repository.get_column_info_by_id(column_id)
                retrieved_column_infos_map[column_id] = column_info
                logger.info(f"从取值信息补充新字段：{column_id}")
            # 将取值添加到示例列表（去重）
            if value not in retrieved_column_infos_map[column_id].examples:
                retrieved_column_infos_map[column_id].examples.append(value)
                added_examples.append((column_id, value))
        
        if added_examples:
            logger.info(f"添加取值示例：{added_examples}")

        # 【步骤 4】按表 ID 分组字段，构建表结构
        # 将扁平的字段列表组织成 {表 ID: [字段列表]} 的结构
        table_to_columns_map: dict[str, list[ColumnInfo]] = {}
        for column_info in retrieved_column_infos_map.values():
            table_id = column_info.table_id
            if table_id not in table_to_columns_map:
                table_to_columns_map[table_id] = []
            table_to_columns_map[table_id].append(column_info)
        
        logger.info(f"按表分组后 - 表数量：{len(table_to_columns_map)}, 各表字段分布：{[(tid, len(cols)) for tid, cols in table_to_columns_map.items()]}")

        # 【步骤 5】补充关键字段（主键、外键）
        # 即使这些字段没有被召回，也需要添加到表结构中，保证 SQL 生成的完整性
        added_key_columns = []
        for table_id in table_to_columns_map.keys():
            # 查询该表的所有主键和外键
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_columns_by_table_id(table_id)
            # 获取当前已有的字段 ID 列表
            column_ids = [column_info.id for column_info in table_to_columns_map[table_id]]
            # 如果关键列不在当前列表中，则添加
            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_to_columns_map[table_id].append(key_column)
                    added_key_columns.append(f"{table_id}.{key_column.name}({key_column.role})")
        
        if added_key_columns:
            logger.info(f"补充关键字段：{added_key_columns}")

        # 【步骤 6】构建 TableInfoState 对象列表
        # 从数据库查询表的元数据（名称、描述、角色），并转换为状态格式
        table_infos: list[TableInfoState] = []
        for table_id, column_infos in table_to_columns_map.items():
            # 查询表的元数据
            table_info: TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            # 将 ColumnInfo 转换为 ColumnInfoState（注意：TypedDict 使用字典字面量）
            columns = [
                {
                    "name": column_info.name,
                    "type": column_info.type,
                    "role": column_info.role,
                    "examples": column_info.examples,
                    "description": column_info.description,
                    "alias": column_info.alias,
                }
                for column_info in column_infos
            ]
            # 构建表信息状态对象（注意：TypedDict 使用字典字面量）
            table_info_state: TableInfoState = {
                "name": table_info.name,
                "role": table_info.role,
                "description": table_info.description,
                "columns": columns,
            }
            table_infos.append(table_info_state)
        
        logger.info(f"最终生成表信息：{len(table_infos)}个表")
        for table_info in table_infos:
            logger.info(f"表 '{table_info['name']}' ({table_info['role']}): {[col['name'] for col in table_info['columns']]}")
            for col in table_info['columns']:
                if col['examples']:
                    logger.info(f"  - 字段 '{col['name']}' examples: {col['examples'][:3]}...")  # 只显示前 3 个示例

        # 【步骤 7】转换 MetricInfo 为 MetricInfoState
        # 保持召回的指标信息，供后续过滤和 SQL 生成使用
        metric_infos: list[MetricInfoState] = [
            {
                "name": retrieved_metric_info.name,
                "description": retrieved_metric_info.description,
                "relevant_columns": retrieved_metric_info.relevant_columns,
                "alias": retrieved_metric_info.alias,
            }
            for retrieved_metric_info in retrieved_metric_infos
        ]
        
        logger.info(f"最终生成指标信息：{len(metric_infos)}个指标")
        for metric_info in metric_infos:
            logger.info(f"指标 '{metric_info['name']}': 相关字段={metric_info['relevant_columns']}")

        # ========== 输出数据详细日志开始 ==========
        logger.info("=" * 80)
        logger.info("【合并召回信息】输出数据 - 详细结构")
        logger.info("=" * 80)
        
        logger.info(f"\n1. 表信息列表 (table_infos) - 共 {len(table_infos)} 个表:")
        for idx, table_info_state in enumerate(table_infos, 1):
            logger.info(f"  [表{idx}] {table_info_state['name']}")
            logger.info(f"          角色：{table_info_state['role']}")
            logger.info(f"          描述：{table_info_state['description']}")
            logger.info(f"          字段数：{len(table_info_state['columns'])}")
            for col_idx, column in enumerate(table_info_state['columns'], 1):
                logger.info(f"            ├─ [{col_idx}] {column['name']} ({column['type']})")
                logger.info(f"            │   角色：{column['role']}")
                logger.info(f"            │   描述：{column['description']}")
                logger.info(f"            │   别名：{column['alias']}")
                logger.info(f"            └─ 示例：{column['examples'] if column['examples'] else '[]'}")
        
        logger.info(f"\n2. 指标信息列表 (metric_infos) - 共 {len(metric_infos)} 条:")
        for idx, metric_info_state in enumerate(metric_infos, 1):
            logger.info(f"  [指标{idx}] {metric_info_state['name']}")
            logger.info(f"           描述：{metric_info_state['description']}")
            logger.info(f"           别名：{metric_info_state['alias']}")
            logger.info(f"           相关字段：{metric_info_state['relevant_columns']}")
        
        logger.info("=" * 80)
        logger.info("【合并完成】输入→输出转换结束")
        logger.info("=" * 80)
        # ========== 输出数据详细日志结束 ==========

        # 标记步骤成功并返回结果
        writer({"type": "progress", "step": step, "status": "success"})
        return {
            "table_infos": table_infos,
            "metric_infos": metric_infos,
        }
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
