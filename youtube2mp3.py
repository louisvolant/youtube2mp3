#!/usr/local/bin/python3
__author__ = 'Louis Volant'
__version__= 1.0

TARGET_BITRATE = "128K"
BASE_OUTPUT_FILENAME = "output.mp3"

import subprocess
import argparse
import logging, re

# README
# execute with
# python3 -m venv myenv
# source myenv/bin/activate
# pip install -r requirements.txt
# python3 youtube2mp3.py 'https://www.youtube.com/watch?v=YOUTUBE_ID' 
# Once finished, simply desactivate the virtual environment using "deactivate"


def sanitize_filename(input):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '', input)

def get_youtube_title(url):
    # Define the command to get the title of the YouTube video
    command = ['yt-dlp', '--get-title', url]
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
    parser.add_argument('-a', '--artist', type=str, help='Artist name to prepend to the filename')

    args = parser.parse_args()

    video_id_or_url = ''
    if args.url:
        video_id_or_url = args.url
    elif args.video_id:
        video_id_or_url = f"https://www.youtube.com/watch?v={args.video_id}"

    args = parser.parse_args()

    # Get the video title and sanitize it for use as a filename
    video_title = get_youtube_title(video_id_or_url)
    sanitized_title = sanitize_filename(video_title)

    # Add artist name to the filename if provided
    if args.artist:
        sanitized_artist = sanitize_filename(args.artist)
        output_path = f"{sanitized_artist} - {sanitized_title}.mp3"
    else:
        output_path = f"{sanitized_title}.mp3"

    logging.info('Processing: {0} and storing to {1}'.format(video_id_or_url, output_path))

    download_youtube_audio(video_id_or_url, output_path, args.audio_quality)


if __name__ == '__main__':
    ## Initialize logging before hitting main, in case we need extra debuggability
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    main()