"""Sensor platform for heat_transfer."""
from __future__ import annotations

from homeassistant.backports.enum import StrEnum
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .const import DOMAIN
from .coordinator import BlueprintDataUpdateCoordinator
from .entity import HeatTransferEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="heat_transfer",
        name="Heat transfer coefficient Sensor",
        icon="mdi:format-quote-close",
    ),
)


# Source https://github.com/dolezsa/thermal_comfort/blob/master/custom_components/thermal_comfort/sensor.py
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
        else:
            raise ValueError(
                f"Unknown sensor type: {string}. Please check https://github.com/CJDumbleton/heat_transfer for valid options."
            )


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        HeatTransferSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class HeatTransferSensor(HeatTransferEntity, SensorEntity):
    """heat_transfer Sensor class."""

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self.coordinator.data.get("body")
