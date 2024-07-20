# Spotify Downloader
Python CLI for downloading music playlists from Spotify. Pre-configured for easy usage to efficently update and sync playlists for local media players.

This is a complete recode from [glomatico/spotify-web-downloader](https://github.com/glomatico/spotify-web-downloader) with only strictly-necessary features. Intended for personal use to sync playlists. (Requires FFmpeg)


## Usage (for NixOS)
Clone the project and cd into the project directory root. Run these commands:
```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install deps and the application
pip install -r requirements.txt 
pip install .

# Example usage, downloading the entire playlist to the ~/Music/Focus/ dir
spotify-downloader -f "Focus" https://open.spotify.com/playlist/3Qk9br14pjEo2aRItDhb2f 
```
Use an extension [such as this](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif) Place your cookies file in the project directory and name it `cookies.txt`.
Use `spotify-downloader (URL goes here)` to download the playlist directly to a folder in ~/Music.
