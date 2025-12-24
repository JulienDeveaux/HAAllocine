"""HTTP view for serving Allocine posters."""

from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web
from aiohttp.web import HTTPNotFound

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AllocinePosterView(HomeAssistantView):
    """View to serve poster images."""

    url = "/api/haallocine/poster/{movie_id}"
    name = "api:haallocine:poster"
    requires_auth = False  # Media players need unauthenticated access

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize view."""
        self.hass = hass

    async def get(self, request: web.Request, movie_id: str) -> web.Response:
        """Serve poster image."""
        # Strip .jpg extension if present
        movie_id = movie_id.replace(".jpg", "")

        _LOGGER.debug("Serving poster for movie ID: %s", movie_id)

        # Get coordinator from runtime data
        if not (config_entries := self.hass.config_entries.async_loaded_entries(DOMAIN)):
            raise HTTPNotFound

        coordinator = config_entries[0].runtime_data.coordinator

        # Find movie in coordinator data
        movie = next(
            (m for m in coordinator.data if m.id == movie_id),
            None,
        )

        if not movie or not movie.local_poster_path:
            _LOGGER.warning("Poster not found for movie ID: %s", movie_id)
            return web.Response(status=404, text="Poster not found")

        # Serve image file
        poster_path = Path(movie.local_poster_path)
        if not poster_path.exists():
            _LOGGER.warning("Poster file does not exist: %s", poster_path)
            return web.Response(status=404, text="Poster file not found")

        _LOGGER.debug("Serving poster from: %s", poster_path)
        return web.FileResponse(poster_path)
