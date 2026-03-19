"""
智能问数 Agent 的工作流定义模块

本模块定义了基于 LangGraph 的智能问数系统核心工作流程，实现从自然语言查询到 SQL 执行的完整自动化处理。

主要功能：
1. 构建 StateGraph 状态图，定义 12 个处理节点和它们之间的执行顺序
2. 实现多阶段信息检索：关键词提取 → 列/值/指标召回 → 信息合并
3. 实现 SQL 生成与验证循环：生成 → 验证 → 修正（如有错误）→ 执行
4. 支持流式输出，可实时反馈每个节点的处理结果

工作流程：
    START → extract_keywords → [recall_column, recall_value, recall_metric] 
           → merge_retrieved_info → [filter_table, filter_metric] 
           → add_extra_context → generate_sql → validate_sql 
           → {正确：run_sql → END | 错误：correct_sql → run_sql → END}

节点说明：
- extract_keywords: 从用户查询中提取关键词
- recall_column/value/metric: 并行召回相关的字段、取值和指标信息
- merge_retrieved_info: 合并所有检索到的信息
- filter_table/metric: 过滤出相关的表和指标
- add_extra_context: 添加额外的上下文信息（如日期、数据库方言等）
- generate_sql: 根据收集的信息生成 SQL 查询
- validate_sql: 验证 SQL 语法和语义是否正确
- correct_sql: 如果验证失败，修正 SQL
- run_sql: 执行 SQL 并返回结果

使用方法：
    from app.agent.graph import graph
    async for chunk in graph.astream(input=state, context=context):
        print(chunk)
"""
import asyncio

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.run_sql import run_sql
from app.agent.nodes.validate_sql import validate_sql
from app.agent.state import DataAgentState
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

graph_builder = StateGraph(state_schema=DataAgentState, context_schema=DataAgentContext)
graph_builder.add_node("extract_keywords", extract_keywords)
graph_builder.add_node("recall_column", recall_column)
graph_builder.add_node("recall_value", recall_value)
graph_builder.add_node("recall_metric", recall_metric)
graph_builder.add_node("merge_retrieved_info", merge_retrieved_info)
graph_builder.add_node("filter_metric", filter_metric)
graph_builder.add_node("filter_table", filter_table)
graph_builder.add_node("add_extra_context", add_extra_context)
graph_builder.add_node("generate_sql", generate_sql)
graph_builder.add_node("validate_sql", validate_sql)
graph_builder.add_node("correct_sql", correct_sql)
graph_builder.add_node("run_sql", run_sql)

graph_builder.add_edge(START, "extract_keywords")
graph_builder.add_edge("extract_keywords", "recall_column")
graph_builder.add_edge("extract_keywords", "recall_value")
graph_builder.add_edge("extract_keywords", "recall_metric")
graph_builder.add_edge("recall_column", "merge_retrieved_info")
graph_builder.add_edge("recall_value", "merge_retrieved_info")
graph_builder.add_edge("recall_metric", "merge_retrieved_info")
graph_builder.add_edge("merge_retrieved_info", "filter_table")
graph_builder.add_edge("merge_retrieved_info", "filter_metric")
graph_builder.add_edge("filter_table", "add_extra_context")
graph_builder.add_edge("filter_metric", "add_extra_context")
graph_builder.add_edge("add_extra_context", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")

graph_builder.add_conditional_edges(source="validate_sql",
                                    path=lambda state: "run_sql" if state['error'] is None else "correct_sql",
                                    path_map={"run_sql": "run_sql", "correct_sql": "correct_sql"})
graph_builder.add_edge("correct_sql", "run_sql")
graph_builder.add_edge("run_sql", END)

graph = graph_builder.compile()

# print(graph.get_graph().draw_mermaid())

if __name__ == '__main__':
    async def test():

        qdrant_client_manager.init()
        embedding_client_manager.init()
        es_client_manager.init()
        meta_mysql_client_manager.init()
        dw_mysql_client_manager.init()

        async with meta_mysql_client_manager.session_factory() as meta_session, dw_mysql_client_manager.session_factory() as dw_session:
            meta_mysql_repository = MetaMySQLRepository(meta_session)
            dw_mysql_repository = DWMySQLRepository(dw_session)

            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
            metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)
            value_es_repository = ValueESRepository(es_client_manager.client)

            state = DataAgentState(query="统计华北地区的销售总额")
            context = DataAgentContext(column_qdrant_repository=column_qdrant_repository,
                                       embedding_client=embedding_client_manager.client,
                                       metric_qdrant_repository=metric_qdrant_repository,
                                       value_es_repository=value_es_repository,
                                       meta_mysql_repository=meta_mysql_repository,
                                       dw_mysql_repository=dw_mysql_repository)
            async for chunk in graph.astream(input=state, context=context, stream_mode='custom'):
                print(chunk)

        await qdrant_client_manager.close()
        await es_client_manager.close()
        await meta_mysql_client_manager.close()
        await dw_mysql_client_manager.close()


    asyncio.run(test())
