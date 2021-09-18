from __future__ import annotations

import asyncio
import functools
import logging
from asyncio.tasks import Task
from typing import Any, AsyncGenerator

import serial_asyncio
from siobrultech_protocols.gem.packets import Packet
from siobrultech_protocols.gem.protocol import PacketProtocol

logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, port: str, baudrate: int = 115200, **kwargs):
        self._closed_future = asyncio.Future()
        self._packets = asyncio.Queue()
        self._producer_task: Task[
            tuple[serial_asyncio.SerialTransport, Any]
        ] = asyncio.create_task(
            serial_asyncio.create_serial_connection(
                asyncio.get_event_loop(),
                functools.partial(PacketProtocol, queue=self._packets),
                port,
                baudrate=baudrate,
                **kwargs,
            ),
            name=f"{__name__}:serial-connection",
        )

    async def packets(self) -> AsyncGenerator[Packet, None]:
        transport, _ = await self._producer_task
        while not transport.is_closing() and not self._closed_future.done():
            task: Task[Packet] = asyncio.create_task(
                self._packets.get(), name=f"{__name__}:wait-for-packet"
            )
            try:
                # Wait until either:
                # 1) a second has passed
                # 2) a packet is processed
                done, _ = await asyncio.wait(
                    (asyncio.create_task(asyncio.sleep(1)), task),
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except asyncio.CancelledError:
                logger.debug("queue generator is getting canceled")
                task.cancel()
                raise
            if task in done:
                self._packets.task_done()
                yield task.result()
            else:
                # Try again if our loop condition is good still.
                task.cancel()

    async def close(self) -> None:
        if not self._closed_future.done():
            self._closed_future.set_result(True)
            transport, _ = await self._producer_task
            transport.close()

    async def __aenter__(self) -> Connection:
        return self

    async def __aexit__(self, exc_type, exc, exc_traceback):
        await self.close()


connect = Connection
