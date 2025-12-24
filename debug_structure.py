#!/usr/bin/env python3
"""Debug script to inspect the actual jsEntities structure."""

import json
import re
import requests

URL = "https://www.allocine.fr/film/sorties-semaine/"

print("Fetching Allocine page...")
response = requests.get(URL, timeout=30)
print(f"Status: {response.status_code}\n")

# Extract jsEntities
patterns = [
    r"jsEntities\s*=\s*({.*?});",
    r"const\s+jsEntities\s*=\s*({.*?});",
    r"var\s+jsEntities\s*=\s*({.*?});",
]

entities = None
for pattern in patterns:
    match = re.search(pattern, response.text, re.DOTALL)
    if match:
        entities = json.loads(match.group(1))
        print(f"✓ Found jsEntities with pattern: {pattern}\n")
        break

if not entities:
    print("✗ jsEntities not found!")
    exit(1)

# Show structure
print("=" * 80)
print("jsEntities Structure:")
print("=" * 80)
print(json.dumps(entities, indent=2, ensure_ascii=False)[:5000])  # First 5000 chars
print("\n... (truncated)")

# Analyze top-level keys
print("\n" + "=" * 80)
print("Top-level keys:")
print("=" * 80)
for key in entities.keys():
    value = entities[key]
    print(f"  {key}: {type(value).__name__}")
    if isinstance(value, (list, dict)):
        print(f"    Length/Size: {len(value)}")
        if isinstance(value, list) and value:
            print(f"    First item type: {type(value[0]).__name__}")
        if isinstance(value, dict) and value:
            first_key = list(value.keys())[0]
            print(f"    First key: {first_key}")

# Try to find movie-like data
print("\n" + "=" * 80)
print("Looking for movie data patterns...")
print("=" * 80)

def find_movie_patterns(obj, path=""):
    """Recursively search for movie-like data."""
    if isinstance(obj, dict):
        # Check if this looks like a movie
        has_title = any(k in obj for k in ['title', 'titleText', 'name'])
        has_id = any(k in obj for k in ['id', 'internalId', 'movieId'])
        has_poster = any(k in obj for k in ['poster', 'image', 'thumbnail'])

        if has_title and (has_id or has_poster):
            print(f"\n✓ Found movie-like object at: {path}")
            print(f"  Keys: {list(obj.keys())[:10]}")  # First 10 keys
            if 'title' in obj:
                print(f"  Title: {obj.get('title', 'N/A')}")
            if 'titleText' in obj:
                print(f"  TitleText: {obj.get('titleText')}")
            return True

        # Recurse into dict
        for key, value in list(obj.items())[:20]:  # Limit depth
            find_movie_patterns(value, f"{path}/{key}")

    elif isinstance(obj, list):
        for i, item in enumerate(obj[:5]):  # Check first 5 items
            find_movie_patterns(item, f"{path}[{i}]")

find_movie_patterns(entities)

print("\n" + "=" * 80)
print("Debug complete!")
print("=" * 80)
