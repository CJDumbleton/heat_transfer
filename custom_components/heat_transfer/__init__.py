"""
Custom integration to integrate heat_transfer with Home Assistant.

For more details about this integration, please refer to
https://github.com/cjdumbleton/heat_transfer
"""
from __future__ import annotations

from homeassistant.config import async_hass_config_yaml
from homeassistant.config import async_process_component_config
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform, SERVICE_RELOAD
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import discovery
from homeassistant.helpers.reload import async_reload_integration_platforms
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .config_flow import get_value
from .const import (
    CONF_ENABLED_SENSORS,
    CONF_IN_T_SENSOR,
    CONF_OUT_T_SENSOR,
    CONF_POLL,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
    OPTIONS_SCHEMA,
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Transfer integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NAME: get_value(entry, CONF_NAME),
        CONF_IN_T_SENSOR: get_value(entry, CONF_IN_T_SENSOR),
        CONF_OUT_T_SENSOR: get_value(entry, CONF_OUT_T_SENSOR),
        CONF_POLL: get_value(entry, CONF_POLL),
        CONF_SCAN_INTERVAL: get_value(entry, CONF_SCAN_INTERVAL),
    }
    if get_value(entry, CONF_ENABLED_SENSORS):
        hass.data[DOMAIN][entry.entry_id][CONF_ENABLED_SENSORS] = get_value(
            entry, CONF_ENABLED_SENSORS
        )
        data = dict(entry.data)
        data.pop(CONF_ENABLED_SENSORS)
        hass.config_entries.async_update_entry(entry, data=data)
    if entry.unique_id is None:
        # We have no unique_id yet, let's use backup.
        hass.config_entries.async_update_entry(entry, unique_id=entry.entry_id)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options from user interface."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry,
                                                                    PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the thermal_comfort integration."""
    if DOMAIN in config:
        await _process_config(hass, config)

    async def _reload_config(call: Event | ServiceCall) -> None:
        """Reload top-level + platforms."""
        try:
            unprocessed_conf = await async_hass_config_yaml(hass)
        except HomeAssistantError as err:
            LOGGER.error(err)
            return

        conf = await async_process_component_config(
            hass, unprocessed_conf, await async_get_integration(hass, DOMAIN)
        )

        if conf is None:
            return

        await async_reload_integration_platforms(hass, DOMAIN, PLATFORMS)

        if DOMAIN in conf:
            await _process_config(hass, conf)

        hass.bus.async_fire(f"event_{DOMAIN}_reloaded", context=call.context)

    hass.helpers.service.async_register_admin_service(
        DOMAIN, SERVICE_RELOAD, _reload_config
    )

    return True

async def _process_config(hass: HomeAssistant, hass_config: ConfigType) -> None:
    """Process config."""
    for conf_section in hass_config[DOMAIN]:
        for platform_domain in PLATFORMS:
            if platform_domain in conf_section:
                hass.async_create_task(
                    discovery.async_load_platform(
                        hass,
                        platform_domain,
                        DOMAIN,
                        {
                            "devices": conf_section[platform_domain],
                            "options": OPTIONS_SCHEMA(conf_section),
                        },
                        hass_config,
                    )
                )