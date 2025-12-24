# HA Allocine - Allocine Weekly Releases for Home Assistant

A Home Assistant custom integration that displays the **top 3 most popular movie posters** from Allocine.fr's weekly releases in your Home Assistant media browser.

## Features

- 🎬 **Automatic Weekly Updates**: Scrapes Allocine.fr every Wednesday (new release day)
- ⭐ **Top 3 Selection**: Automatically filters and displays only the 3 most anticipated movies based on "want to see" count
- 📸 **Media Browser Integration**: Browse and view movie posters directly in HA's media browser
- 🔄 **Manual Refresh**: Service available to manually refresh movie data
- 💾 **Local Caching**: Downloads and caches poster images for fast access
- 🎯 **Simple Naming**: Posters saved as 1.jpg, 2.jpg, 3.jpg (ranked by popularity)

## How It Works

1. **Scrapes** https://www.allocine.fr/film/sorties-semaine/ to get weekly movie releases
2. **Extracts** movie data from the page's JavaScript (jsEntities variable)
3. **Sorts** movies by popularity ("want to see" count)
4. **Filters** to keep only the top 3 most anticipated movies
5. **Downloads** poster images to `.cache/haallocine/` directory
6. **Serves** images via HTTP view at `/api/haallocine/poster/{movie_id}.jpg`
7. **Updates** automatically every Wednesday at 3:00 AM

## Installation

### HACS Installation (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JulienDeveaux&repository=HAAllocine&category=integration)

1. Click the badge above or manually add this repository to HACS:
   - Open HACS in your Home Assistant
   - Click on **Integrations**
   - Click the **3 dots** in the top right corner
   - Select **Custom repositories**
   - Add `https://github.com/JulienDeveaux/HAAllocine` as repository
   - Select **Integration** as category
   - Click **Add**
2. Search for "Allocine Weekly Releases" in HACS
3. Click **Download**
4. Restart Home Assistant
5. Go to **Settings** → **Devices & Services** → **Add Integration**
6. Search for "Allocine Weekly Releases" and add it

### Manual Installation

1. Copy the `custom_components/haallocine` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for "Allocine Weekly Releases" and add it

### Available Service

#### `haallocine.refresh`
Manually refresh movie data from Allocine.fr without waiting for the weekly update.

```yaml
service: haallocine.refresh
```

## Usage

### Media Browser

1. Open Home Assistant's **Media Browser**
2. Look for **"Allocine Weekly Releases"**
3. Browse the top 3 most popular movies of the week
4. Click on any movie to view its poster

### Caching

- **Location**: `{hass_config_dir}/.cache/haallocine/`
- **Filenames**: `1.jpg`, `2.jpg`, `3.jpg` (ranked by popularity)
- **Cleanup**: Cache is cleared before each update
- **Size**: ~3 images × 200KB = ~600KB per week

## Development

### Testing Locally

A standalone test script is provided to test the scraper without Home Assistant:

```bash
cd /Users/julien/IdeaProjects/HAAllocine
python3 test_scraper.py
```

This will:
1. Scrape Allocine.fr
2. Download the top 3 movie posters
3. Save them to a temporary directory
4. Display results with movie details

### Debug Script

To inspect the raw data structure from Allocine:

```bash
python3 debug_structure.py
```

## Credits

Built using the [MSP Integration 101 Template](https://github.com/msp1974/homeassistant-msp-integration-examples) as a starting point.

Inspired by:
- [Immich Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/immich) - Media source pattern
- [Tapo Control](https://github.com/JurajNyiri/HomeAssistant-Tapo-Control) - Media browser implementation

## License

This integration is provided as-is for personal use.

## Support

For issues, questions, or feature requests, please check the Home Assistant logs first, then file an issue.
