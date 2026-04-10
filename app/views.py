from .adapters import redis_eventpublisher


def allocations(orderid: str):
    batches = redis_eventpublisher.get_readmodel(orderid=orderid)

    return [
        {"sku": sku.decode(), "batchref": batchref.decode()}
        for sku, batchref in batches.items()
    ]
