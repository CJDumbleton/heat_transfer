"""Constants for heat_transfer."""
from logging import Logger, getLogger

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

LOGGER: Logger = getLogger(__package__)

DOMAIN = "heat_transfer"
NAME = "Heat Transfer"
VERSION = "0.0.0"

ATTR_COEFFICIENT = "coefficient"
CONF_ENABLED_SENSORS = "enabled_sensors"
CONF_IN_T_SENSOR = "in_temp_sensor_entity_id"
CONF_OUT_T_SENSOR = "out_temp_sensor_entity_id"
CONF_POLL = "poll"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SENSOR_TYPES = "sensor_types"
DEFAULT_NAME = "Heat transfer coefficient"
DISPLAY_PRECISION = 2
POLL_DEFAULT = False
SCAN_INTERVAL_DEFAULT = 30

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="heat_transfer",
        name="Heat transfer coefficient Sensor",
        icon="mdi:thermometer-lines",
    ),
)

SENSOR_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_POLL): cv.boolean,
        vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_SENSOR_TYPES): cv.ensure_list,
    },
    extra=vol.REMOVE_EXTRA,
)

OPTIONS_SCHEMA = vol.Schema({}).extend(
    SENSOR_OPTIONS_SCHEMA.schema,
    extra=vol.REMOVE_EXTRA,
)

class UnknownEntity(HomeAssistantError):
    """Error to indicate there is an unknown entity_id given."""
