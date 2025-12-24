"""Allocine.fr scraper for movie data."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


@dataclass
class AllocineMovie:
    """Represents a movie from Allocine."""

    id: str
    title: str
    poster_url: str
    release_date: str
    want_to_see_count: int = 0
    local_poster_path: str | None = None


class AllocineAPI:
    """API for scraping Allocine.fr."""

    WEEKLY_URL = "https://www.allocine.fr/film/sorties-semaine/"

    def __init__(self, cache_dir: Path) -> None:
        """Initialize API with cache directory."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        _LOGGER.debug("AllocineAPI initialized with cache dir: %s", self.cache_dir)

    def scrape_weekly_releases(self) -> list[AllocineMovie]:
        """Scrape current week's movie releases (blocking operation)."""
        _LOGGER.info("Starting scrape of Allocine weekly releases")
        try:
            response = requests.get(self.WEEKLY_URL, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract jsEntities variable from script tags
            js_entities = self._extract_js_entities(response.text)

            # Parse GraphQL data structure
            movies = self._parse_movies(js_entities)

            _LOGGER.info("Found %d movies to process", len(movies))

            # Sort by want_to_see_count (descending) and keep only top 3
            movies.sort(key=lambda m: m.want_to_see_count, reverse=True)
            top_movies = movies[:3]

            _LOGGER.info("Keeping top 3 most popular movies (out of %d total)", len(movies))
            for i, movie in enumerate(top_movies, 1):
                _LOGGER.info("  #%d: %s (%d want to see)", i, movie.title, movie.want_to_see_count)

            # Download poster images for top 3
            self._download_posters(top_movies)

            return top_movies

        except requests.RequestException as err:
            _LOGGER.error("Failed to scrape Allocine: %s", err)
            raise AllocineConnectionError(f"Connection error: {err}") from err
        except AllocineParseError as err:
            _LOGGER.error("Failed to parse Allocine data: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error during scraping: %s", err)
            raise AllocineParseError(f"Unexpected error: {err}") from err

    def _extract_js_entities(self, html_content: str) -> dict[str, Any]:
        """Extract jsEntities variable from page scripts."""
        _LOGGER.debug("Extracting jsEntities from page")

        # Look for jsEntities in multiple possible formats
        patterns = [
            r"jsEntities\s*=\s*({.*?});",
            r"const\s+jsEntities\s*=\s*({.*?});",
            r"var\s+jsEntities\s*=\s*({.*?});",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                try:
                    entities = json.loads(match.group(1))
                    _LOGGER.debug("Successfully extracted jsEntities")
                    return entities
                except json.JSONDecodeError as err:
                    _LOGGER.warning(
                        "Found jsEntities but failed to parse JSON: %s", err
                    )
                    continue

        raise AllocineParseError("jsEntities not found in page or invalid JSON")

    def _parse_movies(self, js_entities: dict[str, Any]) -> list[AllocineMovie]:
        """Parse movie data from jsEntities structure."""
        _LOGGER.debug("Parsing movies from jsEntities")
        movies = []

        try:
            # jsEntities is a dict where keys are base64-encoded IDs
            # and values are movie objects
            for movie_id, movie_data in js_entities.items():
                if not isinstance(movie_data, dict):
                    _LOGGER.debug("Skipping non-dict entry: %s", movie_id)
                    continue

                try:
                    movie = self._parse_single_movie(movie_data)
                    if movie:
                        movies.append(movie)
                except Exception as err:
                    _LOGGER.warning("Failed to parse movie '%s': %s", movie_id, err)
                    continue

        except Exception as err:
            _LOGGER.error("Error parsing movie list: %s", err)
            raise AllocineParseError(f"Failed to parse movie list: {err}") from err

        if not movies:
            _LOGGER.warning("No movies found in jsEntities")

        return movies

    def _parse_single_movie(self, movie_data: dict[str, Any]) -> AllocineMovie | None:
        """Parse a single movie entry."""
        # Extract ID (it's directly in the movie_data)
        movie_id = str(movie_data.get("id", ""))

        # Extract title
        title = movie_data.get("title", "Unknown")

        # Extract poster URL
        poster_url = self._extract_poster_url(movie_data)

        # Extract release date
        release_date = movie_data.get("releaseDate", "")

        # Extract want to see count
        want_to_see_count = movie_data.get("social", {}).get("user_note_i_want_to_see_count", 0)

        if not movie_id or not poster_url:
            _LOGGER.debug(
                "Skipping movie '%s': missing ID or poster URL", title
            )
            return None

        _LOGGER.debug("Parsed movie: %s (ID: %s, Want to see: %d)", title, movie_id, want_to_see_count)

        return AllocineMovie(
            id=movie_id,
            title=title,
            poster_url=poster_url,
            release_date=release_date,
            want_to_see_count=want_to_see_count,
        )

    def _extract_poster_url(self, movie_data: dict[str, Any]) -> str:
        """Extract poster URL from movie data."""
        # The poster is a dict with a 'url' field
        poster = movie_data.get("poster", {})
        if isinstance(poster, dict):
            url = poster.get("url", "")
            if url:
                return url

        return ""

    def _download_posters(self, movies: list[AllocineMovie]) -> None:
        """Download poster images to cache (blocking operation)."""
        _LOGGER.info("Downloading %d posters to cache", len(movies))

        for rank, movie in enumerate(movies, 1):
            if not movie.poster_url:
                _LOGGER.debug("Skipping download for %s: no poster URL", movie.title)
                continue

            try:
                # Use simple rank-based filename: 1.jpg, 2.jpg, 3.jpg
                poster_path = self.cache_dir / f"{rank}.jpg"

                _LOGGER.debug("Downloading poster #%d for %s from %s", rank, movie.title, movie.poster_url)

                response = requests.get(movie.poster_url, timeout=30)
                response.raise_for_status()

                poster_path.write_bytes(response.content)
                movie.local_poster_path = str(poster_path)

                _LOGGER.info(
                    "Downloaded poster #%d: %s (%d KB)",
                    rank,
                    movie.title,
                    len(response.content) // 1024,
                )

            except Exception as err:
                _LOGGER.warning(
                    "Failed to download poster for %s: %s", movie.title, err
                )
                # Don't fail entire update for one poster

    def clear_cache(self) -> None:
        """Clear all cached poster images."""
        _LOGGER.info("Clearing poster cache at %s", self.cache_dir)
        count = 0
        for poster in self.cache_dir.glob("*.jpg"):
            try:
                poster.unlink()
                count += 1
            except Exception as err:
                _LOGGER.warning("Failed to delete %s: %s", poster, err)

        _LOGGER.info("Cleared %d cached posters", count)


class AllocineConnectionError(Exception):
    """Exception for connection errors."""


class AllocineParseError(Exception):
    """Exception for parsing errors."""
