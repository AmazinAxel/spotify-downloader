# Spotify Downloader
Python CLI for downloading music playlists from Spotify. Pre-configured for easy usage to efficently update and sync playlists for local media players.

This is a complete recode from [glomatico/spotify-web-downloader](https://github.com/glomatico/spotify-web-downloader) with only strictly-necessary features. Intended for personal use to sync playlists. (Requires FFmpeg)

## ⚠️ Terms of Service Warning

This tool breaks Spotify's Terms of Service agreement. Because this requires the cookies of your account, all downloaded songs can be traced to your account. Be extremely careful while using this tool or use an alternate account. 

## Intended Purpose

You can use a daily cronjob to run a backup script to sync all your playlists, making it easy to keep frequently-updated playlists synced on offline devices (such as MP3 players) for personal usage. 

## Usage (for NixOS)

TODO: write a nix flake

Clone the project and cd into the project directory root. Run these commands to make a virtual environment for development:
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
Use an extension [such as this](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif) to download cookies. Place your cookies file in the project directory and name it `cookies.txt`.
Use `spotify-downloader -f 'folderName' (URL goes here)` to download the playlist directly to a folder in ~/Music.
