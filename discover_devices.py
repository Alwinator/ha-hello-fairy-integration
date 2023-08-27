import asyncio
from bleak import BleakScanner


async def main():
    devices = await BleakScanner.discover(cb=dict(use_bdaddr=True))
    for d in devices:
        print(d)


asyncio.run(main())
