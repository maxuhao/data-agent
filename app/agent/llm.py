"""
大语言模型 (LLM) 初始化模块

本模块负责初始化和配置智能问数系统使用的大语言模型客户端。

功能说明：
1. 从 app_config 读取 LLM 配置信息（模型名称、API 密钥、基础 URL）
2. 使用 LangChain 的 init_chat_model 工厂函数创建聊天模型实例
3. 配置模型参数：
   - model: 指定使用的模型（如 GPT-4、Claude、通义千问等）
   - model_provider: 模型提供商（此处为 "openai" 兼容接口）
   - base_url: API 端点地址（支持自定义部署或第三方服务）
   - api_key: API 认证密钥
   - temperature: 温度参数，0 表示输出确定性最高（适合 SQL 生成任务）

设计考虑：
- 单例模式：全局唯一的 llm 实例，避免重复初始化
- 零温度设置：SQL 生成需要精确性，不需要创造性
- OpenAI 兼容接口：可以切换不同的模型提供商（如 Azure、Ollama、vLLM 等）

支持的模型示例：
- OpenAI: gpt-4, gpt-3.5-turbo
- Anthropic: claude-3-opus, claude-sonnet
- 开源模型：qwen-72b, llama-3-70b (通过 OpenAI 兼容接口)

使用方法：
    from app.agent.llm import llm
    response = llm.invoke("你好")
    print(response.content)
    
    # 或在节点函数中使用
    def generate_sql(state: DataAgentState):
        prompt = PromptTemplate(template=SQL_TEMPLATE).format(**state)
        response = llm.invoke(prompt)
        return {"sql": response.content}
"""
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# 确保 .env 文件已加载（双重保险）
load_dotenv()

import os
from app.conf.app_config import app_config

# 输出 LLM 配置信息用于调试
print("=" * 50)
print("LLM 配置信息:")
print(f"模型名称：{app_config.llm.model_name}")
print(f"API Key: {app_config.llm.api_key[:20]}...{app_config.llm.api_key[-10:]}")
print(f"Base URL: {app_config.llm.base_url}")
print(f"\n环境变量检查:")
print(f"LLM_API_KEY (env): {os.getenv('LLM_API_KEY', 'NOT_SET')[:20]}...{os.getenv('LLM_API_KEY', '')[-10:] if os.getenv('LLM_API_KEY') else ''}")
print("=" * 50)

llm = init_chat_model(model=app_config.llm.model_name,
                      model_provider="openai",
                      base_url=app_config.llm.base_url,
                      api_key=app_config.llm.api_key,
                      temperature=0)

if __name__ == '__main__':
    print(llm.invoke("你好").content)
