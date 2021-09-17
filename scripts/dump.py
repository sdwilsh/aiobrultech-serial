import argparse
import asyncio
import logging
from aiobrultech_serial import connect
from siobrultech_protocols.gem.packets import Packet


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Connect to the specified device and print the recieved packets."
    )
    parser.add_argument(
        "port",
        help="The serial connection to read from.  Supports anything pySerial supports.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


async def main(port: str) -> None:
    async def handler(packet: Packet) -> None:
        print("{}".format(packet))

    connect(handler, port)


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    if args.verbose:
        handler = logging.StreamHandler()
        protocols_logger = logging.getLogger("siobrultech_protocols")
        protocols_logger.setLevel(logging.DEBUG)
        protocols_logger.addHandler(handler)
        serial_logger = logging.getLogger("aiobrultech_serial")
        serial_logger.setLevel(logging.DEBUG)
        serial_logger.addHandler(handler)
    asyncio.get_event_loop().run_until_complete(main(args.port))
    asyncio.get_event_loop().run_forever()
