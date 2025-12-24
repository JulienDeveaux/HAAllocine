"""Services for HAAllocine integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_REFRESH

_LOGGER = logging.getLogger(__name__)


class AllocineServicesSetup:
    """Handle HAAllocine services."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize services."""
        self.hass = hass
        self.setup_services()

    def setup_services(self) -> None:
        """Register services."""
        _LOGGER.debug("Registering HAAllocine services")

        self.hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            self.async_manual_refresh,
        )

        _LOGGER.info("HAAllocine services registered")

    async def async_manual_refresh(self, service_call: ServiceCall) -> None:
        """Manually refresh Allocine data."""
        _LOGGER.info("Manual refresh triggered")

        # Get all config entries
        config_entries = self.hass.config_entries.async_entries(DOMAIN)

        if not config_entries:
            _LOGGER.warning("No HAAllocine config entries found for refresh")
            return

        for config_entry in config_entries:
            coordinator = config_entry.runtime_data.coordinator
            _LOGGER.debug("Refreshing coordinator for entry: %s", config_entry.title)
            await coordinator.async_request_refresh()

        _LOGGER.info("Manual refresh completed")
