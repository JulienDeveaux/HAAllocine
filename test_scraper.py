#!/usr/bin/env python3
"""Standalone test script for Allocine scraper."""

import logging
import sys
from pathlib import Path
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Direct import to avoid __init__.py
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "haallocine"))

from allocine_api import (
    AllocineAPI,
    AllocineConnectionError,
    AllocineParseError,
)

def main():
    """Test the Allocine scraper."""
    print("=" * 60)
    print("Testing Allocine Scraper")
    print("=" * 60)

    # Create temporary cache directory
    cache_dir = Path(tempfile.mkdtemp(prefix="allocine_test_"))
    print(f"\nUsing cache directory: {cache_dir}")

    try:
        # Initialize API
        print("\n1. Initializing API...")
        api = AllocineAPI(cache_dir)

        # Test scraping
        print("\n2. Scraping Allocine.fr...")
        print(f"   URL: {api.WEEKLY_URL}")
        movies = api.scrape_weekly_releases()

        # Display results
        print("\n3. Results:")
        print(f"   Found {len(movies)} movies")
        print("\n" + "=" * 60)

        for i, movie in enumerate(movies, 1):
            print(f"\nMovie {i}:")
            print(f"  ID:           {movie.id}")
            print(f"  Title:        {movie.title}")
            print(f"  Release Date: {movie.release_date}")
            print(f"  Poster URL:   {movie.poster_url}")
            print(f"  Cached Path:  {movie.local_poster_path}")

            # Verify file exists
            if movie.local_poster_path:
                path = Path(movie.local_poster_path)
                if path.exists():
                    size_kb = path.stat().st_size / 1024
                    print(f"  File Size:    {size_kb:.1f} KB ✓")
                else:
                    print(f"  File Status:  Missing ✗")

        # Summary
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  Total movies:        {len(movies)}")
        print(f"  With posters:        {sum(1 for m in movies if m.local_poster_path)}")
        print(f"  Cache directory:     {cache_dir}")

        # List cached files
        cached_files = list(cache_dir.glob("*.jpg"))
        print(f"  Cached files:        {len(cached_files)}")

        if cached_files:
            total_size = sum(f.stat().st_size for f in cached_files) / (1024 * 1024)
            print(f"  Total cache size:    {total_size:.2f} MB")

        print("\n✓ Test completed successfully!")
        print(f"\nCache files stored at: {cache_dir}")
        print("You can inspect the downloaded images there.")

        return 0

    except AllocineConnectionError as e:
        print(f"\n✗ Connection Error: {e}")
        print("\nPossible causes:")
        print("  - No internet connection")
        print("  - Allocine.fr is down")
        print("  - Request timeout")
        return 1

    except AllocineParseError as e:
        print(f"\n✗ Parse Error: {e}")
        print("\nPossible causes:")
        print("  - Allocine changed their page structure")
        print("  - jsEntities format changed")
        print("  - GraphQL structure is different than expected")
        print("\nCheck the debug logs above for details.")
        return 1

    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
