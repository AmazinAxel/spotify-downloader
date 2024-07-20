from enum import Enum


class RemuxMode(Enum):
    FFMPEG = "ffmpeg"
    MP4BOX = "mp4box"


class DownloadModeSong(Enum):
    YTDLP = "ytdlp"
    ARIA2C = "aria2c"