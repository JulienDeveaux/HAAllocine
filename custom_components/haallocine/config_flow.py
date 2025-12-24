"""Config flow for HAAllocine."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AllocineConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for HAAllocine."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Config flow user step called")

        # Check if already configured (single instance only)
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            _LOGGER.info("Creating HAAllocine config entry")
            return self.async_create_entry(
                title="Allocine Weekly Releases",
                data={},
            )

        # Show empty form (no configuration needed)
        return self.async_show_form(step_id="user")
