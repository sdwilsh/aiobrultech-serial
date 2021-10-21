import asyncio
import os
import unittest
from unittest import IsolatedAsyncioTestCase

from aiobrultech_serial import connect

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_packet(packet_file_name: str) -> bytes:
    with open(os.path.join(DATA_DIR, packet_file_name), "rb") as data_file:
        return data_file.read()


class TestConnection(IsolatedAsyncioTestCase):
    async def test_close_connection_stops_generator(self) -> None:
        class Data(asyncio.Protocol):
            def connection_made(self, transport: asyncio.BaseTransport) -> None:
                assert isinstance(transport, asyncio.Transport)
                transport.write(read_packet("BIN32-NET.bin"))

        await asyncio.create_task(
            asyncio.get_event_loop().create_server(Data, "localhost", 8000)
        )

        async with connect("socket://localhost:8000") as connection:
            async for packet in connection.packets():
                self.assertEqual(packet.packet_format.name, "BIN32-NET")
                await connection.close()

    async def test_close_transport_stops_generator(self) -> None:
        class Data(asyncio.Protocol):
            def connection_made(self, transport: asyncio.BaseTransport) -> None:
                assert isinstance(transport, asyncio.Transport)
                transport.write(read_packet("BIN32-NET.bin"))
                transport.close()

        await asyncio.create_task(
            asyncio.get_event_loop().create_server(Data, "localhost", 8000)
        )

        async with connect("socket://localhost:8000") as connection:
            async for packet in connection.packets():
                self.assertEqual(packet.packet_format.name, "BIN32-NET")

    async def test_break_exits_gracefully(self) -> None:
        class Data(asyncio.Protocol):
            def connection_made(self, transport: asyncio.BaseTransport) -> None:
                assert isinstance(transport, asyncio.Transport)
                transport.write(read_packet("BIN32-NET.bin"))

        await asyncio.create_task(
            asyncio.get_event_loop().create_server(Data, "localhost", 8000)
        )

        async with connect("socket://localhost:8000") as connection:
            async for packet in connection.packets():
                self.assertEqual(packet.packet_format.name, "BIN32-NET")
                break


if __name__ == "__main__":
    unittest.main()
