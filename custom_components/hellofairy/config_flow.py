"""Config flow for hello-fairy."""
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow

from .const import DOMAIN


def _is_supported(discovery_info: BluetoothServiceInfo) -> bool:
    """Check if device is supported."""
    print(discovery_info)

    # discovery_info.manufacturer_data
    return True


async def get_devices(hass: HomeAssistant):
    service_info = async_discovered_service_info(hass)
    print(service_info)
    for discovery_info in service_info:
        if not _is_supported(discovery_info):
            continue

    return []


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""

    devices = await hass.async_add_executor_job(get_devices, hass)
    return len(devices) > 0


config_entry_flow.register_discovery_flow(DOMAIN, "hello-fairy", _async_has_devices)
