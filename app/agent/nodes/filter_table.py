"""
表信息过滤节点模块

本模块实现基于用户查询的相关性过滤，从召回的表信息中筛选出真正需要的表和字段。

功能说明：
1. 使用 LLM 理解用户查询意图和表结构信息
2. 让 LLM 判断哪些表和字段与查询相关
3. 只保留相关的表和字段，减少上下文噪声
4. 输出过滤后的表信息列表

为什么需要过滤：
- 召回过宽：向量检索可能召回不相关的表（宁可多召，不可遗漏）
- 上下文长度限制：LLM 有 token 限制，需要精简输入
- 提高准确性：减少无关信息干扰，提升 SQL 生成质量
- 性能优化：后续处理只需要关注相关表

技术实现：
- YAML 序列化：将表结构转换为 LLM 可读的格式
- Prompt Engineering: 设计专门的过滤提示词
- JSON 解析：解析 LLM 返回的过滤结果

处理流程：
1. 准备输入：用户查询 + 所有表信息（YAML 格式）
2. 构建 Prompt：加载 filter_table_info 模板
3. LLM 推理：判断每个表/字段的相关性
4. 解析结果：LLM 返回 {"表名": ["字段 1", "字段 2"]}
5. 过滤表信息：只保留被选中的表和字段

示例：
    输入：
    - query = "统计华北地区的销售额"
    - table_infos = [
        {name: "dim_region", columns: ["region_id", "region_name", "province"]},
        {name: "fact_order", columns: ["order_id", "sales_amount", "cost"]},
        {name: "dim_product", columns: ["product_id", "product_name"]}  # 不相关
      ]
    
    LLM 输出：
    - result = {
        "dim_region": ["region_name"],
        "fact_order": ["sales_amount"]
      }
    
    过滤后：
    - filtered_table_infos = [
        {name: "dim_region", columns: ["region_name"]},
        {name: "fact_order", columns: ["sales_amount"]}
      ]

在 LangGraph 中的位置：
    merge_retrieved_info → filter_table → add_extra_context
"""
import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "过滤表信息"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        query = state["query"]
        table_infos: list[TableInfoState] = state["table_infos"]

        prompt = PromptTemplate(template=load_prompt("filter_table_info"), input_variables=["query", "table_infos"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {"query": query, "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False)}
        )

        filtered_table_infos: list[TableInfoState] = []
        for table_info in table_infos:
            if table_info["name"] in result:
                table_info["columns"] = [
                    column_info
                    for column_info in table_info["columns"]
                    if column_info["name"] in result[table_info["name"]]
                ]
                filtered_table_infos.append(table_info)

        logger.info(
            f"Filtered table infos: {[filtered_table_info['name'] for filtered_table_info in filtered_table_infos]}"
        )
        writer({"type": "progress", "step": step, "status": "success"})
        return {"table_infos": filtered_table_infos}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
