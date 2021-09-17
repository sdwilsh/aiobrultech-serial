from __future__ import annotations

import asyncio
import functools
import logging
from asyncio.queues import Queue
from asyncio.tasks import Task
from typing import Any, Awaitable, Callable

import serial_asyncio
from siobrultech_protocols.gem.packets import Packet
from siobrultech_protocols.gem.protocol import PacketProtocol

logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(
        self,
        queue: Queue,
        consumer_task: Task[None],
        producer_task: Task[tuple[serial_asyncio.SerialTransport, Any]],
    ):
        self._consumer_task = consumer_task
        self._queue = queue
        self._producer_task = producer_task

    async def close(self) -> None:
        transport, _ = await self._producer_task
        transport.close()
        await self._queue.join()
        self._consumer_task.cancel()

    async def __aenter__(self) -> Connection:
        return self

    async def __aexit__(self, exc_type, exc, exc_traceback):
        if exc is not None:
            await self.close()


def connect(
    packet_handler: Callable[[Packet], Awaitable[None]],
    port: str,
    baudrate: int = 115200,
    **kwargs
) -> Connection:
    async def consumer(queue: Queue) -> None:
        try:
            while True:
                packet: Packet = await queue.get()
                try:
                    await packet_handler(packet)
                except Exception as exc:
                    logger.exception("Exception while calling packet handler!", exc)
                queue.task_done()
        except asyncio.CancelledError:
            logger.debug("queue consumer is getting canceled")
            raise

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    consumer_task = asyncio.create_task(
        consumer(queue), name="consumer:{}".format(port)
    )
    producer_task = asyncio.create_task(
        serial_asyncio.create_serial_connection(
            loop,
            functools.partial(PacketProtocol, queue=queue),
            port,
            baudrate=baudrate,
            **kwargs
        )
    )

    return Connection(queue, consumer_task, producer_task)
