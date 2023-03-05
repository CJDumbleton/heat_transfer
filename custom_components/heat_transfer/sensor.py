"""Sensor platform for heat_transfer."""
from __future__ import annotations
from asyncio import Lock
from dataclasses import dataclass
from datetime import timedelta
from functools import wraps
import math
from typing import Any

from homeassistant import util
from homeassistant.backports.enum import StrEnum
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITY_PICTURE_TEMPLATE,
    CONF_ICON_TEMPLATE,
    CONF_NAME,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import entity_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.template import Template
from homeassistant.loader import async_get_custom_components
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import (
    ATTR_COEFFICIENT,
    CONF_ENABLED_SENSORS,
    CONF_IN_T_SENSOR,
    CONF_OUT_T_SENSOR,
    CONF_POLL,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_TYPES,
    DEFAULT_NAME,
    DISPLAY_PRECISION,
    DOMAIN,
    LOGGER,
    POLL_DEFAULT,
    SCAN_INTERVAL_DEFAULT,
)


class SensorType(StrEnum):
    """Sensor type enum."""

    HEAT_TRANSFER_COEFFICIENT = "heat_transfer_coefficient"

    def to_name(self) -> str:
        """Return the title of the sensor type."""
        return self.value.replace("_", " ").capitalize()

    @classmethod
    def from_string(cls, string: str) -> "SensorType":
        """Return the sensor type from string."""
        if string in list(cls):
            return cls(string)
        raise ValueError(
            f"Unknown sensor type: {string}. Please check https://github.com/CJDumbleton/heat_transfer for valid options."
            )

SENSOR_TYPES = {
    SensorType.HEAT_TRANSFER_COEFFICIENT: {
        "icon": "mdi:thermometer-lines",
        "key": SensorType.HEAT_TRANSFER_COEFFICIENT,
        "name": SensorType.HEAT_TRANSFER_COEFFICIENT.to_name(),
        "native_unit_of_measurement": "1/s",
        "state_class": SensorStateClass.MEASUREMENT,
        #"suggested_display_precision": DISPLAY_PRECISION,
    }
}

DEFAULT_SENSOR_TYPES = list(SENSOR_TYPES.keys())

def compute_once_lock(sensor_type):
    """Only compute if sensor_type needs update, return just the value otherwise."""

    def wrapper(func):
        @wraps(func)
        async def wrapped(self, *args, **kwargs):
            async with self._compute_states[sensor_type].lock:
                if self._compute_states[sensor_type].needs_update:
                    setattr(self, f"_{sensor_type}", await func(self, *args, **kwargs))
                    self._compute_states[sensor_type].needs_update = False
                return getattr(self, f"_{sensor_type}", None)

        return wrapped

    return wrapper

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Heat Transfer sensors."""
    if discovery_info is None:
        devices = [
            dict(device_config, **{CONF_NAME: device_name})
            for (device_name, device_config) in config[CONF_SENSORS].items()
        ]
        options = {}
    else:
        devices = discovery_info["devices"]
        options = discovery_info["options"]

    sensors = []

    for device_config in devices:
        device_config = options | device_config
        compute_device = DeviceHeatTransfer(
            hass=hass,
            name=device_config.get(CONF_NAME),
            unique_id=device_config.get(CONF_UNIQUE_ID),
            in_temp_sensor_entity=device_config.get(CONF_IN_T_SENSOR),
            out_temp_sensor_entity=device_config.get(CONF_OUT_T_SENSOR),
            should_poll=device_config.get(CONF_POLL, POLL_DEFAULT),
            scan_interval=device_config.get(
                CONF_SCAN_INTERVAL, timedelta(seconds=SCAN_INTERVAL_DEFAULT)
            ),
        )

        sensors += [
            SensorHeatTransfer(
                device=compute_device,
                entity_description=SensorEntityDescription(
                    **SENSOR_TYPES[SensorType.from_string(sensor_type)]
                ),
                icon_template=device_config.get(CONF_ICON_TEMPLATE),
                entity_picture_template=device_config.get(CONF_ENTITY_PICTURE_TEMPLATE),
                sensor_type=SensorType.from_string(sensor_type),
                is_config_entry=False,
            )
            for sensor_type in device_config.get(
                CONF_SENSOR_TYPES, DEFAULT_SENSOR_TYPES
            )
        ]

    async_add_entities(sensors)
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    if data.get(CONF_SCAN_INTERVAL) is None:
        hass.data[DOMAIN][entry.entry_id][
            CONF_SCAN_INTERVAL
        ] = SCAN_INTERVAL_DEFAULT
        data[CONF_SCAN_INTERVAL] = SCAN_INTERVAL_DEFAULT
    LOGGER.debug("async_setup_entry: %s", data)
    compute_device = DeviceHeatTransfer(
        hass=hass,
        name=data[CONF_NAME],
        unique_id=f"{entry.unique_id}",
        in_temp_sensor_entity=data[CONF_IN_T_SENSOR],
        out_temp_sensor_entity=data[CONF_OUT_T_SENSOR],
        should_poll=data[CONF_POLL],
        scan_interval=timedelta(
            seconds=data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
        ),
    )
    entities: list[SensorHeatTransfer] = [
        SensorHeatTransfer(
            device=compute_device,
            sensor_type=sensor_type,
            entity_description=SensorEntityDescription(**SENSOR_TYPES[sensor_type]),
        )
        for sensor_type in SensorType
    ]
    if CONF_ENABLED_SENSORS in data:
        for entity in entities:
            if entity.entity_description.key not in data[CONF_ENABLED_SENSORS]:
                entity.entity_description.entity_registry_enabled_default = False

    if entities:
        async_add_entities(entities)


def id_generator(unique_id: str, sensor_type: str) -> str:
    """Generate id based on unique_id and sensor type.
    :param unique_id: str: common part of id for all entities, device unique_id, as a rule
    :param sensor_type: str: different part of id, sensor type, as s rule
    :returns: str: unique_id+sensor_type
    """
    return unique_id + sensor_type


class SensorHeatTransfer(SensorEntity):
    """heat_transfer Sensor class."""

    def __init__(
        self,
        device: "DeviceHeatTransfer",
        sensor_type: SensorType,
        entity_description: SensorEntityDescription,
        icon_template: Template = None,
        entity_picture_template: Template = None,
        is_config_entry: bool = True,
    ) -> None:
        """Initialize the sensor."""
        self._device = device
        self._sensor_type = sensor_type
        self.entity_description = entity_description
        self.entity_description.has_entity_name = is_config_entry
        if not is_config_entry:
            self.entity_description.name = (
                f"{self._device.name} {self.entity_description.name}"
            )
            if sensor_type in [SensorType.HEAT_TRANSFER_COEFFICIENT]:
                registry = entity_registry.async_get(self._device.hass)
                if sensor_type is SensorType.HEAT_TRANSFER_COEFFICIENT:
                    unique_id = id_generator(
                        self._device.unique_id,
                        SensorType.HEAT_TRANSFER_COEFFICIENT
                    )
                    entity_id = registry.async_get_entity_id(
                        SENSOR_DOMAIN,
                        DOMAIN, unique_id
                    )
                if entity_id is not None:
                    registry.async_update_entity(
                        entity_id,
                        new_unique_id=id_generator(
                            self._device.unique_id,
                            sensor_type
                        )
                    )
        self._icon_template = icon_template
        self._entity_picture_template = entity_picture_template
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self._attr_unique_id = id_generator(self._device.unique_id, sensor_type)
        self._attr_should_poll = False

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self._device.device_info

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return dict(
            self._device.extra_state_attributes, **self._attr_extra_state_attributes
        )

    async def async_added_to_hass(self):
        """Register callbacks."""
        self._device.sensors.append(self)
        if self._icon_template is not None:
            self._icon_template.hass = self.hass
        if self._entity_picture_template is not None:
            self._entity_picture_template.hass = self.hass
        if self._device.compute_states[self._sensor_type].needs_update:
            self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Update the state of the sensor."""
        value = await getattr(self._device, self._sensor_type)()
        if value is None:  # can happen during startup
            return

        if isinstance(value, tuple) and len(value) == 2:
            if self._sensor_type == SensorType.HEAT_TRANSFER_COEFFICIENT:
                self._attr_extra_state_attributes[ATTR_COEFFICIENT] = value[1]
            self._attr_native_value = value[0]
        else:
            self._attr_native_value = value

        for property_name, template in (
            ("_attr_icon", self._icon_template),
            ("_attr_entity_picture", self._entity_picture_template),
        ):
            if template is None:
                continue

            try:
                setattr(self, property_name, template.async_render())
            except TemplateError as ex:
                friendly_property_name = property_name[1:].replace("_", " ")
                if ex.args and ex.args[0].startswith(
                    "UndefinedError: 'None' has no attribute"
                ):
                    # Common during HA startup - so just a warning
                    LOGGER.warning(
                        "Could not render %s template %s, the state is unknown",
                        friendly_property_name,
                        self.name,
                    )
                    continue

                try:
                    setattr(self, property_name, getattr(super(), property_name))
                except AttributeError:
                    LOGGER.error(
                        "Could not render %s template %s: %s",
                        friendly_property_name,
                        self.name,
                        ex,
                    )


@dataclass
class ComputeState:
    """Thermal Comfort Calculation State."""

    needs_update: bool = False
    lock: Lock = None


class DeviceHeatTransfer:
    """Representation of a Heat Transfer Sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        unique_id: str,
        in_temp_sensor_entity: str,
        out_temp_sensor_entity: str,
        should_poll: bool,
        scan_interval: timedelta,
    ):
        """Initialize the sensor."""
        self.hass = hass
        self._unique_id = unique_id
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, self._unique_id)},
            name=name,
            manufacturer=DEFAULT_NAME,
            model="Virtual Device",
        )
        self.extra_state_attributes = {}
        self._in_temp_sensor_entity = in_temp_sensor_entity
        self._out_temp_sensor_entity = out_temp_sensor_entity
        self._in_temp = None
        self._out_temp = None
        self._should_poll = should_poll
        self.sensors = []
        self._compute_states = {
            sensor_type: ComputeState(lock=Lock())
            for sensor_type in SENSOR_TYPES.keys()
        }

        async_track_state_change_event(
            self.hass, self._in_temp_sensor_entity, self.temperature_state_listener
        )

        async_track_state_change_event(
            self.hass, self._out_temp_sensor_entity, self.temperature_state_listener
        )

        hass.async_create_task(
            self._new_temperature_state(hass.states.get(in_temp_sensor_entity))
        )
        hass.async_create_task(
            self._new_temperature_state(hass.states.get(out_temp_sensor_entity))
        )

        hass.async_create_task(self._set_version())

        if self._should_poll:
            if scan_interval is None:
                scan_interval = timedelta(seconds=SCAN_INTERVAL_DEFAULT)
            async_track_time_interval(
                self.hass,
                self.async_update_sensors,
                scan_interval,
            )

    async def _set_version(self):
        self._device_info["sw_version"] = (
            await async_get_custom_components(self.hass)
        )[DOMAIN].version.string

    async def temperature_state_listener(self, event):
        """Handle temperature device state changes."""
        await self._new_temperature_state(event.data.get("new_state"))

    async def _new_temperature_state(self, state):
        if _is_valid_state(state):
            hass = self.hass
            unit = state.attributes.get(
                ATTR_UNIT_OF_MEASUREMENT,
                hass.config.units.temperature_unit
            )
            temp = util.convert(state.state, float)
            # convert to celsius if necessary
            temperature = TemperatureConverter.convert(temp, unit, UnitOfTemperature.CELSIUS)
            if -89.2 <= temperature <= 56.7:
                self.extra_state_attributes[ATTR_TEMPERATURE] = temp
                self._temperature = temperature
                await self.async_update()
        else:
            LOGGER.info("Temperature has an invalid value: %s. Can't calculate new states.", state)

    @compute_once_lock(SensorType.HEAT_TRANSFER_COEFFICIENT)
    async def heat_transfer_coefficient(self) -> float:
        """Heat transfer coefficient
        <https://en.wikipedia.org/wiki/Newton's_law_of_cooling#Simplified_formulation>.
        """
        return self._out_temp - self._in_temp

    async def async_update(self):
        """Update the state."""
        if self._in_temp is not None and self._out_temp is not None:
            for sensor_type in SENSOR_TYPES.keys():
                self._compute_states[sensor_type].needs_update = True
            if not self._should_poll:
                await self.async_update_sensors(True)

    async def async_update_sensors(self, force_refresh: bool = False) -> None:
        """Update the state of the sensors."""
        for sensor in self.sensors:
            sensor.async_schedule_update_ha_state(force_refresh)

    @property
    def compute_states(self) -> dict[SensorType, ComputeState]:
        """Compute states of configured sensors."""
        return self._compute_states

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_info(self) -> dict:
        """Return the device info."""
        return self._device_info

    @property
    def name(self) -> str:
        """Return the name."""
        return self._device_info["name"]


def _is_valid_state(state) -> bool:
    if state is not None:
        if state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                return not math.isnan(float(state.state))
            except ValueError:
                pass
    return False