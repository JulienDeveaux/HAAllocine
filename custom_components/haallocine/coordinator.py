"""DataUpdateCoordinator for HAAllocine."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .allocine_api import AllocineAPI, AllocineConnectionError, AllocineMovie, AllocineParseError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AllocineCoordinator(DataUpdateCoordinator[list[AllocineMovie]]):
    """Coordinator for Allocine data with Wednesday scheduling."""

    data: list[AllocineMovie]

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Initialize coordinator WITHOUT update_interval (manual scheduling)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_method=self.async_update_data,
            # NO update_interval - we manually schedule
        )

        # Initialize API with cache directory
        cache_dir = Path(hass.config.path(".cache", "haallocine"))
        self.api = AllocineAPI(cache_dir)

        # Track scheduled update
        self._scheduled_update = None

    async def async_update_data(self) -> list[AllocineMovie]:
        """Fetch data from Allocine (called on first refresh and manual updates)."""
        _LOGGER.info("Starting Allocine data update")

        try:
            # Clear old cache before fetching new data
            await self.hass.async_add_executor_job(self.api.clear_cache)

            # Scrape weekly releases (blocking operation)
            movies = await self.hass.async_add_executor_job(
                self.api.scrape_weekly_releases
            )

            _LOGGER.info("Successfully scraped %d movies from Allocine", len(movies))

            # Schedule next Wednesday update after successful fetch
            self._schedule_next_wednesday_update()

            return movies

        except AllocineConnectionError as err:
            _LOGGER.error("Connection error: %s", err)
            raise UpdateFailed(f"Failed to connect to Allocine: {err}") from err
        except AllocineParseError as err:
            _LOGGER.error("Parse error: %s", err)
            raise UpdateFailed(f"Failed to parse Allocine data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during update")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _schedule_next_wednesday_update(self) -> None:
        """Schedule update for next Wednesday at 03:00."""
        # Cancel existing scheduled update
        if self._scheduled_update:
            self._scheduled_update.cancel()
            self._scheduled_update = None

        # Calculate next Wednesday
        now = datetime.now()
        days_until_wednesday = (2 - now.weekday()) % 7  # Wednesday is 2

        if days_until_wednesday == 0:
            # Today is Wednesday - schedule for next week
            days_until_wednesday = 7

        next_wednesday = now + timedelta(days=days_until_wednesday)
        next_wednesday = next_wednesday.replace(
            hour=3, minute=0, second=0, microsecond=0
        )

        seconds_until_wednesday = (next_wednesday - now).total_seconds()

        _LOGGER.info(
            "Scheduling next update for %s (in %.1f hours)",
            next_wednesday.strftime("%Y-%m-%d %H:%M"),
            seconds_until_wednesday / 3600,
        )

        # Schedule update using event loop
        self._scheduled_update = self.hass.loop.call_later(
            seconds_until_wednesday,
            lambda: self.hass.create_task(self.async_request_refresh()),
        )

    async def async_shutdown(self) -> None:
        """Cancel scheduled updates on shutdown."""
        _LOGGER.info("Shutting down coordinator and canceling scheduled updates")
        if self._scheduled_update:
            self._scheduled_update.cancel()
            self._scheduled_update = None
