"""
SQL 执行节点模块

本模块实现最终 SQL 的执行并返回查询结果，是智能问数流程的最后一个环节。

功能说明：
1. 从 state 获取经过验证的正确 SQL
2. 调用数据仓库 Repository 执行 SQL
3. 将执行结果通过流式输出返回给前端
4. 记录执行日志

输出类型：
- progress: 进度更新（"运行 SQL" - running/success/error）
- result: 实际查询结果（JSON 格式的行列数据）

为什么没有返回值：
- 直接通过 writer 输出结果到流
- 避免重复序列化（结果已经在 writer 中）
- 符合 LangGraph 的流式响应模式

处理流程：
1. 提取 state 中的 SQL
2. 调用 dw_mysql_repository.run(sql) 执行
3. 记录成功日志
4. 发送 success 进度更新
5. 发送 result 数据包（包含查询结果）
6. 如果出错，发送 error 进度更新并抛出异常

示例：
    输入：sql = "SELECT SUM(sales_amount) AS total_sales FROM fact_order WHERE region_id = 1"
    
    输出：
    - writer({"type": "progress", "step": "运行 SQL", "status": "running"})
    - result = [{"total_sales": 1000000.00}]
    - writer({"type": "progress", "step": "运行 SQL", "status": "success"})
    - writer({"type": "result", "data": [{"total_sales": 1000000.00}]})

在 LangGraph 中的位置：
    validate_sql (error=None) → run_sql → END
    correct_sql → run_sql → END
"""
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def run_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "运行SQL"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        sql = state["sql"]
        dw_mysql_repository = runtime.context["dw_mysql_repository"]

        result = await dw_mysql_repository.run(sql)

        logger.info(f"SQL execution result: {result}")
        writer({"type": "progress", "step": step, "status": "success"})
        writer({"type": "result", "data": result})
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
