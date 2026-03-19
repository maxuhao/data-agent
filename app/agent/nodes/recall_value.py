"""
字段取值召回节点模块

本模块实现维度字段具体取值的检索功能，用于识别用户查询中提到的具体值（如地区名、产品名等）。

功能说明：
1. 使用 LLM 扩展关键词，生成可能的字段取值表述
2. 在 Elasticsearch 中进行全文检索，匹配维度字段的实际取值
3. 返回匹配的取值信息列表，包括字段名、取值示例、出现频次等

与 recall_column 的区别：
- recall_column: 查找数据库中的字段/列名（column name）
- recall_value: 查找字段的具体取值（column value）
  
技术栈：
- Elasticsearch: 全文搜索引擎，适合模糊匹配和同义词扩展
- LLM 关键词扩展：处理口语化表达和缩写

典型应用场景：
- 用户提到 "北京" → 匹配 dim_region.region_name = '北京'
- 用户提到 "华为" → 匹配 dim_company.company_name = '华为技术有限公司'
- 用户提到 "Q1" → 匹配 dim_date.quarter = '第一季度'

处理流程：
1. 从 state 获取关键词列表
2. 使用 LLM 扩展（如 "北京" → ["北京市", "华北", "首都"]）
3. 对每个关键词在 ES 中搜索匹配的取值
4. 去重并返回

示例：
    输入：keywords = ["华为", "北京"]
    LLM 扩展：result = ["华为技术", "华为公司", "北京市", "首都"]
    ES 搜索：
    - "华为" → ValueInfo(field="company_name", value="华为技术有限公司", count=1000)
    - "北京" → ValueInfo(field="region_name", value="北京市", count=5000)
    
    输出：retrieved_value_infos = [ValueInfo(...), ValueInfo(...)]

为什么需要单独召回取值：
- 字段名 vs 取值：用户说 "华为" 而非 "company_name"
- 模糊匹配："华为" 可能对应 "华为技术"、"华为终端" 等
- 消歧义：帮助理解多义词

在 LangGraph 中的位置：
    extract_keywords → recall_value → merge_retrieved_info
"""
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "召回字段取值"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        query = state["query"]
        keywords = state["keywords"]
        value_es_repository = runtime.context["value_es_repository"]

        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"), input_variables=["query"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)

        value_infos_map: dict[str, ValueInfo] = {}
        for keyword in keywords:
            current_value_infos: list[ValueInfo] = await value_es_repository.search(keyword)
            for current_value_info in current_value_infos:
                if current_value_info.id not in value_infos_map:
                    value_infos_map[current_value_info.id] = current_value_info

        retrieved_value_infos: list[ValueInfo] = list(value_infos_map.values())
        logger.info(f"Recalled value infos: {list(value_infos_map.keys())}")
        writer({"type": "progress", "step": step, "status": "success"})
        return {"retrieved_value_infos": retrieved_value_infos}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
