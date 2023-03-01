"""Adds config flow for Heat Transfer."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.input_number import (
    DOMAIN as INPUT_NUMBER_DOMAIN
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_IN_T_SENSOR,
    CONF_OUT_T_SENSOR,
    DOMAIN,
    LOGGER,
    UnknownEntity,
)


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
            d = data.get(conf, None)  # pylint: disable=invalid-name
            if input is not None and self.hass.states.get(d) is None:
                LOGGER.error(
                    "Error: entity id %s doesn't have any state.",
                    d,
                )
                raise UnknownEntity(conf)
