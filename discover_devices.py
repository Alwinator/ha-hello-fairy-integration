import asyncio
import time

from bleak import BleakScanner, BleakClient

from test import convert_rgb


async def main():
    devices = await BleakScanner.discover(cb=dict(use_bdaddr=True))
    for d in devices:
        if d.name and "Hello Fairy" in d.name:
            print(d)
            print(d.metadata, d.details)
            client = BleakClient(d)
            print(f"Connected: {client.is_connected}")

            paired = await client.connect()
            print(f"Connected: {client.is_connected}")

            # for k, d in (await client.get_services()).characteristics.items():
            #     print(d)

            await client.write_gatt_char("49535343-8841-43f4-a8d4-ecbe34729bb3", bytes.fromhex("aa020101bb"), response=False)
            await client.write_gatt_char("49535343-8841-43f4-a8d4-ecbe34729bb3", bytes.fromhex("aa030701001403e8038cbb"), response=False)

            time.sleep(5)
            await client.write_gatt_char("49535343-8841-43f4-a8d4-ecbe34729bb3", bytes.fromhex("aa020100bb"),
                                         response=False)


asyncio.run(main())
