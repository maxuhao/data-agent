"""
字段信息召回节点模块

本模块实现基于关键词的数据库字段信息检索功能，通过向量相似度匹配相关字段。

功能说明：
1. 使用 LLM 扩展关键词：通过提示词工程生成更多相关词汇
2. 对每个关键词进行向量嵌入（Embedding）
3. 在 Qdrant 向量数据库中搜索最相似的字段信息
4. 去重并返回所有匹配的字段列表

技术栈：
- LangChain: 构建 LLM 链式调用（Prompt → LLM → OutputParser）
- Qdrant: 向量数据库，存储字段的向量化表示
- BGE Embedding: 中文语义向量化模型
- JsonOutputParser: 解析 LLM 输出的 JSON 格式结果

处理流程：
1. 从 state 获取关键词列表和原始查询
2. 使用 LLM 扩展关键词（如 "销售" → ["销售额", "营收", "收入"]）
3. 对每个关键词计算向量表示
4. 在 Qdrant 中搜索 Top-K 相似字段
5. 去重（基于字段 ID）并返回

示例：
    输入：keywords = ["销售", "华北地区"]
    LLM 扩展：result = ["销售额", "区域", "地区"]
    扩展后：keywords = ["销售", "华北地区", "销售额", "区域", "地区"]
    
    向量搜索：
    - "销售" → fact_order.sales_amount, dim_product.sales_qty
    - "华北地区" → dim_region.region_name (where region='华北')
    
    输出：retrieved_column_infos = [ColumnInfo(...), ColumnInfo(...)]

为什么需要扩展关键词：
- 用户表达多样："销售额"、"营收"、"销售收入"可能指同一概念
- 提高召回率：避免遗漏相关字段
- 语义鸿沟：用户用语 vs 数据库命名

在 LangGraph 中的位置：
    extract_keywords → recall_column → merge_retrieved_info
"""
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "召回字段信息"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        keywords = state["keywords"]
        query = state["query"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]
        embedding_client = runtime.context["embedding_client"]

        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_column_recall"), input_variables=["query"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)

        column_info_map: dict[str, ColumnInfo] = {}
        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            current_column_infos: list[ColumnInfo] = await column_qdrant_repository.search(embedding)
            for column_info in current_column_infos:
                if column_info.id not in column_info_map:
                    column_info_map[column_info.id] = column_info
        retrieved_column_infos: list[ColumnInfo] = list(column_info_map.values())

        logger.info(f"Recalled column infos: {list(column_info_map.keys())}")
        writer({"type": "progress", "step": step, "status": "success"})
        return {"retrieved_column_infos": retrieved_column_infos}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
