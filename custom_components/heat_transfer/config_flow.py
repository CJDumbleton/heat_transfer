"""Adds config flow for Heat Transfer."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.components.input_number import (
    DOMAIN as INPUT_NUMBER_DOMAIN
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    CONF_IN_T_SENSOR,
    CONF_OUT_T_SENSOR,
    DEFAULT_NAME,
    DOMAIN,
    LOGGER,
    UnknownEntity,
)
from .sensor import (
    SensorType
)


# Source https://github.com/dolezsa/thermal_comfort/blob/master/custom_components/thermal_comfort/config_flow.py
def get_sensors_by_device_class(
    _hass: HomeAssistant,
    device_class: SensorDeviceClass,
    include_all: bool = False,
) -> list:
    """Get sensors of required class from entity registry."""

    def filter_by_device_class(
        _state: State, _list: list[SensorDeviceClass], should_be_in: bool = True
    ) -> bool:
        """Filter state objects by device class.
        :param _state: state object for examination
        :param _list: list of device classes
        :param should_be_in: should the object's device_class be in the list
        to pass the filter or not
        """
        collected_device_class = _state.attributes.get(
            "device_class", _state.attributes.get("original_device_class")
        )
        # XNOR
        return not ((collected_device_class in _list) ^ should_be_in)

    def filter_for_device_class_sensor(state: State) -> bool:
        """Filter states by Platform.SENSOR and required device class."""
        return state.domain == Platform.SENSOR and filter_by_device_class(
            state, [device_class], should_be_in=True
        )

    def filter_useless_device_class(state: State) -> bool:
        """Filter out states with useless for us device class."""
        device_class_for_exclude = [
            SensorDeviceClass.AQI,
            SensorDeviceClass.BATTERY,
            SensorDeviceClass.CO,
            SensorDeviceClass.CO2,
            SensorDeviceClass.CURRENT,
            SensorDeviceClass.DATE,
            SensorDeviceClass.ENERGY,
            SensorDeviceClass.FREQUENCY,
            SensorDeviceClass.GAS,
            SensorDeviceClass.ILLUMINANCE,
            SensorDeviceClass.MONETARY,
            SensorDeviceClass.NITROGEN_DIOXIDE,
            SensorDeviceClass.NITROGEN_MONOXIDE,
            SensorDeviceClass.NITROUS_OXIDE,
            SensorDeviceClass.OZONE,
            SensorDeviceClass.PM1,
            SensorDeviceClass.PM10,
            SensorDeviceClass.PM25,
            SensorDeviceClass.POWER_FACTOR,
            SensorDeviceClass.POWER,
            SensorDeviceClass.PRESSURE,
            SensorDeviceClass.SIGNAL_STRENGTH,
            SensorDeviceClass.SULPHUR_DIOXIDE,
            SensorDeviceClass.TIMESTAMP,
            SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
            SensorDeviceClass.VOLTAGE,
        ]
        return filter_by_device_class(
            state, device_class_for_exclude, should_be_in=False
        )

    def filter_useless_domain(state: State) -> bool:
        """Filter states with useless for us domains."""
        domains_for_exclude = [
            Platform.AIR_QUALITY,
            Platform.ALARM_CONTROL_PANEL,
            Platform.BINARY_SENSOR,
            Platform.BUTTON,
            Platform.CALENDAR,
            Platform.CAMERA,
            Platform.CLIMATE,
            Platform.COVER,
            Platform.DEVICE_TRACKER,
            Platform.FAN,
            Platform.GEO_LOCATION,
            Platform.IMAGE_PROCESSING,
            Platform.LIGHT,
            Platform.LOCK,
            Platform.MAILBOX,
            Platform.MEDIA_PLAYER,
            Platform.NOTIFY,
            Platform.REMOTE,
            Platform.SCENE,
            Platform.SIREN,
            Platform.STT,
            Platform.SWITCH,
            Platform.TTS,
            Platform.VACUUM,
            "automation",
            "person",
            "script",
            "scene",
            "sun",
            "timer",
            "zone",
        ]
        return state.domain not in domains_for_exclude

    def filter_useless_units(state: State) -> bool:
        """Filter out states with useless for us units of measurements."""
        units_for_exclude = [
            # Electric
            "W",
            "kW",
            "VA",
            "BTU/h" "Wh",
            "kWh",
            "MWh",
            "mA",
            "A",
            "mV",
            "V",
            # Degree units
            "°",
            # Currency units
            "€",
            "$",
            "¢",
            # Time units
            "μs",
            "ms",
            "s",
            "min",
            "h",
            "d",
            "w",
            "m",
            "y",
            # Length units
            "mm",
            "cm",
            "m",
            "km",
            "in",
            "ft",
            "yd",
            "mi",
            # Frequency units
            "Hz",
            "kHz",
            "MHz",
            "GHz",
            # Pressure units
            "Pa",
            "hPa",
            "kPa",
            "bar",
            "cbar",
            "mbar",
            "mmHg",
            "inHg",
            "psi",
            # Sound pressure units
            "dB",
            "dBa",
            # Volume units
            "L",
            "mL",
            "m³",
            "ft³",
            "gal",
            "fl. oz.",
            # Volume Flow Rate units
            "m³/h",
            "ft³/m",
            # Area units
            "m²",
            # Mass
            "g",
            "kg",
            "mg",
            "µg",
            "oz",
            "lb",
            #
            "µS/cm",
            "lx",
            "UV index",
            "W/m²",
            "BTU/(h×ft²)",
            # Precipitation units
            "mm/h",
            "in",
            "in/h",
            # Concentration units
            "µg/m³",
            "mg/m³",
            "μg/ft³",
            "p/m³",
            "ppm",
            "ppb",
            # Speed units
            "mm/d",
            "in/d",
            "m/s",
            "in/h",
            "km/h",
            "mph",
            # Signal_strength units
            "dB",
            "dBm",
            # Data units
            "bit",
            "kbit",
            "Mbit",
            "Gbit",
            "B",
            "kB",
            "MB",
            "GB",
            "TB",
            "PB",
            "EB",
            "ZB",
            "YB",
            "KiB",
            "MiB",
            "GiB",
            "TiB",
            "PiB",
            "EiB",
            "ZiB",
            "YiB",
            "bit/s",
            "kbit/s",
            "Mbit/s",
            "Gbit/s",
            "B/s",
            "kB/s",
            "MB/s",
            "GB/s",
            "KiB/s",
            "MiB/s",
            "GiB/s",
        ]
        additional_units = {
            SensorDeviceClass.HUMIDITY: ["°C", "°F", "K"],
            SensorDeviceClass.TEMPERATURE: ["%"],
        }
        units_for_exclude += additional_units.get(device_class, [])

        unit_of_measurement = state.attributes.get(
            "unit_of_measurement", state.attributes.get("native_unit_of_measurement")
        )
        return unit_of_measurement not in units_for_exclude

    def filter_thermal_comfort_ids(entity_id: str) -> bool:
        """Filter out device_ids containing our SensorType."""
        return all(sensor_type not in entity_id for sensor_type in SensorType)

    filters_for_additional_sensors: list[callable] = [
        filter_useless_device_class,
        filter_useless_domain,
        filter_useless_units,
    ]

    result = [
        state.entity_id
        for state in filter(
            filter_for_device_class_sensor,
            _hass.states.async_all(),
        )
    ]

    result.sort()
    LOGGER.debug(
        "Results for %s based on device class: %s",
        device_class,
        result,
    )

    if include_all:
        additional_sensors = _hass.states.async_all()
        for f in filters_for_additional_sensors:
            additional_sensors = list(filter(f, additional_sensors))

        additional_entity_ids = [state.entity_id for state in additional_sensors]
        additional_entity_ids = list(set(additional_entity_ids) - set(result))
        additional_entity_ids.sort()
        LOGGER.debug("Additional results: %s", additional_entity_ids)
        result += additional_entity_ids

    result = list(
        filter(
            filter_thermal_comfort_ids,
            result,
        )
    )

    LOGGER.debug("Results after cleaning own entities: %s", result)

    return result


# Source: https://github.com/dolezsa/thermal_comfort/blob/master/custom_components/thermal_comfort/config_flow.py
def get_value(
    config_entry: config_entries.ConfigEntry | None, param: str, default=None
):
    """Get current value for configuration parameter.

    :param config_entry: config_entries|None: config entry from Flow
    :param param: str: parameter name for getting value
    :param default: default value for parameter, defaults to None
    :returns: parameter value, or default value or None
    """
    if config_entry is not None:
        return config_entry.options.get(param, config_entry.data.get(param, default))
    else:
        return default


def build_schema(
    config_entry: config_entries.ConfigEntry | None,
    hass: HomeAssistant,
) -> vol.Schema:
    """Build configuration schema.

    :param config_entry: config entry for getting current parameters or None
    :param hass: Home Assistant instance
    :return: Configuration schema with default parameters
    """
    temperature_sensors = get_sensors_by_device_class(
        hass,
        SensorDeviceClass.TEMPERATURE,
        False,
    )

    if not temperature_sensors:
        return None

    schema = vol.Schema({
        vol.Required(
            CONF_NAME, default=get_value(
                config_entry,
                CONF_NAME,
                DEFAULT_NAME
            )
        ): str,
        vol.Required(
            CONF_IN_T_SENSOR, default=get_value(
                config_entry,
                CONF_IN_T_SENSOR,
                temperature_sensors[0]
            ),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN],
                include_entities=temperature_sensors
            ),
        ),
        vol.Required(
            CONF_OUT_T_SENSOR, default=get_value(
                config_entry,
                CONF_OUT_T_SENSOR,
                temperature_sensors[0]
            ),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN],
                include_entities=temperature_sensors
            ),
        ),
    })
    return schema


class HeatTransferFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Heat Transfer."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._validate_input(user_input)
            except UnknownEntity as err:
                _errors[str(err)] = "unknown_entity"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_IN_T_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN]
                        ),
                    ),
                    vol.Required(CONF_OUT_T_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN]
                        ),
                    )
                }
            ),
            errors=_errors,
        )

    async def _validate_input(self, data: dict) -> None:
        """Validate the user's inputs are usable entities."""
        for conf in [
            CONF_IN_T_SENSOR,
            CONF_OUT_T_SENSOR,
        ]:
            input_data = data.get(conf, None)
            if (input_data is not None
                    and self.hass.states.get(input_data)) is None:
                LOGGER.error(
                    "Error: entity id %s doesn't have any state.",
                    input_data,
                )
                raise UnknownEntity(conf)
