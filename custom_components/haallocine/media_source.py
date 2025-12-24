"""Media source for HAAllocine posters."""

from __future__ import annotations

import logging

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .http_view import AllocinePosterView

_LOGGER = logging.getLogger(__name__)


async def async_get_media_source(hass: HomeAssistant) -> AllocineMediaSource:
    """Set up Allocine media source."""
    _LOGGER.debug("Setting up Allocine media source")
    # Register HTTP view for serving posters (like Immich does)
    hass.http.register_view(AllocinePosterView(hass))
    return AllocineMediaSource(hass)


class AllocineMediaSource(MediaSource):
    """Allocine movie poster media source."""

    name: str = "Allocine Weekly Releases"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize media source."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media item to playable URL."""
        movie_id = item.identifier
        _LOGGER.debug("Resolving media for movie ID: %s", movie_id)

        # Get coordinator from runtime data
        config_entries = self.hass.config_entries.async_loaded_entries(DOMAIN)
        if not config_entries:
            raise Unresolvable("Integration not configured")

        coordinator = config_entries[0].runtime_data.coordinator

        # Find movie in coordinator data
        movie = next(
            (m for m in coordinator.data if m.id == movie_id),
            None,
        )

        if not movie:
            raise Unresolvable(f"Movie {movie_id} not found")

        # Return URL to our HTTP view
        url = f"/api/haallocine/poster/{movie_id}.jpg"
        _LOGGER.debug("Resolved media URL: %s", url)

        return PlayMedia(
            url=url,
            mime_type="image/jpeg",
        )

    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Browse available movies."""
        _LOGGER.debug("Browsing media, identifier: %s", item.identifier)

        # Get coordinator from runtime data
        config_entries = self.hass.config_entries.async_loaded_entries(DOMAIN)
        if not config_entries:
            raise Unresolvable("Integration not configured")

        coordinator = config_entries[0].runtime_data.coordinator

        if not coordinator.data:
            _LOGGER.warning("No movie data available")

        # Root level - show all movies (identifier is None or empty)
        if not item.identifier:
            _LOGGER.debug("Showing root level with %d movies", len(coordinator.data))
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier="",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.IMAGE,
                title="Allocine Weekly Releases",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=movie.id,
                        media_class=MediaClass.IMAGE,
                        media_content_type=MediaType.IMAGE,
                        title=movie.title,
                        can_play=True,
                        can_expand=False,
                        thumbnail=f"/api/haallocine/poster/{movie.id}.jpg",
                    )
                    for movie in coordinator.data
                ],
            )

        # Individual movie selected
        movie = next(
            (m for m in coordinator.data if m.id == item.identifier),
            None,
        )

        if not movie:
            raise Unresolvable(f"Movie {item.identifier} not found")

        _LOGGER.debug("Showing individual movie: %s", movie.title)
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=movie.id,
            media_class=MediaClass.IMAGE,
            media_content_type=MediaType.IMAGE,
            title=movie.title,
            can_play=True,
            can_expand=False,
            thumbnail=f"/api/haallocine/poster/{movie.id}.jpg",
        )
