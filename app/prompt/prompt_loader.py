"""
提示词加载器模块

本模块提供 LLM 提示词（Prompt）的加载功能，从外部文件读取提示词模板。

功能说明：
1. 从 prompts/ 目录读取 .prompt 文件
2. 支持 UTF-8 编码（确保中文正常显示）
3. 返回纯文本提示词内容

目录结构：
    app/
      prompt/
        prompt_loader.py      # 本文件
      prompts/                # 提示词文件目录
        extract_keywords.prompt
        generate_sql.prompt
        validate_sql.prompt
        ...

什么是 Prompt：
- 给 LLM 的指令文本
- 包含任务描述、输入格式、输出要求等
- 决定 LLM 的输出质量和方向

为什么使用外部文件：
- 便于维护：提示词与代码分离
- 易于修改：不需要重新编译代码
- 版本管理：可以独立追踪提示词变更
- 协作友好：业务人员也可以优化提示词

提示词文件示例（generate_sql.prompt）：
    你是一个 SQL 专家，请根据以下信息生成 SQL 查询：
    
    用户查询：{query}
    表结构：
    {table_infos}
    
    请生成符合 MySQL 语法的 SQL 查询。

使用方法：
    from app.prompt.prompt_loader import load_prompt
    
    # 加载提示词模板
    template = load_prompt("generate_sql")
    
    # 使用 LangChain 的 PromptTemplate 填充变量
    from langchain_core.prompts import PromptTemplate
    prompt = PromptTemplate(template=template, input_variables=["query", "table_infos"])
    
    # 调用 LLM
    response = llm.invoke({"query": "...", "table_infos": "..."})
"""
from pathlib import Path


def load_prompt(name: str):
    prompt_path = Path(__file__).parents[2] / 'prompts' / f"{name}.prompt"
    return prompt_path.read_text(encoding="utf-8")
