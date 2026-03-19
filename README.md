# 智能问数

智能问数是一个基于自然语言处理与数据分析技术的智能数据服务系统，面向数据仓库应用场景，旨在帮助用户通过对话方式高效获取数据仓库中的数据洞察。用户无需掌握复杂的查询语法，即可用自然语言提出问题，系统自动完成对数据仓库数据的理解、计算分析与结果可视化，大幅提升数据使用效率，降低数据分析门槛，助力业务决策智能化。

## 项目架构

```
data-agent/
├── app/                    # 核心应用代码
├── conf/                   # 配置文件
├── prompts/               # LLM 提示词模板
├── docker/                # Docker 部署配置
├── logs/                  # 日志文件
├── main.py               # 应用入口
└── README.md             # 项目说明
```

## 目录结构及功能说明

### 1. `app/` - 核心应用目录

包含智能问数系统的所有核心业务代码，按功能模块划分为以下子目录：

#### `app/agent/` - Agent 工作流模块
实现基于 LangGraph 的智能问数工作流，包含状态定义、上下文管理和 12 个处理节点。

**文件说明：**
- `context.py` - 定义 LangGraph 工作流的上下文数据结构，存储所有节点共享的依赖注入对象（数据库连接、向量库客户端等）
- `graph.py` - 定义 StateGraph 状态图，构建从关键词提取到 SQL 执行的完整工作流程
- `llm.py` - 初始化和配置大语言模型客户端，使用 LangChain 集成 OpenAI 兼容接口
- `state.py` - 使用 TypedDict 定义工作流中传递的状态数据结构，确保类型安全

**nodes/ - 处理节点模块**
每个节点实现工作流中的一个具体处理步骤：

- `extract_keywords.py` - 从用户查询中提取关键词，使用 jieba.analyse 进行中文分词和词性过滤
- `recall_column.py` - 基于关键词在 Qdrant 向量数据库中检索相关的字段信息
- `recall_value.py` - 在 Elasticsearch 中检索维度字段的具体取值（如地区名、产品名）
- `recall_metric.py` - 在 Qdrant 中检索预定义的业务指标信息
- `merge_retrieved_info.py` - 合并三个召回源的信息，补充关联字段并按表分组
- `filter_table.py` - 使用 LLM 过滤出与查询相关的表和字段
- `filter_metric.py` - 使用 LLM 过滤出与查询相关的业务指标
- `add_extra_context.py` - 添加日期信息和数据库方言信息
- `generate_sql.py` - 根据收集的信息生成 SQL 查询
- `validate_sql.py` - 验证 SQL 语法和语义是否正确
- `correct_sql.py` - 如果验证失败，修正 SQL
- `run_sql.py` - 执行 SQL 并返回结果

#### `app/api/` - API 接口模块
定义 FastAPI 路由、依赖注入和应用生命周期管理。

**文件说明：**
- `lifespan.py` - 管理应用启动和关闭时的资源初始化与释放（数据库连接、向量库客户端等）
- `dependencies.py` - 定义 API 路由的依赖注入函数（会话管理、Repository 注入、QueryService 组合）
- `routers/query_router.py` - 定义 POST /api/query 端点，接收自然语言查询并返回流式响应
- `schemas/query_schema.py` - 定义请求和响应的 Pydantic 数据模型

#### `app/clients/` - 客户端管理器模块
封装外部服务的异步客户端，管理连接池和会话生命周期。

**文件说明：**
- `mysql_client_manager.py` - MySQL 数据库客户端管理器，提供元数据库和数据仓库的连接池
- `qdrant_client_manager.py` - Qdrant 向量数据库客户端管理器，支持语义相似度搜索
- `es_client_manager.py` - Elasticsearch 客户端管理器，提供全文检索和模糊匹配能力
- `embedding_client_manager.py` - Hugging Face 嵌入模型客户端管理器，提供文本向量化功能

#### `app/repositories/` - 数据仓库模块
实现 Repository 模式，封装数据访问逻辑，位于 Service 层之下。

**mysql/ - MySQL 数据仓库**
- `dw/dw_mysql_repository.py` - 数据仓库访问，提供表结构查询、数据取样、SQL 验证和执行
- `meta/meta_mysql_repository.py` - 元数据访问，负责表信息、字段信息、指标信息的持久化
- `meta/mappers/` - Entity 与 Model 之间的转换映射器
  - `column_info_mapper.py` - ColumnInfo 实体与 ColumnInfoMySQL 模型互转
  - `table_info_mapper.py` - TableInfo 实体与 TableInfoMySQL 模型互转
  - `metric_info_mapper.py` - MetricInfo 实体与 MetricInfoMySQL 模型互转
  - `column_metric_mapper.py` - ColumnMetric 实体与 ColumnMetricMySQL 模型互转

**qdrant/ - Qdrant 向量数据库**
- `column_qdrant_repository.py` - 字段信息的向量检索，支持字段的语义相似度匹配
- `metric_qdrant_repository.py` - 指标信息的向量检索，支持业务指标的语义匹配

**es/ - Elasticsearch 搜索引擎**
- `value_es_repository.py` - 维度字段取值的全文检索，支持模糊匹配和同义词扩展

#### `app/services/` - 业务服务模块
实现核心业务逻辑，组合多个 Repository 完成复杂操作。

**文件说明：**
- `query_service.py` - 查询服务，将用户自然语言转换为 SQL 并执行，以 SSE 格式流式返回结果
- `meta_knowledge_service.py` - 元知识构建服务，将配置文件中的表、字段、指标同步到各存储系统

#### `app/entities/` - 业务实体模块
定义业务层的实体类，用于在各层之间传递结构化数据。

**文件说明：**
- `column_info.py` - 字段信息实体，包含字段的完整元数据（名称、类型、角色、示例、描述、别名）
- `table_info.py` - 表信息实体，包含表的物理结构定义（名称、类型、描述）
- `metric_info.py` - 指标信息实体，包含业务指标的定义和计算逻辑
- `column_metric.py` - 指标 - 字段关联实体，记录指标计算涉及的字段
- `value_info.py` - 字段取值信息实体，存储维度字段的具体取值

#### `app/models/` - 数据库模型模块
定义 SQLAlchemy ORM 模型，映射数据库表结构。

**文件说明：**
- `base.py` - SQLAlchemy 模型基类，所有模型类的统一父类
- `column_info.py` - column_info 表的 ORM 模型，存储字段元数据
- `table_info.py` - table_info 表的 ORM 模型，存储表元数据
- `metric_info.py` - metric_info 表的 ORM 模型，存储业务指标定义
- `column_metric.py` - column_metric 表的 ORM 模型，存储指标与字段的关联关系

#### `app/conf/` - 配置管理模块
加载和管理应用程序的所有配置信息。

**文件说明：**
- `app_config.py` - 加载 app_config.yml，定义日志、数据库、向量库、ES、LLM 等配置
- `meta_config.py` - 加载 meta_config.yaml，定义表、字段、指标的配置结构

#### `app/prompt/` - 提示词加载模块
管理 LLM 提示词模板的加载。

**文件说明：**
- `prompt_loader.py` - 从 prompts/ 目录读取 .prompt 文件，返回纯文本提示词内容

#### `app/core/` - 核心工具模块
提供日志、上下文变量等核心工具。

**文件说明：**
- `log.py` - 使用 Loguru 配置统一的日志系统，支持 request_id 追踪和彩色输出
- `context.py` - 定义异步上下文变量（ContextVar），用于在异步环境中传递请求级数据

#### `app/scripts/` - 脚本工具模块
提供辅助工具和批处理脚本。

**文件说明：**
- `build_meta_knowledge.py` - 元知识构建脚本，将配置文件中的元数据同步到各存储系统

---

### 2. `conf/` - 配置文件目录

存放应用程序的配置文件，支持环境变量覆盖。

**文件说明：**
- `app_config.yml` - 应用程序主配置文件，包含：
  - 日志配置（文件日志、控制台日志的级别、路径、轮转策略）
  - 数据库配置（元数据库、数据仓库的连接信息）
  - Qdrant 向量数据库配置
  - Embedding 嵌入模型服务配置
  - Elasticsearch 配置
  - LLM 大语言模型配置
  
- `meta_config.yaml` - 元知识配置文件，定义：
  - 表结构（表名、类型、描述、字段列表）
  - 字段定义（字段名、角色、描述、别名、是否同步到 ES）
  - 指标定义（指标名、描述、相关字段、别名）

---

### 3. `prompts/` - 提示词模板目录

存放 LLM 使用的提示词模板文件，采用 .prompt 后缀。

**文件说明：**
- `extend_keywords_for_column_recall.prompt` - 字段召回时扩展关键词的提示词，用于生成更多相关词汇
- `extend_keywords_for_value_recall.prompt` - 取值召回时扩展关键词的提示词，生成可能的字段取值表述
- `extend_keywords_for_metric_recall.prompt` - 指标召回时扩展关键词的提示词，生成指标相关词汇
- `filter_table_info.prompt` - 表信息过滤的提示词，让 LLM 判断哪些表和字段与查询相关
- `filter_metric_info.prompt` - 指标信息过滤的提示词，让 LLM 判断哪些指标与查询相关
- `generate_sql.prompt` - SQL 生成的专用提示词，指导 LLM 根据上下文生成正确的 SQL
- `correct_sql.prompt` - SQL 校正的专用提示词，提供错误信息让 LLM 修正 SQL

---

### 4. `docker/` - Docker 部署目录

包含 Docker Compose 配置和服务镜像构建文件。

**目录结构：**
```
docker/
├── docker-compose.yaml      # Docker Compose 编排文件
├── mysql/                   # MySQL 初始化脚本
│   ├── dw.sql              # 数据仓库表结构
│   └── meta.sql            # 元数据库表结构
├── elasticsearch/           # Elasticsearch 插件配置
│   └── plugins/            # IK 分词器插件
└── embedding/              # Embedding 模型目录
    └── bge-large-zh-v1.5/  # BGE 中文嵌入模型
```

**文件说明：**
- `docker-compose.yaml` - 定义所有服务的容器编排：
  - MySQL 8.0（元数据库 + 数据仓库）
  - Elasticsearch 8.x（全文搜索引擎）
  - Kibana（ES 可视化工具）
  - Qdrant v1.16（向量数据库）
  - Embedding（BGE-large-zh-v1.5 中文嵌入模型）

---

### 5. `logs/` - 日志目录

存放应用运行日志文件。

**文件说明：**
- `app.log` - 应用主日志文件，包含所有节点的执行日志和错误信息

---

### 6. 根目录文件

**文件说明：**
- `main.py` - FastAPI 应用入口，配置中间件（request_id 生成）、注册路由、设置生命周期管理
- `pyproject.toml` - Python 项目配置文件，定义项目依赖（FastAPI、LangChain、SQLAlchemy 等）
- `.env` - 环境变量文件（敏感信息，不应提交到版本控制）
- `.gitignore` - Git 忽略规则
- `uv.lock` - UV 包管理器锁文件

---

## 技术栈

- **Web 框架**: FastAPI
- **Agent 框架**: LangGraph + LangChain
- **数据库**: MySQL 8.0
- **向量数据库**: Qdrant
- **搜索引擎**: Elasticsearch 8.x
- **嵌入模型**: BGE-large-zh-v1.5
- **日志**: Loguru
- **ORM**: SQLAlchemy 2.0
- **分词**: jieba

---

## 快速开始

### 1. 启动所有依赖服务
```bash
cd docker
docker-compose up -d
```

### 2. 安装依赖
```bash
uv sync
```

### 3. 配置环境变量
编辑 `.env` 文件，配置数据库连接、LLM API 密钥等。

### 4. 构建元知识库
```bash
python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
```

### 5. 启动应用

#### 方式一：使用 FastAPI 开发服务器（推荐用于开发）
```bash
fastapi dev main.py
```
**优点：**
- 🚀 **自动重载**：代码修改后自动重启，无需手动干预
- 🔍 **调试友好**：详细的错误页面和堆栈跟踪
- ⚡ **开箱即用**：无需额外配置，最适合开发环境
- 🎨 **交互式文档**：自动提供 Swagger UI 和 ReDoc

#### 方式二：使用 Uvicorn（适合生产和自定义配置）
```bash
# 使用 uv
uv run uvicorn main:app --reload

# 或直接使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
**优点：**
- ⚙️ **灵活配置**：支持自定义 host、port、workers 等参数
- 📦 **生产就绪**：可以配置多 worker 进程处理并发
- 🔧 **精细控制**：适合需要调优性能的场景
- 🌐 **跨平台**：所有 Python 环境通用

#### 方式三：使用 Python 模块运行
```bash
python -m uvicorn main:app --reload
```
**优点：**
- 💼 **兼容性好**：适用于没有安装 uv 的环境
- 🎯 **简单直接**：命令简短，易于记忆

---

### 6. 访问 API

#### API 端点
```
POST http://localhost:8000/api/query
Content-Type: application/json

{"query": "统计华北地区 2025 年的销售额"}
```

#### 交互式文档
启动后自动提供以下文档界面：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**功能：**
- 📖 在线查看 API 接口说明
- 🧪 直接在浏览器中测试接口
- 📊 查看请求/响应格式
- 🔐 管理认证信息

---

## 工作流程

```
START → extract_keywords → [recall_column, recall_value, recall_metric] 
       → merge_retrieved_info → [filter_table, filter_metric] 
       → add_extra_context → generate_sql → validate_sql 
       → {正确：run_sql → END | 错误：correct_sql → run_sql → END}
```

---

## 项目特点

1. **语义检索**: 使用向量数据库解决用户用语 vs 数据库命名的语义鸿沟
2. **模糊匹配**: Elasticsearch 全文检索支持同义词、错别字容错
3. **自纠正**: SQL 验证失败时自动修正，提高成功率
4. **流式输出**: SSE 实时反馈每个处理步骤的进度
5. **类型安全**: TypedDict + Pydantic 确保数据结构正确
6. **依赖注入**: FastAPI 依赖系统解耦各层代码
7. **日志追踪**: request_id 串联完整调用链，便于调试
