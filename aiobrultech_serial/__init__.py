from __future__ import annotations

import asyncio
import logging
from asyncio.futures import Future
from asyncio.queues import Queue
from asyncio.tasks import Task
from types import TracebackType
from typing import Any, AsyncGenerator, Optional, Type

import serial_asyncio
from siobrultech_protocols.gem.packets import Packet
from siobrultech_protocols.gem.protocol import PacketProtocol

logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, port: str, baudrate: int = 115200, **kwargs: Any):
        self._closed_future: Future[bool] = Future()
        self._packets: Queue[Packet] = Queue()
        self._producer_task: Task[
            tuple[serial_asyncio.SerialTransport, Any]
        ] = asyncio.create_task(
            serial_asyncio.create_serial_connection(  # type: ignore
                asyncio.get_event_loop(),
                lambda: self._protocol,
                port,
                baudrate=baudrate,
                **kwargs,
            ),
            name=f"{__name__}:serial-connection",
        )
        self._protocol = PacketProtocol(queue=self._packets)

    async def packets(self) -> AsyncGenerator[Packet, None]:
        transport = await self._get_transport()
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
            transport = await self._get_transport()
            transport.close()

    async def __aenter__(self) -> Connection:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ):
        await self.close()

    async def _get_transport(self) -> serial_asyncio.SerialTransport:
        transport, _ = await self._producer_task
        return transport


connect = Connection
