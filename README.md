# Youtube2Mp3
Python3 tool to retrieve MP3 sound from a given Youtube video

**You should only retrieve copyright free MP3 sounds**

## Requirements

Python3, os, logging, subprocess

````
python3 -m venv myenv
source myenv/bin/activate
pip install yt-dlp
python3 youtube2mp3.py "https://www.youtube.com/watch?v=YOUTUBE_ID" 
````

## How to execute

Go in the same folder than the python script and type

````
$ python3 youtube2mp3.py -u "https://www.youtube.com/watch?v=YOUTUBE_ID"
````
OR
````
$ python3 youtube2mp3.py -v YOUTUBE_ID
````