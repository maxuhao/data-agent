"""
SQLAlchemy 模型基类模块

本模块定义所有数据库模型的继承基类，提供 ORM 映射的基础配置。

功能说明：
1. 继承 SQLAlchemy 的 DeclarativeBase
2. 作为所有模型类的统一父类
3. 自动映射 Python 类到数据库表

什么是 DeclarativeBase：
- SQLAlchemy 2.0+ 的声明式基类
- 通过类属性定义数据库表结构
- 自动建立类与表的映射关系

为什么需要基类：
- 统一配置：所有模型共享相同的基类配置
- 代码复用：公共属性和方法可以放在基类中
- 类型推断：IDE 可以更好地提供自动补全

使用方法：
    from app.models.base import Base
    
    class MyModel(Base):
        __tablename__ = "my_table"
        id: Mapped[str] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(128))
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
