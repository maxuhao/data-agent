"""
指标信息召回节点模块

本模块实现业务指标的检索功能，用于识别用户查询中涉及的统计指标（如销售额、利润率、订单数等）。

功能说明：
1. 使用 LLM 扩展指标相关的关键词
2. 对每个关键词进行向量化
3. 在 Qdrant 向量数据库中搜索相似的指标定义
4. 返回匹配的指标信息列表

什么是指标（Metric）：
- 预定义的业务度量标准，有明确的计算逻辑
- 例如：销售额、订单量、客单价、毛利率、转化率等
- 与普通字段的区别：指标是派生值，字段是原始数据

为什么需要单独召回指标：
- 业务语义层：用户说 "销售额" 实际指 SUM(order.sales_amount)
- 统一口径：避免不同人对同一指标理解不一致
- 简化 SQL 生成：直接使用预定义的指标逻辑

技术栈：
- Qdrant 向量数据库：存储指标的向量化表示
- BGE Embedding: 中文语义向量化
- LLM 关键词扩展：处理同义词和业务术语

典型应用场景：
- 用户问 "销售额是多少" → 匹配预定义的 sales_amount 指标
- 用户问 "业绩怎么样" → 匹配 performance 指标集
- 用户问 "利润率" → 匹配 profit_margin = profit / revenue

处理流程：
1. 从 state 获取关键词
2. LLM 扩展（如 "销售" → ["销售额", "营收", "销售收入"]）
3. 向量化并搜索 Qdrant
4. 去重返回指标列表

示例：
    输入：keywords = ["销售", "利润"]
    LLM 扩展：result = ["销售额", "销售收入", "利润率", "毛利润"]
    向量搜索：
    - "销售额" → MetricInfo(name="销售额", formula="SUM(fact_order.sales_amount)")
    - "利润率" → MetricInfo(name="利润率", formula="profit / revenue * 100%")
    
    输出：retrieved_metric_infos = [MetricInfo(...), MetricInfo(...)]

在 LangGraph 中的位置：
    extract_keywords → recall_metric → merge_retrieved_info
"""
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "召回指标信息"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        query = state["query"]
        keywords = state["keywords"]
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repository = runtime.context["metric_qdrant_repository"]

        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_metric_recall"), input_variables=["query"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)

        metric_info_map: dict[str, MetricInfo] = {}
        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            current_metric_infos: list[MetricInfo] = await metric_qdrant_repository.search(embedding)
            for metric_info in current_metric_infos:
                if metric_info.id not in metric_info_map:
                    metric_info_map[metric_info.id] = metric_info
        retrieved_metric_infos: list[MetricInfo] = list(metric_info_map.values())

        logger.info(f"Recalled metric infos: {list(metric_info_map.keys())}")
        logger.info(f"Recalled metric infos: {list(retrieved_metric_infos)}")
        writer({"type": "progress", "step": step, "status": "success"})
        return {"retrieved_metric_infos": retrieved_metric_infos}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
