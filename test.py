from contextlib import contextmanager


@contextmanager
def lifespan(url: str):
    print(f"建立链接:{url}")
    yield f"链接:{url}"
    print(f"断开链接:{url}")


with lifespan(url="mysql://root:123456@localhost:3306/test") as conn:
    print(f"基于获取的链接{conn}执行业务操作")
