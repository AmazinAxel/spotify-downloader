from __future__ import annotations

import inspect
import json
import logging
import os
from enum import Enum
from pathlib import Path
import subprocess
import shutil

import click

MP4_TAGS_MAP = {
    "album": "\xa9alb",
    "album_artist": "aART",
    "artist": "\xa9ART",
    "composer": "\xa9wrt",
    "copyright": "cprt",
    "media_type": "stik",
    "producer": "\xa9prd",
    "release_date": "\xa9day",
    "title": "\xa9nam",
    "url": "\xa9url",
}

from .downloader import Downloader
from .downloader_song import DownloaderSong
from .enums import DownloadModeSong, RemuxMode
from .spotify_api import SpotifyApi

spotify_api_sig = inspect.signature(SpotifyApi.__init__)
downloader_sig = inspect.signature(Downloader.__init__)
downloader_song_sig = inspect.signature(DownloaderSong.__init__)

def get_param_string(param: click.Parameter) -> str:
    if isinstance(param.default, Enum):
        return param.default.value
    elif isinstance(param.default, Path):
        return str(param.default)
    else:
        return param.default

@click.command()
@click.help_option("-h", "--help")

# CLI options
@click.argument(
    "url",
    nargs=-1,
    type=str,
    required=True,
)
@click.option(
    "--foldername",
    "-f",
    type=str,  # Remove is_flag=True to allow passing a folder name
    required=True,
    help="The name of the output folder (within ~/Music)",
)
@click.option(
    "--premium",
    "-p",
    is_flag=True,
    type=bool,
    help="Whether to download music in premium quality (requires a Spotify Premium account)",
)


def main(
    url: str,
    foldername: str,
    premium: bool,
    cookies_path = Path("./cookies.txt"),
    temp_path: Path = Path("./temp"),
) -> None:
    logging.basicConfig(
        format="[%(levelname)-8s %(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(2)
    if not cookies_path.exists():
        logger.critical("Cookies file not found: ", cookies_path)
        return
    spotify_api = SpotifyApi(cookies_path)
    downloader = Downloader(
        spotify_api,
        foldername
    )
    downloader_song = DownloaderSong(
        downloader,
        premium
    )
    logger.debug("Setting up CDM")
    downloader.set_cdm()
    logger.debug("Queuing songs...")
    try:
        global song_queue
        url_info = downloader.get_url_info(url[0])
        song_queue = downloader.get_download_queue(url_info)
    except Exception as e:
        logger.error(f'Failed to get {url[0]} Error: {e}')
        exit()
    try:
        # Create the folder if it doesn't exist
        folder_path = Path(f"/home/alec/Music/{foldername}/")
        os.makedirs(folder_path, exist_ok=True)
        
        for queue_index, queue_item in enumerate(song_queue, start=1):
            track = queue_item.metadata

            # First, check if the file already exists
            final_path = folder_path.joinpath(f"{track['album']['artists'][0]['name']} - {track['name']}.m4a")

            if final_path.exists():
                logger.info(f"(Skipping {queue_index}/{len(song_queue)}) {track['album']['artists'][0]['name']} - {track['name']} already exists")
                continue

            # Download the song if it doesn't exist
            queue_progress = f"Downloading track {queue_index}/{len(song_queue)}"
            logger.info(f'({queue_progress}) Downloading "{track["name"]}"')
            track_id = track["id"]
            logger.debug("Getting GID metadata")
            gid = spotify_api.track_id_to_gid(track_id)
            metadata_gid = spotify_api.get_gid_metadata(gid)

            # Get metadata
            logger.debug("Getting album metadata")
            album_metadata = spotify_api.get_album(
                spotify_api.gid_to_track_id(metadata_gid["album"]["gid"])
            )

            # Get creds
            logger.debug("Getting track credits")
            track_credits = spotify_api.get_track_credits(track_id)
            tags = downloader_song.get_tags(
                metadata_gid,
                album_metadata,
                track_credits,
            )

            logger.debug("Getting file info")
            file_id = downloader_song.get_file_id(metadata_gid)
            if not file_id:
                logger.error(
                    f"({queue_progress}) Track not available on Spotify's "
                    "servers and no alternative found, skipping"
                )
                continue
            
            logger.debug("Getting PSSH")
            pssh = spotify_api.get_pssh(file_id)
            logger.debug("Getting decryption key")
            decryption_key = downloader_song.get_decryption_key(pssh)
            logger.debug("Getting stream URL")
            stream_url = spotify_api.get_stream_url(file_id)
            encrypted_path = temp_path.joinpath(f"{track_id}_encrypted.m4a")
            decrypted_path = temp_path.joinpath(f"{track_id}_decrypted.m4a")
            logger.debug(f'Downloading to "{encrypted_path}"')
            downloader_song.download(encrypted_path, stream_url)
            remuxed_path = temp_path.joinpath(f"{track_id}_remuxed.m4a")
            logger.debug(f'Decrypting/Remuxing to "{remuxed_path}"')
            downloader_song.remux(
                encrypted_path,
                decrypted_path,
                remuxed_path,
                decryption_key,
            )

            logger.debug("Applying tags")
            downloader.apply_tags(remuxed_path, tags)
            logger.debug(f'Moving to "{final_path}"')
            downloader.move_to_final_path(remuxed_path, final_path)
    except Exception as e:
        logger.error(f'Failed to download song! Error: {e}')
    finally: # Clean up
        if temp_path.exists():
            shutil.rmtree(temp_path)
    logger.info("Completed playlist download")

    # Update mpc/mpd database (OPTIONAL)
    subprocess.run('mpc update', shell = True)
    logger.info("Updated mpc database")