#!/usr/local/bin/python3
__author__ = 'Louis Volant'
__version__ = 1.1  # Updated version

TARGET_BITRATE = "128K"
BASE_OUTPUT_FILENAME = "output.mp3"

import subprocess
import argparse
import logging
import re


# README
# execute with
# python3 -m venv myenv
# source myenv/bin/activate
# pip install -r requirements.txt
# python3 youtube2mp3.py -u 'YOUR_YOUTUBE_VIDEO_URL' -n
# Or with video ID:
# python3 youtube2mp3.py --video_id 'YOUR_YOUTUBE_VIDEO_ID' -n
# Once finished, simply desactivate the virtual environment using "deactivate"


def sanitize_filename(input_str):  # Renamed input to input_str to avoid conflict with built-in
    # Remove invalid characters from filename
    if input_str is None:
        return ""
    return re.sub(r'[<>:"/\\|?*]', '', input_str)


def get_youtube_title(url):
    # Define the command to get the title of the YouTube video
    command = ['yt-dlp', '--get-title', url]
    # Run the command and capture the output
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_youtube_channel_name(url):
    # Define the command to get the channel name of the YouTube video
    # %(channel)s is a yt-dlp output template for the channel name
    # %(uploader)s can also be used, it might be more general
    command = ['yt-dlp', '--print', '%(channel)s', url]
    # Run the command and capture the output
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def download_youtube_audio(url, output_path=BASE_OUTPUT_FILENAME, audio_quality=TARGET_BITRATE):
    # Define the command to download and convert the audio
    command = [
        'yt-dlp',
        '-x', '--audio-format', 'mp3',
        '--audio-quality', audio_quality,
        '--output', output_path,
        url
    ]

    # Run the command
    subprocess.run(command, check=True)

    print(f'Audio has been downloaded and converted to {output_path}')


def main():
    parser = argparse.ArgumentParser(description='Download YouTube video audio and convert to MP3.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--url', type=str, help='The URL of the YouTube video')
    group.add_argument('-v', '--video_id', type=str, help='The ID of the YouTube video')
    parser.add_argument('-q', '--audio_quality', default='128K', help='The audio quality in kbps (default: 128K)')
    parser.add_argument('-a', '--artist', type=str, help='Artist name to prepend to the filename (manual override)')
    parser.add_argument('-n', '--add_account_name', action='store_true',
                        help='Prepend the YouTube account/channel name to the filename')  # New argument

    args = parser.parse_args()

    video_id_or_url = ''
    if args.url:
        video_id_or_url = args.url
    elif args.video_id:
        # Ensure video_id is correctly used to form a URL if yt-dlp needs a full URL
        # yt-dlp usually handles video IDs directly, but being explicit is fine.
        # The original script had "https://www.youtube.com/watch?v={args.video_id}"
        # Using a more standard YouTube URL structure might be safer if yt-dlp has issues with the googleusercontent one.
        # However, yt-dlp is generally very robust with various URL formats including just the ID.
        # For simplicity, we can let yt-dlp handle the ID directly.
        # If you need a full URL, you could use: f"https://www.youtube.com/watch?v={args.video_id}"
        video_id_or_url = args.video_id

    # Get the video title and sanitize it for use as a filename
    video_title = get_youtube_title(video_id_or_url)
    sanitized_title = sanitize_filename(video_title)

    filename_parts = []

    # Add account name to the filename if -n flag is provided
    if args.add_account_name:
        account_name = get_youtube_channel_name(video_id_or_url)
        sanitized_account_name = sanitize_filename(account_name)
        if sanitized_account_name:  # Check if account name was successfully retrieved
            filename_parts.append(sanitized_account_name)

    # Add artist name to the filename if provided (this will come after account name if both are present)
    if args.artist:
        sanitized_artist = sanitize_filename(args.artist)
        filename_parts.append(sanitized_artist)

    filename_parts.append(sanitized_title)

    output_filename_stem = " - ".join(filter(None, filename_parts))  # filter(None,...) removes empty strings
    output_path = f"{output_filename_stem}.mp3"

    if not sanitized_title:  # Handle case where title might be empty
        logging.error(f"Could not retrieve a valid title for {video_id_or_url}. Using a default filename.")
        output_path = f"output_{sanitize_filename(video_id_or_url)}.mp3"

    logging.info(f'Processing: {video_id_or_url} and storing to {output_path}')

    download_youtube_audio(video_id_or_url, output_path, args.audio_quality)


if __name__ == '__main__':
    ## Initialize logging before hitting main, in case we need extra debuggability
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    main()