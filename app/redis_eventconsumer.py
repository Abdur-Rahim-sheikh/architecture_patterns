import json

from redis import Redis

from app.domain import commands
from app.service_layer import SqlAlchemyRepository, messagebus
from app.domain.events import Event
from .adapters import orm
from .config import get_redis_host_and_port

r = Redis(**get_redis_host_and_port())


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_message=True)
    pubsub.subscribe("change_batch_quantity")

    for m in pubsub.listen():
        handle_change_batch_quantity(m)


def handle_change_batch_quantity(m):
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus.handle(cmd, uow=SqlAlchemyRepository)


def publish(channel, event: Event):
    r.publish(channel, json.dumps(dict(event)))
