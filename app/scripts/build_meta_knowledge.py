"""
元知识构建脚本模块

本模块是智能问数系统的知识库构建工具，负责将配置文件中定义的元数据同步到各个存储系统中。

功能说明：
1. 读取 meta_config.yaml 配置文件
2. 初始化所有客户端（MySQL、Qdrant、Embedding、ES）
3. 创建 Repository 实例（数据访问层）
4. 调用 MetaKnowledgeService 执行知识库构建
5. 优雅关闭所有客户端资源

核心流程：
【步骤 1】初始化客户端
    - meta_mysql_client_manager: 元数据库连接
    - dw_mysql_client_manager: 数据仓库连接
    - qdrant_client_manager: 向量数据库连接
    - embedding_client_manager: 嵌入模型客户端
    - es_client_manager: Elasticsearch 客户端

【步骤 2】创建 Repository 实例
    - MetaMySQLRepository: 元数据访问（保存表、字段、指标信息）
    - DWMySQLRepository: 数据仓库访问（查询表结构、字段取值）
    - ColumnQdrantRepository: 字段向量检索
    - MetricQdrantRepository: 指标向量检索
    - ValueESRepository: 维度取值全文检索

【步骤 3】创建 Service 实例
    - MetaKnowledgeService: 知识构建服务
    - 注入所有 Repository 和客户端依赖

【步骤 4】执行构建流程
    - 读取配置文件
    - 同步表信息到 Meta MySQL
    - 为字段建立 Qdrant 向量索引
    - 为维度取值建立 ES 全文索引
    - 同步指标信息到 Meta MySQL
    - 为指标建立 Qdrant 向量索引

【步骤 5】关闭资源
    - 关闭所有数据库连接池
    - 关闭所有客户端连接

技术栈：
- asyncio: 异步 IO 操作
- argparse: 命令行参数解析
- 依赖注入：通过构造函数注入 Repository 和 Service
- 上下文管理器：async with 管理会话生命周期

为什么需要知识库构建：
- 语义检索基础：字段/指标的向量化表示
- 模糊匹配基础：维度取值的全文索引
- 统一元数据：集中管理表结构、业务含义
- 解耦配置：配置文件 → 实际存储分离

数据来源：
- meta_config.yaml: 人工配置的元知识定义
- DW MySQL: 实际的表结构和数据
- Meta MySQL: 存储解析后的元数据
- Qdrant: 存储向量化的语义表示
- Elasticsearch: 存储维度取值的全文索引

执行方式：
1. PyCharm 直接运行（推荐）：
   - 右键 → Run 'build_meta_knowledge'
   - 默认使用 conf/meta_config.yaml

2. 命令行运行：
   python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml

执行日志：
    加载配置文件成功
    保存表信息和字段信息到数据库成功
    为字段信息建立向量索引成功
    为指定的维度字段取值建立全文索引成功
    保存指标信息到数据库成功
    为指标信息建立向量索引成功

注意事项：
- 确保所有服务已启动（MySQL、Qdrant、ES、Embedding）
- 确保配置文件路径正确
- 确保数据库表结构已创建（见 docker/mysql/meta.sql）
- 首次运行会创建 Qdrant 集合和 ES 索引

使用方法：
    # 在 PyCharm 中直接运行即可
    # 或者在终端执行：
    python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
    
    # 构建完成后，系统就具备了：
    # 1. 字段语义检索能力（Qdrant）
    # 2. 指标语义检索能力（Qdrant）
    # 3. 维度取值模糊匹配能力（ES）
    # 4. 完整的元数据管理（Meta MySQL）
"""
import argparse
import asyncio
from pathlib import Path

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


async def build(config_path: Path):
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()

    async with meta_mysql_client_manager.session_factory() as meta_session, dw_mysql_client_manager.session_factory() as dw_session:
        meta_mysql_repository = MetaMySQLRepository(meta_session)
        dw_mysql_repository = DWMySQLRepository(dw_session)

        column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)

        value_es_repository = ValueESRepository(es_client_manager.client)

        metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)

        meta_knowledge_service = MetaKnowledgeService(meta_mysql_repository=meta_mysql_repository,
                                                      dw_mysql_repository=dw_mysql_repository,
                                                      column_qdrant_repository=column_qdrant_repository,
                                                      embedding_client=embedding_client_manager.client,
                                                      value_es_repository=value_es_repository,
                                                      metric_qdrant_repository=metric_qdrant_repository)
        await meta_knowledge_service.build(config_path)

    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await es_client_manager.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--conf')  # 接受一个值的选项

    args = parser.parse_args()
    config_path = args.conf

    config_path = Path(__file__).parent.parent.parent / 'conf' / 'meta_config.yaml'

    asyncio.run(build(Path(config_path)))
