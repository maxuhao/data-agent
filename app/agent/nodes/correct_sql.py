"""
SQL 校正节点模块

本模块实现对验证失败的 SQL 进行修正，是智能问数系统的自我修复机制。

功能说明：
1. 分析原始 SQL 和错误信息
2. 结合所有上下文信息（表结构、指标、日期等）
3. 让 LLM 理解错误原因并修正 SQL
4. 返回修正后的 SQL

与 generate_sql 的区别：
- generate_sql: 从零开始生成 SQL
- correct_sql: 基于已有 SQL 和错误信息进行修正
- 输入更多：包含原始 SQL 和具体错误信息
- 针对性强：明确知道哪里出错

为什么需要单独校正：
- LLM 幻觉：可能编造不存在的表/字段
- 语法错误：SQL 语法不符合数据库规范
- 逻辑错误：JOIN 条件、聚合函数使用不当
- 自纠正机制：允许系统承认错误并改正

处理流程：
1. 从 state 提取所有信息（包括错误的 SQL 和错误信息）
2. 加载 correct_sql 专用提示词
3. 构建 Prompt → LLM → Parser 链
4. 调用 LLM 修正 SQL
5. 记录并返回修正结果

示例：
    输入：
    - query = "统计华北地区的销售额"
    - sql = "SELECT SUM(sales) FROM fact_order WHERE region_name = '华北'"  # 错误：region_name 不在 fact_order 表中
    - error = "Unknown column 'region_name' in 'where clause'"
    
    修正后：
    - result = "SELECT SUM(fo.sales_amount) AS sales_amount FROM fact_order fo JOIN dim_region dr ON fo.region_id = dr.region_id WHERE dr.region_name = '华北'"
    
    改进点：
    - 添加了 JOIN dim_region
    - 使用了正确的字段名 sales_amount
    - 在正确的表上过滤 region_name

在 LangGraph 中的位置：
    validate_sql (error != None) → correct_sql → run_sql
"""
import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.context import request_id_context_var
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "校正SQL"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        table_infos = state["table_infos"] # 表信息
        metric_infos = state["metric_infos"] # 指标信息
        date_info = state["date_info"] # 日期信息
        db_info = state["db_info"] # 数据库信息
        query = state["query"] # 用户查询
        sql = state["sql"] # 生成的 SQL
        error = state["error"] # 错误信息

        prompt = PromptTemplate(
            template=load_prompt("correct_sql"), # 加载提示词
            input_variables=["table_infos", "metric_infos", "date_info", "db_info", "query", "sql", "error"], # 输入变量
        )
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {
                "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
                "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
                "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
                "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
                "query": query,
                "sql": sql,
                "error": error,
            }
        )

        logger.info(f"Corrected SQL: {result}")
        writer({"type": "progress", "step": step, "status": "success"})
        return {"sql": result}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
