from __future__ import annotations

import inspect
import json
import logging
from enum import Enum
from pathlib import Path

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
    is_flag=True,
    type=str,
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
    cookies_path = Path("/home/alec/Projects/spotify-downloader/cookies.txt"),
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
    try:
        global song_queue
        url_info = downloader.get_url_info(url[1])
        song_queue = downloader.get_download_queue(url_info)
    except Exception as e:
        logger.error(f'Failed to get {url[1]} Error: {e}')
        #continue
    logger.debug("Loading song queues...")
    try:
        for queue_index, queue_item in enumerate(song_queue, start=1):
            # First, check if the file already exists

            # Download the song if it doesn't exist
            queue_progress = f"Downloading track {queue_index}/{len(song_queue)}"
            track = queue_item.metadata
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

            # Path creator
            logger.debug("Creating path")
            final_path = downloader_song.get_final_path(tags)
            if final_path.exists():
                logger.warning(
                    f'({queue_progress}) Track already exists at "{final_path}", skipping'
                )
                #continue
            logger.debug("Getting file info")
            file_id = downloader_song.get_file_id(metadata_gid)
            if not file_id:
                logger.error(
                    f"({queue_progress}) Track not available on Spotify's "
                    "servers and no alternative found, skipping"
                )
                #continue
            
            logger.debug("Getting PSSH")
            pssh = spotify_api.get_pssh(file_id)
            logger.debug("Getting decryption key")
            decryption_key = downloader_song.get_decryption_key(pssh)
            logger.debug("Getting stream URL")
            stream_url = spotify_api.get_stream_url(file_id)
            encrypted_path = downloader.get_encrypted_path(track_id, ".m4a")
            decrypted_path = downloader.get_decrypted_path(track_id, ".m4a")
            logger.debug(f'Downloading to "{encrypted_path}"')
            downloader_song.download(encrypted_path, stream_url)
            remuxed_path = downloader.get_remuxed_path(track_id, ".m4a")
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
        logger.error(
            f'Failed to download song! Error: {e}'
        )
    finally: # Clean up
        if temp_path.exists():
            downloader.cleanup_temp_path()
    logger.info("Completed playlist download")
