"""
SQL 生成节点模块

本模块实现核心的自然语言到 SQL 的转换功能，是整个智能问数系统的关键环节。

功能说明：
1. 收集所有必要的上下文信息：
   - 表结构信息（过滤后的表和字段）
   - 业务指标定义（预定义的度量标准）
   - 日期信息（当前日期、季度等）
   - 数据库方言（MySQL/PostgreSQL/Oracle）
2. 构建专门的 SQL 生成 Prompt
3. 调用 LLM 生成符合语法的 SQL 查询
4. 返回生成的 SQL 语句

技术栈：
- LangChain: 构建 LLM 链式调用
- YAML 序列化：将结构化数据转换为 LLM 可读格式
- StrOutputParser: 解析 LLM 输出的纯文本 SQL
- Prompt Engineering: 设计专业的 SQL 生成提示词

为什么使用 YAML 序列化：
- 保留层级结构：表 → 字段的嵌套关系
- 可读性强：LLM 容易理解 YAML 格式
- 支持中文：allow_unicode=True 保证中文正常显示
- 排序保留：sort_keys=False 保持字段顺序

处理流程：
1. 从 state 提取所有必要信息
2. 序列化为 YAML 格式
3. 加载 generate_sql 提示词模板
4. 构建 Prompt → LLM → Parser 链
5. 调用 LLM 生成 SQL
6. 记录并返回 SQL

示例：
    输入：
    - query = "统计华北地区 2025 年的销售额"
    - table_infos = [
        {name: "dim_region", columns: [{name: "region_name", type: "varchar"}]},
        {name: "fact_order", columns: [{name: "sales_amount", type: "decimal"}, {name: "order_date", type: "date"}]}
      ]
    - metric_infos = [{name: "销售额", formula: "SUM(sales_amount)"}]
    - date_info = {date: "2026-03-15", quarter: "Q1"}
    - db_info = {dialect: "mysql", version: "8.0"}
    
    输出：
    - sql = "SELECT SUM(fo.sales_amount) AS sales_amount FROM fact_order fo JOIN dim_region dr ON fo.region_id = dr.region_id WHERE dr.region_name = '华北' AND YEAR(fo.order_date) = 2025"

在 LangGraph 中的位置：
    add_extra_context → generate_sql → validate_sql
"""
import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "生成SQL"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]
        query = state["query"]

        prompt = PromptTemplate(
            template=load_prompt("generate_sql"),
            input_variables=["table_infos", "metric_infos", "date_info", "db_info", "query"],
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
            }
        )
        logger.info(f"Generated SQL: {result}")

        writer({"type": "progress", "step": step, "status": "success"})
        return {"sql": result}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
