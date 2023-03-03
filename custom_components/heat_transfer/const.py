"""Constants for heat_transfer."""
from logging import Logger, getLogger

from homeassistant.exceptions import HomeAssistantError

LOGGER: Logger = getLogger(__package__)

DOMAIN = "heat_transfer"
NAME = "Heat Transfer"
VERSION = "0.0.0"

CONF_IN_T_SENSOR = "in_temp_sensor_entity_id"
CONF_OUT_T_SENSOR = "out_temp_sensor_entity_id"

DEFAULT_NAME = "Heat transfer coefficient"

class UnknownEntity(HomeAssistantError):
    """Error to indicate there is an unknown entity_id given."""
