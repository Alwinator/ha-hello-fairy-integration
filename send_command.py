import asyncio
from bleak import BleakClient

address = "48:53:52:01:D6:40"
MODEL_NBR_UUID = "2A24"


async def main(address):
    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")

        paired = await client.pair(protection_level=2)
        print(f"Paired: {paired}")


asyncio.run(main(address))
