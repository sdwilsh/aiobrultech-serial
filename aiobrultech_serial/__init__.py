from __future__ import annotations

import asyncio
import logging
from asyncio.futures import Future
from asyncio.locks import Lock
from asyncio.queues import Queue
from asyncio.tasks import Task
from datetime import datetime, timedelta
from types import TracebackType
from typing import Any, AsyncGenerator, Optional, Type

import serial_asyncio
from siobrultech_protocols.gem import api
from siobrultech_protocols.gem.const import PACKET_DELAY_CLEAR_TIME_DEFAULT
from siobrultech_protocols.gem.packets import Packet, PacketFormatType
from siobrultech_protocols.gem.protocol import (
    ApiType,
    BidirectionalProtocol,
    PacketProtocolMessage,
    PacketReceivedMessage,
)

from aiobrultech_serial.exceptions import SetFailed

logger: logging.Logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(
        self,
        port: str,
        api_type: Optional[ApiType] = None,
        baudrate: int = 115200,
        packet_delay_clear_time: timedelta = PACKET_DELAY_CLEAR_TIME_DEFAULT,
        **kwargs: Any,
    ):
        self._api_lock: Lock = Lock()
        self._closed_future: Future[bool] = Future()
        self._packets: Queue[PacketProtocolMessage] = Queue()
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
        self._protocol = BidirectionalProtocol(
            api_type=api_type,
            queue=self._packets,
            packet_delay_clear_time=packet_delay_clear_time,
        )

    async def packets(self) -> AsyncGenerator[Packet, None]:
        transport = await self._get_transport()
        while not transport.is_closing() and not self._closed_future.done():
            task: Task[PacketProtocolMessage] = asyncio.create_task(
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
                message = task.result()
                if isinstance(message, PacketReceivedMessage):
                    yield message.packet
            else:
                # Try again if our loop condition is good still.
                task.cancel()

    async def close(self) -> None:
        if not self._closed_future.done():
            self._closed_future.set_result(True)
            transport = await self._get_transport()
            transport.close()

    async def get_serial_number(self) -> int:
        await self._assert_transport_open()
        async with self._api_lock:
            return await api.get_serial_number(self._protocol)

    async def set_date_and_time(self, new_datetime: datetime) -> None:
        await self._assert_transport_open()
        async with self._api_lock:
            success = await api.set_date_and_time(self._protocol, new_datetime)
            if not success:
                raise SetFailed()

    async def set_packet_format(self, format: PacketFormatType) -> None:
        await self._assert_transport_open()
        async with self._api_lock:
            success = await api.set_packet_format(self._protocol, format)
            if not success:
                raise SetFailed()

    async def set_packet_send_interval(self, send_interval_seconds: int) -> None:
        await self._assert_transport_open()
        async with self._api_lock:
            success = await api.set_packet_send_interval(
                self._protocol, send_interval_seconds
            )
            if not success:
                raise SetFailed()

    async def set_secondary_packet_format(self, format: PacketFormatType) -> None:
        await self._assert_transport_open()
        async with self._api_lock:
            success = await api.set_secondary_packet_format(self._protocol, format)
            if not success:
                raise SetFailed()

    async def synchronize_time(self) -> None:
        await self._assert_transport_open()
        async with self._api_lock:
            success = await api.synchronize_time(self._protocol)
            if not success:
                raise SetFailed()

    async def _assert_transport_open(self):
        transport = await self._get_transport()
        assert not transport.is_closing() and not self._closed_future.done()

    async def __aenter__(self) -> Connection:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def _get_transport(self) -> serial_asyncio.SerialTransport:
        transport, _ = await self._producer_task
        return transport


connect = Connection
