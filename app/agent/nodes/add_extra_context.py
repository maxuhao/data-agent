"""
额外上下文添加节点模块

本模块实现为 SQL 生成添加必要的辅助上下文信息，包括日期信息和数据库方言信息。

功能说明：
1. 获取当前日期信息：
   - 完整日期（YYYY-MM-DD）
   - 星期几（Monday, Tuesday...）
   - 季度（Q1, Q2, Q3, Q4）
2. 获取数据库方言和版本信息：
   - 数据库类型（MySQL, PostgreSQL, Oracle 等）
   - 数据库版本号
3. 将信息添加到状态中，供 SQL 生成使用

为什么需要这些上下文：
- 日期相对性：用户说 "今天"、"本周"、"上月" 需要知道当前日期
- 季度计算："Q1 销售额" 需要知道现在是哪个季度
- SQL 方言差异：不同数据库的语法、函数有差异
  - MySQL: DATE_FORMAT(), LIMIT
  - PostgreSQL: TO_CHAR(), FETCH FIRST
  - Oracle: TO_DATE(), ROWNUM

典型应用场景：
- 用户问 "今天的订单" → 需要知道今天是 2026-03-15
- 用户问 "本季度业绩" → 需要知道当前是 Q1
- 用户问 "最近 7 天" → 需要计算 date_range
- SQL 生成时需要使用正确的日期函数

处理流程：
1. 获取系统当前日期
2. 格式化为多种表示（日期字符串、星期、季度）
3. 从数据仓库读取数据库元信息
4. 封装为 DateInfoState 和 DBInfoState
5. 返回给状态

示例：
    执行时间：2026-03-15（星期日）
    
    输出：
    - date_info = {
        "date": "2026-03-15",
        "weekday": "Sunday",
        "quarter": "Q1"
      }
    - db_info = {
        "dialect": "mysql",
        "version": "8.0.35"
      }

在 LangGraph 中的位置：
    [filter_table, filter_metric] → add_extra_context → generate_sql
"""
from datetime import date

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger

# runtime 是 LangGraph 的运行时对象，包含上下文和状态
# state 是 LangGraph 的状态对象，包含输入数据、中间结果和输出数据
async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "添加额外上下文"
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        # 获取数据库信息
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        today = date.today()
        date_str = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        quarter = f"Q{(today.month - 1) // 3 + 1}"
        date_info = DateInfoState(date=date_str, weekday=weekday, quarter=quarter)

        db = await dw_mysql_repository.get_db_info()
        db_info = DBInfoState(**db)
        logger.info(f"Database info: {db_info}")
        logger.info(f"Date info: {date_info}")

        writer({"type": "progress", "step": step, "status": "success"})
        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        logger.error(f"{step} failed: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
