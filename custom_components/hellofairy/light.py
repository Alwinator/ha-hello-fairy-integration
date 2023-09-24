"""Platform for light integration."""
from __future__ import annotations

import logging
from typing import Any

from bleak import BleakScanner, BleakClient, BLEDevice
from homeassistant.components.light import (PLATFORM_SCHEMA, LightEntity)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# User config
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({

})

BLUETOOTH_SERVICE = '49535343-8841-43f4-a8d4-ecbe34729bb3'
COMMANDS = {
    "on": bytes.fromhex("aa020101bb"),
    "off": bytes.fromhex("aa020100bb"),
    "white": bytes.fromhex("aa03070100000000038cbb"),
}


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    devices = await BleakScanner.discover(cb=dict(use_bdaddr=True))
    fairy_devices = []

    for d in devices:
        if d.name and "Hello Fairy" in d.name:
            fairy_devices.append(FairyLight(d))

    async_add_entities(fairy_devices)


class FairyLight(LightEntity):
    """Representation of a Fairy Light."""


    def __init__(self, bluetooth_device: BLEDevice) -> None:
        """Initialize an FairyLight."""
        self._bluetooth_device = bluetooth_device
        self._client = BleakClient(bluetooth_device)
        self._name = bluetooth_device.name
        self._state = None
        self._brightness = None

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    async def _send_command(self, command: str):
        await self._client.write_gatt_char(
            BLUETOOTH_SERVICE,
            bytes.fromhex(COMMANDS[command]),
            response=False)

    @property
    def brightness(self):
        """Return the brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._send_command("on")
        # self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._send_command("off")

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        # self._light.update()
        # self._state = self._light.is_on()
        # self._brightness = self._light.brightness
        pass
