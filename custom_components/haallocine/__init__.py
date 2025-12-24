"""The HAAllocine integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import AllocineCoordinator
from .services import AllocineServicesSetup

_LOGGER = logging.getLogger(__name__)

type MyConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold runtime data."""

    coordinator: AllocineCoordinator


async def async_setup_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Set up HAAllocine from a config entry."""
    _LOGGER.info("Setting up HAAllocine integration")

    # Initialize coordinator
    coordinator = AllocineCoordinator(hass, config_entry)

    # Perform first refresh
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        raise ConfigEntryNotReady("Failed to fetch initial data from Allocine")

    # Store in runtime data
    config_entry.runtime_data = RuntimeData(coordinator=coordinator)

    # Setup services
    AllocineServicesSetup(hass)

    # Media source is automatically discovered via async_get_media_source
    # HTTP view is registered in media_source.py

    _LOGGER.info("HAAllocine integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Unload integration and clean up resources."""
    _LOGGER.info("Unloading HAAllocine integration")

    # Shutdown coordinator (cancel scheduled updates)
    coordinator = config_entry.runtime_data.coordinator
    await coordinator.async_shutdown()

    # Remove services
    for service in hass.services.async_services_for_domain(DOMAIN):
        hass.services.async_remove(DOMAIN, service)

    return True
