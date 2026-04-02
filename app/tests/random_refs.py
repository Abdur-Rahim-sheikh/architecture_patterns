from uuid import uuid4


def random_sku(prefix: str = "random"):
    return prefix + uuid4().hex[:5]


def random_batchref(prefix: int = 0):
    return f"{prefix}-{uuid4().hex[:5]}"


def random_orderid(prefix: int = 0):
    return f"{prefix}-{uuid4().hex[:5]}"
