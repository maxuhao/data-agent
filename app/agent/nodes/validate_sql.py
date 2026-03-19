"""
SQL 验证节点模块

本模块实现对生成的 SQL 进行语法验证，确保 SQL 可以在目标数据库上正确执行。

功能说明：
1. 从 state 获取生成的 SQL
2. 调用数据仓库 Repository 的 validate 方法
3. 根据验证结果返回错误信息或 None（表示成功）
4. 控制流程分支：验证通过 → run_sql，验证失败 → correct_sql

验证内容：
- 语法检查：SQL 是否符合 MySQL 语法规则
- 表存在性：引用的表是否真实存在
- 字段存在性：引用的字段是否在表中
- 权限检查：是否有访问这些表的权限
- 复杂度评估：避免过于复杂的查询

为什么需要单独验证：
- LLM 可能犯错：生成的 SQL 可能有语法错误
- 幻觉问题：LLM 可能编造不存在的表/字段
- 上下文限制：可能遗漏某些约束条件
- 安全第一：避免危险操作（如 DROP、DELETE）

处理流程：
1. 提取 state 中的 SQL
2. 尝试在数据库中 EXPLAIN 或 PREPARE 该 SQL
3. 如果成功 → error = None
4. 如果失败 → error = 错误信息
5. 返回验证结果

示例：
    输入：sql = "SELECT SUM(sales) FROM fact_order WHERE region_id = 1"
    
    验证通过：
    - return {"error": None}
    - 流程：validate_sql → run_sql
    
    验证失败：
    - return {"error": "Table 'fact_order' doesn't exist"}
    - 流程：validate_sql → correct_sql

在 LangGraph 中的位置：
    generate_sql → validate_sql → {正确：run_sql | 错误：correct_sql}
"""
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "校验SQL"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        sql = state["sql"]
        dw_mysql_repository: DWMySQLRepository = runtime.context["dw_mysql_repository"]

        try:
            await dw_mysql_repository.validate(sql)
            logger.info("SQL syntax is valid")
            writer({"type": "progress", "step": step, "status": "success"})
            return {"error": None}
        except Exception as e:
            logger.info(f"SQL syntax error: {str(e)}")
            writer({"type": "progress", "step": step, "status": "success"})
            return {"error": str(e)}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
