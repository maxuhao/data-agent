"""
查询请求数据模型模块

本模块定义 API 请求和响应的数据结构，使用 Pydantic 进行数据验证和序列化。

功能说明：
1. 定义 QuerySchema 数据模型
2. 验证请求体格式（必须包含 query 字段）
3. 自动类型转换和数据清洗
4. 生成 OpenAPI/Swagger 文档

Pydantic 的优势：
- 类型检查：编译时和运行时类型验证
- 数据验证：自动验证字段是否必填、格式是否正确
- 自动序列化：模型 → JSON / JSON → 模型
- IDE 支持：自动补全和类型提示
- 文档生成：自动生成 API 文档

QuerySchema 结构：
- query: str (必填) - 用户的自然语言查询
  示例："统计华北地区 2025 年的销售额"

为什么使用 BaseModel：
- FastAPI 要求：请求体和响应体必须继承 BaseModel
- 自动验证：FastAPI 会自动调用 model_validate()
- 错误处理：格式错误时返回清晰的错误信息
- 文档友好：Swagger UI 中显示字段说明

请求验证示例：
    ✅ 正确：{"query": "统计销售额"}
    ❌ 错误：{"wrong_field": "..."} → 返回 422 验证错误
    ❌ 错误：{} → 返回 422 验证错误（缺少必填字段）

使用方法：
    from app.api.schemas.query_schema import QuerySchema
    
    # 创建实例（自动验证）
    query_data = QuerySchema(query="统计销售额")
    
    # 访问字段
    print(query_data.query)  # "统计销售额"
    
    # 转换为字典
    print(query_data.model_dump())  # {"query": "统计销售额"}
"""
from pydantic import BaseModel


class QuerySchema(BaseModel):
    query: str
