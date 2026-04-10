import requests

from app import config

url = config.get_api_url()


def post_to_add_batch(ref, sku, qty, eta):
    r = requests.post(
        f"{url}/add_batch",
        json={"ref": ref, "sku": sku, "qty": qty, "eta": eta},
        timeout=5,
    )
    assert r.status_code == 201


def post_to_allocate(orderid, sku, qty) -> requests.Response:
    data = {"orderid": orderid, "sku": sku, "qty": qty}
    return requests.post(f"{url}/allocate", json=data, timeout=5)


def get_allocation(orderid):
    return requests.get(f"{url}/allocations?orderid={orderid}")
