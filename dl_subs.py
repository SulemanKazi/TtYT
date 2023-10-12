"""Utilities to download english subtitles from YouTube videos."""
import logging

import youtube_dl
import vtt_to_srt.vtt_to_srt as vtt


class YTLogger:
    """Used to hold youtube-dl's output for parsing."""

    def __init__(self) -> None:
        self.debug_msg = []
        self.warning_msg = []
        self.error_msg = []

    def debug(self, msg):
        self.debug_msg.append(msg)

    def warning(self, msg):
        self.warning_msg.append(msg)

    def error(self, msg):
        self.error_msg.append(msg)


def get_subtitles_for_video(video_url):
    """Downloads subtitles for a given YouTube video in the SRT format.

    Args:
        video_url: URL of the YouTube video.
    Returns:
        The name of the SRT file containing the subtitles, None if an error
        occurs.
    """
    sub_lang, auto_subs = _find_best_subs(video_url)
    if sub_lang:
        output_file = _download_subs(video_url, sub_lang, auto_subs)
        if output_file:
            return _convert_to_srt(output_file)

    return None


def _find_best_subs(video_url):
    """Given a video URL, returns the best subtitles available."""
    logger = YTLogger()

    # Get information about what subtitles are available for the video.
    # These can be auto-generated (called 'automatic captions'), upload by the
    # video creator (called 'subtitles'), or non-existent.
    ydl_opts = {
        "skip_download": True,
        "listsubtitles": True,
        "logger": logger,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # Parse YTDL output to determine if any english subtitles or captions
    # are available.
    caption_type = None
    last_seen = None
    caption_lang_code = None

    # Sift through YTDL output and find the best subtitles. Subtitles are given
    # preference over automatic captions.
    for message in logger.debug_msg:
        for output_line in message.splitlines():
            if "Available automatic captions" in output_line:
                last_seen = "AUTO"
            elif "Available subtitles" in output_line:
                last_seen = "SUBTITLES"
            elif output_line.startswith("en"):
                caption_lang_code = output_line.split(" ", 2)[0]
                caption_type = last_seen

    if caption_type and caption_lang_code:
        download_auto_subs = caption_type == "AUTO"
        return caption_lang_code, download_auto_subs

    logging.error("Error finding subtitles for %s", video_url)
    error = " ".join(logger.error_msg)
    logging.error(error)

    return None, None


def _download_subs(video_url, lang_code, auto_subs):
    """Download subtitles for a video. """
    logger = YTLogger()

    ydl_opts = {
        "skip_download": True,
        "subtitleslangs": [lang_code],
        "logger": logger,
        "outtmpl": "%(title)s"
    }

    if auto_subs:
        ydl_opts["writeautomaticsub"] = True
    else:
        ydl_opts["writesubtitles"] = True

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    for message in logger.debug_msg:
        for output_line in message.splitlines():
            if "Writing video subtitles to: " in output_line:
                output_file = output_line.split("Writing video subtitles to: ",
                                                1)[1]
                return output_file

    logging.error("Error downloading subtitles for %s", video_url)
    error = " ".join(logger.error_msg)
    logging.error(error)

    return None


def _convert_to_srt(file_name):
    """Convert VTT subtitles to SRT format."""
    convert_file = vtt.ConvertFile(file_name, "utf-8")
    convert_file.convert()

    # Return the file name of the srt file.
    if file_name.endswith(".vtt"):
        return file_name[:-4] + ".srt"

    logging.error("Error converting subtitles for %s", file_name)
    return None
