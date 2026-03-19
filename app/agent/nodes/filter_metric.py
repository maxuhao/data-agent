"""
指标信息过滤节点模块

本模块实现基于用户查询的相关性过滤，从召回的指标信息中筛选出真正需要的业务指标。

功能说明：
1. 使用 LLM 理解用户查询的业务意图
2. 让 LLM 判断哪些预定义指标与查询相关
3. 只保留相关指标，避免指标滥用
4. 输出过滤后的指标信息列表

为什么需要过滤指标：
- 指标爆炸：可能召回多个相似指标（销售额、销售收入、营收）
- 口径统一：同一业务概念可能有多个指标定义
- 简化 SQL: 只包含必要的指标计算逻辑
- 避免混淆：过多指标会干扰 SQL 生成

与 filter_table 的关系：
- 并行执行：两个过滤节点独立工作
- 不同类型：一个过滤表结构，一个过滤业务指标
- 共同目标：精简上下文，提高准确性

处理流程：
1. 准备输入：用户查询 + 所有指标信息（YAML 格式）
2. 构建 Prompt：加载 filter_metric_info 模板
3. LLM 判断：哪些指标名称与查询匹配
4. 解析结果：LLM 返回 ["指标名 1", "指标名 2"]
5. 过滤指标：只保留被选中的指标

示例：
    输入：
    - query = "分析华北地区的销售情况"
    - metric_infos = [
        {name: "销售额", description: "..."},
        {name: "销售利润率", description: "..."},
        {name: "订单量", description: "..."},
        {name: "客单价", description: "..."}  # 不直接相关
      ]
    
    LLM 输出：
    - result = ["销售额", "销售利润率"]
    
    过滤后：
    - filtered_metric_infos = [
        {name: "销售额", ...},
        {name: "销售利润率", ...}
      ]

在 LangGraph 中的位置：
    merge_retrieved_info → filter_metric → add_extra_context
"""
import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "过滤指标信息"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        query = state["query"]
        metric_infos: list[MetricInfoState] = state["metric_infos"]

        prompt = PromptTemplate(template=load_prompt("filter_metric_info"), input_variables=["query", "metric_infos"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {"query": query, "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)}
        )
        filtered_metric_infos = [metric_info for metric_info in metric_infos if metric_info["name"] in result]

        logger.info(
            f"Filtered metric infos: {[filtered_metric_info['name'] for filtered_metric_info in filtered_metric_infos]}"
        )
        writer({"type": "progress", "step": step, "status": "success"})
        return {"metric_infos": filtered_metric_infos}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
