"""
应用程序配置模块

本模块定义并加载智能问数系统的所有配置信息，采用 dataclass 和 OmegaConf 实现类型安全的配置管理。

配置分类：
1. 日志配置 (LoggingConfig)
   - 文件日志：启用状态、级别、路径、轮转策略、保留策略
   - 控制台日志：启用状态、级别

2. 数据库配置 (DBConfig)
   - db_meta: 元数据库（存储表结构、指标定义、字段描述等）
   - db_dw: 数据仓库（存储实际业务数据）

3. 向量数据库配置 (QdrantConfig)
   - 存储字段和指标的向量化表示
   - 用于语义相似度搜索

4. 嵌入模型配置 (EmbeddingConfig)
   - BGE 中文嵌入模型服务地址
   - 将文本转换为向量

5. Elasticsearch 配置 (ESConfig)
   - 维度字段取值索引
   - 用于模糊匹配和同义词扩展

6. LLM 配置 (LLMConfig)
   - 大语言模型名称
   - API 密钥和端点
   - 支持 OpenAI 兼容接口

设计考虑：
- 使用 dataclass 提供类型检查
- 使用 OmegaConf 实现 YAML 配置加载和验证
- 配置与代码分离，便于部署和维护
- 支持环境变量和配置文件两种方式

配置加载流程：
1. 从项目根目录的 conf/app_config.yml 读取配置
2. 使用 OmegaConf.structured 定义 Schema
3. 合并配置并转换为 AppConfig 对象
4. 全局唯一的 app_config 实例供各模块使用

示例用法：
    from app.conf.app_config import app_config
    
    # 访问配置
    db_host = app_config.db_dw.host
    llm_model = app_config.llm.model_name
    log_path = app_config.logging.file.path
"""
# 日志配置
from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf


@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str


@dataclass
class Console:
    enable: bool
    level: str


@dataclass
class LoggingConfig:
    file: File
    console: Console


# 数据库配置
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int


@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str


@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str


@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str


@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig


config_file = Path(__file__).parents[2] / 'conf' / 'app_config.yml'
context = OmegaConf.load(config_file)
schema = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))

if __name__ == '__main__':
    print(app_config.logging.file.path)