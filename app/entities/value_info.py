"""
字段取值信息实体模块

本模块定义维度字段具体取值的数据结构，用于存储和传递字段的实际取值。

功能说明：
1. 使用 dataclass 定义字段取值的实体
2. 存储维度字段的具体值（如 "北京市"、"华为"、"Q1"）
3. 支持 Elasticsearch 全文检索

数据结构：
- id: 唯一标识（格式："表名。字段名。取值"）
- value: 字段的实际取值（中文、英文、数字等）
- column_id: 所属字段的 ID（外键引用）

什么是维度取值：
- 维度字段的所有可能取值
- 用于识别用户查询中提到的具体值
- 支持模糊匹配和同义词扩展

示例：
【地区字段】
- column_id: "dim_region.region_name"
- values: [
    ValueInfo(id="dim_region.region_name.北京市", value="北京市", ...),
    ValueInfo(id="dim_region.region_name.上海市", value="上海市", ...),
    ValueInfo(id="dim_region.region_name.广东省", value="广东省", ...)
  ]

【产品字段】
- column_id: "dim_product.product_name"
- values: [
    ValueInfo(value="华为 Mate60", ...),
    ValueInfo(value="iPhone 15", ...),
    ValueInfo(value="小米 14", ...)
  ]

在智能问数中的作用：
- 用户说 "北京" → 匹配 ValueInfo(value="北京市")
- 用户说 "华为" → 匹配 ValueInfo(value="华为技术有限公司")
- 帮助 LLM 理解用户提到的具体值对应的字段

数据来源：
- 从 DW 库查询维度字段的所有取值
- 通过 build_meta_knowledge.py 导入到 Elasticsearch
- 只对配置中 sync=True 的字段建立取值索引

使用方法：
    # 创建取值信息
    value = ValueInfo(
        id="dim_region.region_name.北京市",
        value="北京市",
        column_id="dim_region.region_name"
    )
    
    # 在 ES 中搜索
    results = await es_repository.search("北京")
    # 返回：[ValueInfo(value="北京市"), ValueInfo(value="北京区")]
"""
from dataclasses import dataclass


@dataclass
class ValueInfo:
    id: str
    value: str
    column_id: str
