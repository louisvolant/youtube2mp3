import pytesseract
from PIL import Image
import os
import sys
import google.generativeai as genai
import re
import subprocess

# Define a constant for our separator
DATA_SEPARATOR = "---NEW_SECTION---"

# --- Configuration for Gemini API (kept for completeness, but not used for extraction here) ---
GEMINI_API_KEY = os.getenv('GEMINI_AI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_AI_API_KEY not set. Gemini API calls will be skipped if they were used.")


def clean_ocr_text(text):
    """
    Cleans the OCR text by replacing common date/time patterns
    and known UI noise with a clear separator or by simply removing them.
    """
    cleaned_text = text.lower()

    # --- Step 1: Remove common UI noise patterns (high priority) ---
    ui_noise_patterns = [
        r'n\s*ol\s*>\s*&',
        r'<\s*titres\s*n\s*q\s*3x',
        r'x\s*\n\s*<',
        r'mai\s+2025',
        r'titres\s*ab\s*©\s*\)\s*re',
        r'x\s*\.',
        r'<\s*titres\s*\(>\)\s*©\s*\)\s*be',
        r'®\s*ul\s*=\s*@',
        r'4\s*titres\s*ab\s*©\s*\)\s*b=',
        r'\.',
        r'r¢\s*titres\s*an\s*\)',
        r'la\s*semaine\s*derniére',
        r'titres\s*n\s*q\s*3='
    ]

    for pattern in ui_noise_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text)

    # --- Step 2: Replace main date/time patterns with DATA_SEPARATOR ---
    french_months = "(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"

    # Most comprehensive date/time pattern
    full_date_time_pattern = rf'\b\d{{1,2}}\s+{french_months}(?:\s+\d{{4}})?\s*[a&]?\s*(?:\d{{1,2}}:\d{{2}})?\b'
    cleaned_text = re.sub(full_date_time_pattern, DATA_SEPARATOR, cleaned_text)

    # Simple time patterns (e.g., "22:59")
    cleaned_text = re.sub(r'\b\d{1,2}:\d{2}\b', DATA_SEPARATOR, cleaned_text)

    # Day-of-week patterns ("hier", "aujourd'hui", etc.)
    cleaned_text = re.sub(r'\b(hier|aujourd\'hui|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b', DATA_SEPARATOR, cleaned_text)

    # --- Step 3: Remove lingering numerical remnants of dates/times near separators ---
    # This targets patterns like "19 a", "22 &", "19 4", etc. that precede a separator.
    # It looks for 1-2 digits, followed by optional spaces, then optional a/& or another digit/character,
    # and then optional spaces before the DATA_SEPARATOR.
    # This specifically aims to remove the "19 4" remnants.
    cleaned_text = re.sub(r'\b\d{1,2}\s*(?:[a&]|\d{1,2}|\w)?\s*' + re.escape(DATA_SEPARATOR), DATA_SEPARATOR, cleaned_text)


    # --- Step 4: Final cleanup (after all pattern replacements) ---
    cleaned_text = re.sub(r'\n\s*\n+', '\n', cleaned_text)
    cleaned_text = re.sub(rf'{re.escape(DATA_SEPARATOR)}\s*{re.escape(DATA_SEPARATOR)}', DATA_SEPARATOR, cleaned_text)
    cleaned_text = re.sub(rf'^{re.escape(DATA_SEPARATOR)}\s*|\s*{re.escape(DATA_SEPARATOR)}$', '', cleaned_text)

    return cleaned_text.strip()



def parse_song_data_from_cleaned_text(cleaned_text_with_separators):
    """
    Parses the cleaned text (with DATA_SEPARATORs) into song title and artist pairs.
    Assumes pattern: (Title lines) \n (Artist line) \n ---NEW_SECTION---
    """
    song_data_list = []

    blocks = cleaned_text_with_separators.split(DATA_SEPARATOR)

    for block in blocks:
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]

        if len(lines) >= 2:
            artist = lines[-1]
            title_lines = lines[:-1]
            song_title = '\n'.join(title_lines)

            song_data_list.append({
                "song_title": song_title,
                "artist": artist
            })
        elif len(lines) == 1:
            song_data_list.append({
                "song_title": lines[0],
                "artist": ""
            })

    return song_data_list


def find_youtube_url(query):
    """
    Uses yt-dlp to search YouTube for a video URL based on the query.
    Returns the URL or None if not found.
    """
    print(f"Searching YouTube for: '{query}'...")

    # Construct the full path to yt-dlp within the active virtual environment
    # sys.prefix points to the base directory of the virtual environment (e.g., /path/to/myenv)
    yt_dlp_path = os.path.join(sys.prefix, 'bin', 'yt-dlp')

    if not os.path.exists(yt_dlp_path):
        print(f"Error: yt-dlp not found at expected location: {yt_dlp_path}.")
        print(
            "Please ensure yt-dlp is installed in your virtual environment (pip install yt-dlp) and the virtual environment is active.")
        return None

    try:
        command = [yt_dlp_path, f'ytsearch1:{query}', '--get-url']  # Use the full path
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        url = result.stdout.strip()
        if url:
            print(f"Found URL: {url}")
            return url
        else:
            print("No URL found.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error during Youtube for '{query}': {e.stderr.strip()}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during search: {e}")
        return None


def download_audio_with_script(youtube_url, song_title, artist, script_path, audio_quality='128K',
                               add_account_name=True):
    """
    Calls the youtube2mp3.py script to download audio.
    """
    print(f"Attempting to download '{song_title}' by '{artist}' from {youtube_url}...")
    command = [
        sys.executable,  # Use the current Python interpreter (from activated venv)
        script_path,
        '-u', youtube_url,
        '-q', audio_quality
    ]

    # Add artist name argument if available
    if artist:
        command.extend(['-a', artist])

    # Add account name argument if enabled
    if add_account_name:
        command.append('-n')

    try:
        # Set check=True to raise CalledProcessError on non-zero exit codes
        subprocess.run(command, check=True)
        print(f"Successfully initiated download for '{song_title}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading audio for '{song_title}':")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
    except FileNotFoundError:
        print(f"Error: {script_path} not found. Ensure the script path is correct.")
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")


def extract_text_from_images(folder_path):
    """
    Extracts text from all PNG images in the specified folder,
    cleans it, parses it, finds YouTube URLs, and downloads audio.
    Files are processed in alphabetical order by name.
    """
    # Assuming youtube2mp3.py is in the same directory as ocr_script.py
    youtube2mp3_script_path = os.path.join(folder_path, 'youtube2mp3.py')
    if not os.path.exists(youtube2mp3_script_path):
        print(
            f"Error: youtube2mp3.py not found at {youtube2mp3_script_path}. Please ensure it's in the same directory.")
        return

    sorted_filenames = sorted(os.listdir(folder_path))

    for filename in sorted_filenames:
        if filename.lower().endswith(".png"):
            image_path = os.path.join(folder_path, filename)
            print(f"\n{'=' * 20} Processing {filename} {'=' * 20}\n")  # More prominent separator
            try:
                img = Image.open(image_path)
                ocr_text = pytesseract.image_to_string(img)

                cleaned_ocr_text = clean_ocr_text(ocr_text)
                print(f"Cleaned OCR Text (with separators):\n{cleaned_ocr_text}\n")

                extracted_songs = parse_song_data_from_cleaned_text(cleaned_ocr_text)

                if extracted_songs:
                    print("Extracted Song Information (Direct Parsing):\n")
                    for item in extracted_songs:
                        title = item.get('song_title', '').replace('\n', ' ').strip()  # Replace newlines, then strip
                        artist = item.get('artist', '').replace('\n', ' ').strip()  # Replace newlines, then strip

                        if not title and not artist:
                            print("  Skipping empty entry.")
                            continue

                        print(f"  Title : {title} / Artist : {artist}")

                        # Formulate a search query. Add "official audio" or "music video" for better results.
                        search_query = f"{title} {artist} official audio" if artist else f"{title} official audio"

                        youtube_url = find_youtube_url(search_query)

                        if youtube_url:
                            # Call youtube2mp3.py script
                            download_audio_with_script(
                                youtube_url,
                                title,
                                artist,
                                youtube2mp3_script_path,
                                audio_quality='128K',  # Or make this configurable
                                add_account_name=True  # Or make this configurable
                            )
                        else:
                            print(f"Could not find a YouTube URL for '{title}' by '{artist}'. Skipping download.\n")

                    print(f"\n{'=' * 50}\n")
                else:
                    print("No song information extracted from this image.\n" + "=" * 50 + "\n")

            except Exception as e:
                print(f"Error processing {filename}: {e}\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    folder_path = "."
    extract_text_from_images(folder_path)