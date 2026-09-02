#!/usr/local/bin/python3
__author__ = 'Louis Volant'
__version__ = 1.2

TARGET_BITRATE = "128K"
BASE_OUTPUT_FILENAME = "output.mp3"

import argparse
import logging
import os
import re
import sys
import subprocess
from pathlib import Path

try:
    import yt_dlp
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "yt-dlp is required. Install with: pip install -U yt-dlp"
    ) from exc


# README
# execute with
# python3 -m venv myenv
# source myenv/bin/activate
# pip install -r requirements.txt
# NOTE : if getting HTTP 403 Forbidden from Youtube, execute : pip install -U yt-dlp
# OR if still not working : python3 -m pip install -U --pre "yt-dlp[default]"
# python3 youtube2mp3.py -u 'YOUR_YOUTUBE_VIDEO_URL' -n
# Or with video ID:
# python3 youtube2mp3.py --video_id 'YOUR_YOUTUBE_VIDEO_ID' -n
# Background (returns immediately):
# python3 youtube2mp3.py -v 'VIDEO_ID' -n -b
# Once finished, simply deactivate the virtual environment using "deactivate"


def sanitize_filename(input_str):
    """Remove invalid characters from a filename stem."""
    if input_str is None:
        return ""
    result = input_str.replace("|", "-")
    result = re.sub(r'[<>:"/\\|?*]', "", result)
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"\s*-\s*-+\s*", " - ", result)
    return result.strip()


def normalize_audio_quality(audio_quality):
    """Convert CLI values like 128K to yt-dlp preferredquality (128)."""
    if audio_quality is None:
        return "128"
    value = str(audio_quality).strip().upper().rstrip("K")
    return value or "128"


def build_output_path(info, add_account_name=False, artist=None, video_ref=None):
    """Build the final .mp3 path from extracted metadata (no extra network calls)."""
    title = sanitize_filename(info.get("title") or "")
    filename_parts = []

    if add_account_name:
        channel = sanitize_filename(
            info.get("channel") or info.get("uploader") or info.get("creator") or ""
        )
        if channel:
            filename_parts.append(channel)

    if artist:
        sanitized_artist = sanitize_filename(artist)
        if sanitized_artist:
            filename_parts.append(sanitized_artist)

    if title:
        filename_parts.append(title)
        stem = " - ".join(filename_parts)
        return f"{stem}.mp3"

    logging.error(
        "Could not retrieve a valid title for %s. Using a default filename.",
        video_ref or "video",
    )
    fallback = sanitize_filename(video_ref) or "output"
    return f"output_{fallback}.mp3"


def download_youtube_audio(
    url,
    audio_quality=TARGET_BITRATE,
    add_account_name=False,
    artist=None,
):
    """
    Single-pass download:
    1) extract_info(download=False) — one YouTube metadata fetch
    2) process_ie_result(info, download=True) — reuses the same info dict
       (no second webpage/player/API round-trip for metadata)
    Cookies are loaded once for this YoutubeDL instance.
    """
    quality = normalize_audio_quality(audio_quality)

    # Progress stays visible for the download phase.
    base_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "cookiesfrombrowser": ("chrome",),
        "noprogress": False,
        "quiet": False,
        "no_warnings": False,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        # Keep original audio container only until MP3 extraction finishes.
        "keepvideo": False,
    }

    with yt_dlp.YoutubeDL(base_opts) as ydl:
        # --- pass 1: metadata only (single network extraction) ---
        info = ydl.extract_info(url, download=False)
        if not info:
            raise RuntimeError(f"No metadata returned for {url}")

        # Playlists should not happen with noplaylist, but be defensive.
        if info.get("_type") == "playlist" and info.get("entries"):
            info = next((e for e in info["entries"] if e), None)
            if not info:
                raise RuntimeError(f"Empty playlist result for {url}")

        output_path = build_output_path(
            info,
            add_account_name=add_account_name,
            artist=artist,
            video_ref=url,
        )
        # Stem only; %(ext)s is filled by yt-dlp then replaced by ExtractAudio (mp3)
        stem = str(Path(output_path).with_suffix(""))
        ydl.params["outtmpl"] = {"default": f"{stem}.%(ext)s"}

        logging.info("Processing: %s and storing to %s", url, output_path)

        # --- pass 2: download using already-extracted info (no re-fetch) ---
        ydl.process_ie_result(info, download=True)

    print(f"Audio has been downloaded and converted to {output_path}")
    return output_path


def _background_log_path(video_id_or_url):
    safe = sanitize_filename(video_id_or_url) or "download"
    safe = re.sub(r"\s+", "_", safe)[:80]
    return f"youtube2mp3_{safe}.log"


def run_in_background(argv_without_background):
    """
    Re-launch this script without -b/--background, detached from the terminal.
    Returns immediately so the shell is free for other commands.
    """
    script = str(Path(__file__).resolve())
    cmd = [sys.executable, script, *argv_without_background]

    # Derive a stable-ish log name from -v/-u if present.
    video_ref = "download"
    if "-v" in argv_without_background:
        i = argv_without_background.index("-v")
        if i + 1 < len(argv_without_background):
            video_ref = argv_without_background[i + 1]
    elif "--video_id" in argv_without_background:
        i = argv_without_background.index("--video_id")
        if i + 1 < len(argv_without_background):
            video_ref = argv_without_background[i + 1]
    elif "-u" in argv_without_background:
        i = argv_without_background.index("-u")
        if i + 1 < len(argv_without_background):
            video_ref = argv_without_background[i + 1]
    elif "--url" in argv_without_background:
        i = argv_without_background.index("--url")
        if i + 1 < len(argv_without_background):
            video_ref = argv_without_background[i + 1]

    log_path = _background_log_path(video_ref)
    log_file = open(log_path, "w", encoding="utf-8")  # noqa: SIM115 — kept open for child

    # start_new_session=True detaches from the controlling terminal (POSIX).
    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    log_file.close()

    print(f"Download started in background (pid {proc.pid}).")
    print(f"Log: {os.path.abspath(log_path)}")
    print(f"Follow with: tail -f {log_path}")
    return proc.pid


def _strip_background_flags(argv):
    """Return argv without -b/--background for the detached child process."""
    out = []
    for arg in argv:
        if arg in ("-b", "--background"):
            continue
        out.append(arg)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    parser = argparse.ArgumentParser(
        description="Download YouTube video audio and convert to MP3 (single-pass)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", type=str, help="The URL of the YouTube video")
    group.add_argument("-v", "--video_id", type=str, help="The ID of the YouTube video")
    parser.add_argument(
        "-q",
        "--audio_quality",
        default="128K",
        help="The audio quality in kbps (default: 128K)",
    )
    parser.add_argument(
        "-a",
        "--artist",
        type=str,
        help="Artist name to prepend to the filename (manual override)",
    )
    parser.add_argument(
        "-n",
        "--add_account_name",
        action="store_true",
        help="Prepend the YouTube account/channel name to the filename",
    )
    parser.add_argument(
        "-b",
        "--background",
        action="store_true",
        help="Start download in background and return immediately",
    )

    args = parser.parse_args(argv)

    if args.background:
        child_argv = _strip_background_flags(argv)
        run_in_background(child_argv)
        return

    video_id_or_url = args.url if args.url else args.video_id

    download_youtube_audio(
        video_id_or_url,
        audio_quality=args.audio_quality,
        add_account_name=args.add_account_name,
        artist=args.artist,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(funcName)s - %(levelname)s - %(message)s",
    )
    main()
