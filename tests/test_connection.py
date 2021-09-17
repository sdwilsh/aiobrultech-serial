import asyncio
import os
import unittest
from unittest import IsolatedAsyncioTestCase

from siobrultech_protocols.gem.packets import Packet

from aiobrultech_serial import connect

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_packet(packet_file_name: str) -> bytes:
    with open(os.path.join(DATA_DIR, packet_file_name), "rb") as data_file:
        return data_file.read()


class TestConnection(IsolatedAsyncioTestCase):
    async def test_simple(self) -> None:
        future = asyncio.Future()

        class Data(asyncio.Protocol):
            def connection_made(self, transport: asyncio.Transport) -> None:
                transport.write(read_packet("BIN32-NET.bin"))
                transport.close()

        await asyncio.create_task(
            asyncio.get_event_loop().create_server(Data, "localhost", 8000)
        )

        async def handler(packet: Packet) -> None:
            future.set_result(packet)
            future.done()

        async with connect(handler, "socket://localhost:8000"):
            packet: Packet = await asyncio.wait_for(future, 2)
            self.assertEqual(packet.packet_format.name, "BIN32-NET")


if __name__ == "__main__":
    unittest.main()
