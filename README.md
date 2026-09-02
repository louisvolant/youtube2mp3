# Youtube2Mp3

Python3 tool to download audio from a YouTube video and convert it to MP3.

**You should only retrieve copyright-free MP3 sounds.**

## Requirements

- Python 3
- [ffmpeg](https://ffmpeg.org/) (required for MP3 conversion)
- Python packages from `requirements.txt` (mainly `yt-dlp`)
- Google Chrome installed (cookies are read from the Chrome profile)

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

If you get HTTP 403 from YouTube:

```bash
pip install -U yt-dlp
# or
python3 -m pip install -U --pre "yt-dlp[default]"
```

## How it works (v1.2)

The script uses the **yt-dlp Python API** in a single pass:

1. One metadata extraction (`title`, `channel`, formats, …)
2. Local filename build (no extra network calls)
3. Download + MP3 conversion, **reusing** the same metadata

Chrome cookies are loaded once per run. This replaces the old design that
spawned 2–3 separate `yt-dlp` CLI processes.

## How to execute

From the folder that contains the script:

```bash
python3 youtube2mp3.py -u "https://www.youtube.com/watch?v=YOUTUBE_ID"
```

or with a bare video ID:

```bash
python3 youtube2mp3.py -v YOUTUBE_ID
```

### Common options

| Flag | Meaning |
|------|---------|
| `-u` / `--url` | Full YouTube URL |
| `-v` / `--video_id` | Video ID only |
| `-a` / `--artist` | Prepend a manual artist name to the filename |
| `-n` / `--add_account_name` | Prepend the YouTube channel name |
| `-q` / `--audio_quality` | MP3 bitrate (default: `128K`) |
| `-b` / `--background` | Start download in background and return immediately |

### Examples

Without artist:

```bash
python3 youtube2mp3.py -u "https://www.youtube.com/watch?v=..."
```

With artist:

```bash
python3 youtube2mp3.py -u "https://www.youtube.com/watch?v=..." -a "Artist Name"
```

With video ID, channel name in filename, and custom quality:

```bash
python3 youtube2mp3.py -v "VIDEO_ID" -n -q 192K
```

### Background mode

Returns the shell immediately; progress goes to a log file:

```bash
python3 youtube2mp3.py -v "VIDEO_ID" -n -b
```

Example output:

```text
Download started in background (pid 12345).
Log: /path/to/youtube2mp3_VIDEO_ID.log
Follow with: tail -f youtube2mp3_VIDEO_ID.log
```

```bash
tail -f youtube2mp3_VIDEO_ID.log
```

Equivalent shell approach without `-b`:

```bash
nohup python3 youtube2mp3.py -v "VIDEO_ID" -n > dl.log 2>&1 &
```

## Output filename

Pattern (parts omitted when empty):

```text
[channel - ][artist - ]title.mp3
```

Invalid filename characters are stripped/sanitized automatically.

## Notes

- Default audio quality is `128K` MP3 (re-encoded from the best available audio).
- Playlists are disabled (`noplaylist`).
- When finished, leave the venv with `deactivate`.
