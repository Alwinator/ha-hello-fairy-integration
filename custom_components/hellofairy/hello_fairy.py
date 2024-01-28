# Standard imports
import asyncio
import enum
import logging
import struct
from typing import Any, Callable, cast

# 3rd party imports
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.client import BaseBleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

CONTROL_UUID = "49535343-8841-43f4-a8d4-ecbe34729bb3"


class Conn(enum.Enum):
    DISCONNECTED = 1
    UNPAIRED = 2
    PAIRING = 3
    PAIRED = 4


_LOGGER = logging.getLogger(__name__)

class Lamp:
    """The class that represents a Hello Fairy lamp
    A Lamp object describe a real world Hello Fairy lamp.
    """

    def __init__(self, ble_device: BLEDevice):
        self._client: BleakClient | None = None
        self._ble_device = ble_device
        self._mac = self._ble_device.address
        _LOGGER.debug(
            f"Initializing Hello Fairy Lamp {self._ble_device.name} ({self._mac})"
        )
        _LOGGER.debug(f"BLE_device details: {self._ble_device.details}")
        self._is_on = False
        self._rgb = (0, 0, 0)
        self._brightness = 0
        self.versions: str | None = None

        # store func to call on state received:
        self._state_callbacks: list[Callable[[], None]] = []
        self._conn = Conn.DISCONNECTED
        self._pair_resp_event = asyncio.Event()
        self._read_service = False
        self._is_client_bluez = True

    def __str__(self) -> str:
        """The string representation"""
        str_rgb = f"rgb_{self._rgb} "
        str_bri = f"bri_{self._brightness} " if self._mode else ""
        str_rep = (
            f"<Lamp {self._mac} "
            f"{'ON' if self._is_on else 'OFF'} "
            f"{str_bri}{str_rgb}"
            f">"
        )
        return str_rep

    def add_callback_on_state_changed(self, func: Callable[[], None]) -> None:
        """
        Register callbacks to be called when lamp state is received or bt disconnected
        """
        self._state_callbacks.append(func)

    def run_state_changed_cb(self) -> None:
        """Execute all registered callbacks for a state change"""
        for func in self._state_callbacks:
            func()

    def diconnected_cb(self, client: BaseBleakClient) -> None:
        _LOGGER.debug(f"Disconnected CB from client {client}")
        # ensure we are responding to the newest client:
        # if client != self._client:
        #     return
        self._mode = None  # lamp not available
        self._conn = Conn.DISCONNECTED
        self.run_state_changed_cb()

    async def connect(self, num_tries: int = 3) -> None:
        if (
            self._client and not self._client.is_connected
        ):  # check the connection has not dropped
            await self.disconnect()
        if self._conn == Conn.PAIRING or self._conn == Conn.PAIRED:
            # We do not try to reconnect if we are disconnected or unpaired
            return
        _LOGGER.debug("Initiating new connection")
        try:
            if self._client:
                await self.disconnect()

            _LOGGER.debug(f"Connecting now to {self._ble_device}:...")
            self._client = await establish_connection(
                BleakClient,
                device=self._ble_device,
                name=self._mac,
                disconnected_callback=self.diconnected_cb,
                max_attempts=4,
            )
            _LOGGER.debug(
                f"Client used is: {self._client}. Backend is {self._client._backend}"
            )
            self._is_client_bluez = (
                str(type(self._client._backend))
                == "<class 'bleak.backends.bluezdbus.client.BleakClientBlueZDBus'>"
            )
            self._conn = Conn.UNPAIRED
            _LOGGER.debug(f"Connected: {self._client.is_connected}")

            # read services if in debug mode:
            if not self._read_service and _LOGGER.isEnabledFor(logging.DEBUG):
                await self.read_services()
                self._read_service = True
                await asyncio.sleep(0.2)

            # It may be that on bluez the notification request is not sent properly
            # Not sure on esp... so only applyt to bluez
            _LOGGER.debug("Request Pairing")
            await self.pair()
            # since we have no feedback
            # we wait longer on first connection in case need to push button...
            await asyncio.sleep(0.3)
            # now we are assuming that we paired successfully
            self._conn = Conn.PAIRED
            # ensure we get state straight away after connection
            await self.get_state()
            # advertise to HA lamp is now available:
            self.run_state_changed_cb()

            _LOGGER.debug(f"Connection status: {self._conn}")

        except asyncio.TimeoutError:
            _LOGGER.error("Connection Timeout error")
        except BleakError as err:
            _LOGGER.error(f"Connection: BleakError: {err}")

    async def pair(self) -> None:
        """Send pairing command directly"""
        # bits = bytearray(struct.pack("BBB15x", COMMAND_STX, CMD_PAIR, CMD_PAIR_ON))
        if self._conn != Conn.UNPAIRED or self._client is None:
            _LOGGER.error("Pairing: Cannot request pair as not connected")
            return
        try:
            # Send pairing event
            # await self._client.write_gatt_char(CONTROL_UUID, bits)
            pass
        except asyncio.TimeoutError:
            _LOGGER.error("Pairing: Timeout error")
        except BleakError as err:
            _LOGGER.error(f"Pairing: BleakError: {err}")

    async def disconnect(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.disconnect()
        except asyncio.TimeoutError:
            _LOGGER.error("Disconnection: Timeout error")
        except BleakError as err:
            _LOGGER.error(f"Disconnection: BleakError: {err}")
        self._conn = Conn.DISCONNECTED

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def available(self) -> bool:
        return self._conn == Conn.PAIRED

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def brightness(self) -> int:
        return self._brightness

    @property
    def color(self) -> tuple[int, int, int]:
        return self._rgb

    def get_prop_min_max(self) -> dict[str, Any]:
        return {
            "brightness": {"min": 0, "max": 100},
            "color": {"min": 0, "max": 255},
        }

    async def send_cmd(self, bits: bytes, wait_notif: float = 0.5) -> bool:
        await self.connect()
        if self._conn == Conn.PAIRED and self._client is not None:
            try:
                await self._client.write_gatt_char(CONTROL_UUID, bytearray(bits))
                await asyncio.sleep(wait_notif)
                return True
            except asyncio.TimeoutError:
                _LOGGER.error("Send Cmd: Timeout error")
            except BleakError as err:
                _LOGGER.error(f"Send Cmd: BleakError: {err}")
        return False

    async def get_state(self) -> None:
        """Request the state of the lamp (send back state through notif)"""
        # bits = struct.pack("BBB15x", COMMAND_STX, CMD_GETSTATE, CMD_GETSTATE_SEC)
        # _LOGGER.debug("Send Cmd: Get_state")
        # await self.send_cmd(bits)

    async def turn_on(self) -> None:
        """Turn the lamp on. (send back state through notif)"""
        bits = bytes.fromhex("aa020101bb")
        _LOGGER.debug("Send Cmd: Turn On")
        await self.send_cmd(bits)

    async def turn_off(self) -> None:
        """Turn the lamp off. (send back state through notif)"""
        bits = bytes.fromhex("aa020100bb")
        _LOGGER.debug("Send Cmd: Turn Off")
        await self.send_cmd(bits)

    # set_brightness/temperature/color do NOT send a notification back.
    # However, the lamp takes time to transition to new state
    # and if another command (including get_state) is sent during that time,
    # it stops the transition where it is...
    async def set_brightness(self, brightness: int) -> None:
        """Set the brightness [1-100] (no notif)"""
        brightness = min(100, max(0, int(brightness)))
        _LOGGER.debug(f"Set_brightness {brightness}")
        bits = bytes.fromhex("aa030701001403e8038cbb")
        _LOGGER.debug("Send Cmd: Brightness")
        if await self.send_cmd(bits, wait_notif=0):
            self._brightness = brightness

    async def set_color(
        self, red: int, green: int, blue: int, brightness: int | None = None
    ) -> None:
        """Set the color of the lamp [0-255] (no notif)"""
        if brightness is None:
            brightness = self._brightness
        _LOGGER.debug(f"Set_color {(red, green, blue)}, {brightness}")
        bits = bytes.fromhex(
            "aa030701001403e8038cbb"
        )
        _LOGGER.debug("Send Cmd: Color")
        if await self.send_cmd(bits, wait_notif=0):
            self._rgb = (red, green, blue)
            self._brightness = brightness

    async def read_services(self) -> None:
        if self._client is None:
            return
        for service in self._client.services:
            _LOGGER.info(f"[Service] {service}")
            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = bytes(await self._client.read_gatt_char(char.uuid))
                        _LOGGER.info(
                            f"__[Characteristic] {char} ({','.join(char.properties)}), Value: {str(value)}"
                        )
                    except Exception as e:
                        _LOGGER.error(
                            f"__[Characteristic] {char} ({','.join(char.properties)}), Value: {e}"
                        )

                else:
                    value = None
                    _LOGGER.info(
                        f"__[Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                    )

                for descriptor in char.descriptors:
                    try:
                        value = bytes(
                            await self._client.read_gatt_descriptor(descriptor.handle)
                        )
                        _LOGGER.info(
                            f"____[Descriptor] {descriptor}) | Value: {str(value)}"
                        )
                    except Exception as e:
                        _LOGGER.error(f"____[Descriptor] {descriptor}) | Value: {e}")


async def find_device_by_address(
    address: str, timeout: float = 20.0
) -> BLEDevice | None:
    from bleak import BleakScanner

    return await BleakScanner.find_device_by_address(address.upper(), timeout=timeout)


async def discover_hello_fairy_lamps(
    scanner: type[BleakScanner] | None = None,
) -> list[dict[str, Any]]:
    """Scanning feature
    Scan the BLE neighborhood for an Yeelight lamp
    This method requires the script to be launched as root
    Returns the list of nearby lamps
    """
    lamp_list = []
    scanner = scanner if scanner is not None else BleakScanner

    devices = await scanner.discover()
    for d in devices:
        lamp_list.append({"ble_device": d})
        _LOGGER.info(f"found {d.name} with mac: {d.address}, details:{d.details}")
    return lamp_list


if __name__ == "__main__":

    import sys

    # bleak backends are very loud, this reduces the log spam when using --debug
    logging.getLogger("bleak.backends").setLevel(logging.WARNING)
    # start the logger to stdout
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    _LOGGER.info("HELLO_FAIRY_BT scanning starts")

    # start discovery:
    # lamp_list = asyncio.run(discover_yeelight_lamps())
    # _LOGGER.info("YEELIGHT_BT scanning ends")
    # from bleak import BleakScanner
    # device = asyncio.run( BleakScanner.find_device_by_address("F8:24:41:E6:3E:39", timeout=20.0))
    # print("DEVICE:")
    # print(device)
    # print("DEVICE END")
    # lamp_list = [device]

    # # now try to connect to the lamp
    # if not lamp_list:
    #     exit

    async def test_light() -> None:

        device = await find_device_by_address("F8:24:41:E6:3E:39")
        if device is None:
            print("No device found")
            return
        lamp_list = [{"ble_device": device}]

        lamp = Lamp(cast(BLEDevice, lamp_list[0]["ble_device"]))
        await lamp.connect()
        await asyncio.sleep(2.0)
        await lamp.turn_on()
        await asyncio.sleep(2.0)
        await lamp.turn_off()
        await asyncio.sleep(2.0)
        await lamp.turn_on()
        await asyncio.sleep(2.0)
        await lamp.set_brightness(20)
        await asyncio.sleep(1.0)
        await lamp.set_brightness(70)
        await asyncio.sleep(2.0)
        await lamp.set_color(red=100, green=250, blue=50)
        await asyncio.sleep(2.0)
        await lamp.turn_off()
        await asyncio.sleep(2.0)
        await lamp.disconnect()
        await asyncio.sleep(2.0)

    asyncio.run(test_light())
    print("The end")