import json

from redis import Redis

from app.domain import commands
from app.service_layer import MessageBus

from . import bootstrap
from .config import get_redis_host_and_port

r = Redis(**get_redis_host_and_port())


def main():
    bus = bootstrap.bootstrap()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")

    for m in pubsub.listen():
        handle_change_batch_quantity(m, bus)


def handle_change_batch_quantity(m, bus: MessageBus):
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    print(f"got command via redis eventconsumer client, {cmd=}")
    bus.handle(cmd)


# def publish(channel, event: Event):
#     r.publish(channel, json.dumps(dict(event)))


if __name__ == "__main__":
    main()
