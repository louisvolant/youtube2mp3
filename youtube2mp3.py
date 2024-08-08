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
# pip install yt-dlp
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
    parser.add_argument('url', type=str, help='The URL of the YouTube video')
    #parser.add_argument('output', type=str, nargs='?', default=BASE_OUTPUT_FILENAME, help='The output MP3 file path')
    # Example : python3 youtube2mp3.py https://www.youtube.com/watch?v=K65eFWaVq3w output_mision_control.mp3
    parser.add_argument('--audio_quality', '-q', default=TARGET_BITRATE, help='The audio quality in kbps (default: 128K)')

    args = parser.parse_args()

    # Get the video title and sanitize it for use as a filename
    video_title = get_youtube_title(args.url)
    sanitized_title = sanitize_filename(video_title)
    output_path = f"{sanitized_title}.mp3"

    logging.info('Processing: {0} and storing to {1}'.format(args.url, output_path))

    download_youtube_audio(args.url, output_path, args.audio_quality)


if __name__ == '__main__':
    ## Initialize logging before hitting main, in case we need extra debuggability
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    main()