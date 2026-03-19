"""
演示普通 dict 和 TypedDict 的类型检查区别
"""

from typing import TypedDict


# ========== 1. 普通 dict - 没有类型检查 ==========

def process_data_bad(data: dict):
    """使用普通 dict，无法进行类型检查"""
    print(data["name"])
    print(data["age"])


# ❌ 这样写也不会报错，但运行时会出错
wrong_data = {
    "name": "张三",
    "age": "不是数字"  # 应该是 int，但写成了 str
}

process_data_bad(wrong_data)  # 运行时才发现问题


# ========== 2. TypedDict - 有类型检查 ==========

class PersonState(TypedDict):
    name: str
    age: int
    email: str | None


def process_data_good(person: PersonState):
    """使用 TypedDict，IDE 和类型检查工具会提示错误"""
    print(f"姓名：{person['name']}")
    print(f"年龄：{person['age']}")
    if person.get('email'):
        print(f"邮箱：{person['email']}")


# ✅ 正确的用法
correct_person: PersonState = {
    "name": "李四",
    "age": 25,
    "email": "lisi@example.com"
}

process_data_good(correct_person)


# ❌ 类型错误 - IDE 会标红提示
wrong_person: PersonState = {
    "name": "王五",
    "age": "三十岁",  # ❌ 类型错误！应该是 int
    "email": 12345    # ❌ 类型错误！应该是 str 或 None
}

# ❌ 缺少必需字段
incomplete_person: PersonState = {
    "name": "赵六"
    # ❌ 缺少 age 和 email 字段（如果设置了 required）
}


# ========== 3. 实际项目中的例子 ==========

class DataAgentState(TypedDict):
    query: str
    keywords: list[str]
    sql: str
    error: str | None


def validate_sql_node(state: DataAgentState):
    """LangGraph 节点函数"""
    # ✅ 有类型提示，IDE 会自动补全
    query = state["query"]
    keywords = state["keywords"]
    
    # ❌ 如果拼写错误，IDE 会提示
    # typo = state["qery"]  # 拼写错误，会被检测到
    
    return {"sql": "SELECT ...", "error": None}


# 测试运行
if __name__ == '__main__':
    print("===== 普通 dict 示例 =====")
    process_data_bad(wrong_data)
    
    print("\n===== TypedDict 示例 =====")
    process_data_good(correct_person)
    
    print("\n===== LangGraph 状态示例 =====")
    agent_state: DataAgentState = {
        "query": "统计销售额",
        "keywords": ["销售", "统计"],
        "sql": "SELECT SUM(sales) FROM orders",
        "error": None
    }
    result = validate_sql_node(agent_state)
    print(result)
