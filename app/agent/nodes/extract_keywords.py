"""
关键词提取节点模块

本模块实现从用户自然语言查询中提取关键词的功能，作为智能问数流程的第一步。

功能说明：
1. 使用 jieba.analyse 进行中文分词和关键词抽取
2. 基于词性过滤，保留对 SQL 生成有意义的词汇：
   - 名词 (n, nr, ns, nt, nz): 数据实体、地名、机构名等
   - 动词 (v, vn): 操作意图（统计、分析、比较）
   - 形容词 (a, an): 限定条件（快速、主要、核心）
   - 英文 (eng): 字段名、表名等
   - 成语和固定短语 (i, l): 业务术语
3. 将原始查询也加入关键词列表，确保不丢失信息

算法选择：
- jieba.analyse.extract_tags: 基于 TF-IDF 的关键词抽取算法
- 适合短文本（用户查询通常较短）
- 支持自定义词性过滤

处理流程：
1. 接收用户查询（如 "统计华北地区的销售总额"）
2. 分词并标注词性
3. 提取符合词性要求的关键词
4. 去重后返回关键词列表

示例：
    输入：query = "统计华北地区的销售总额"
    输出：keywords = ["统计", "华北地区", "销售总额", "统计华北地区的销售总额"]
    
    输入：query = "北京和上海哪个城市业绩更好"
    输出：keywords = ["北京", "上海", "城市", "业绩", "北京和上海哪个城市业绩更好"]

在 LangGraph 中的位置：
    START → extract_keywords → recall_column/value/metric
"""
import jieba.analyse
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    step = "抽取关键词"
    writer = runtime.stream_writer
    writer({"type": "progress", "step": step, "status": "running"})

    try:
        query = state["query"]

        allow_pos = (
            "n",  # 名词: 数据、服务器、表格
            "nr",  # 人名: 张三、李四
            "ns",  # 地名: 北京、上海
            "nt",  # 机构团体名: 政府、学校、某公司
            "nz",  # 其他专有名词: Unicode、哈希算法、诺贝尔奖
            "v",  # 动词: 运行、开发
            "vn",  # 名动词: 工作、研究
            "a",  # 形容词: 美丽、快速
            "an",  # 名形词: 难度、合法性、复杂度
            "eng",  # 英文
            "i",  # 成语
            "l",  # 常用固定短语
        )

        keywords = jieba.analyse.extract_tags(query, allowPOS=allow_pos) # 使用 jieba.analyse.extract_tags 进行关键词抽取 allowPOS 参数指定允许的词性

        keywords = list(set(keywords + [query]))

        writer({"type": "progress", "step": step, "status": "success"})

        logger.info(f"抽取关键词成功: {keywords}")
        return {"keywords": keywords}
    except Exception as e:
        logger.error(f"抽取关键词失败: {e}")
        writer({"type": "progress", "step": step, "status": "error"})
        raise
