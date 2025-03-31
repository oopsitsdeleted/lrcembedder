import requests
import mutagen.flac
import os
import sys

def get_lrc_from_api(track_name, artist_name, album_name=None, duration=None):
    """Retrieves LRC lyrics from the LRCLIB API."""
    url = "https://lrclib.net/api/get"
    params = {
        "track_name": track_name,
        "artist_name": artist_name,
        "album_name": album_name,
        "duration": duration,
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print("Lyrics not found.")
        return None
    else:
        print(f"Error: {response.status_code}")
        return None

def embed_lrc_into_flac(flac_file_path, lrc_text):
    """Embeds LRC lyrics into a FLAC file."""
    try:
        audio = mutagen.flac.FLAC(flac_file_path)
        audio["UNSYNCEDLYRICS"] = lrc_text
        audio["LYRICS"] = lrc_text
        audio.save()
        print(f"LRC lyrics embedded into {flac_file_path}")
    except Exception as e:
        print(f"Error embedding lyrics: {e}")

def save_lrc_to_file(flac_file_path, lrc_text):
    """Saves LRC lyrics to a .lrc file."""
    lrc_file_path = os.path.splitext(flac_file_path)[0] + ".lrc"
    try:
        with open(lrc_file_path, "w", encoding="utf-8") as f:
            f.write(lrc_text)
        print(f"LRC lyrics saved to {lrc_file_path}")
    except Exception as e:
        print(f"Error saving LRC file: {e}")

def get_flac_metadata(flac_file_path):
    """Gets metadata from a FLAC file."""
    try:
        audio = mutagen.flac.FLAC(flac_file_path)
        track_name = audio.get("TITLE", [""])[0]
        artist_name = audio.get("ARTIST", [""])[0]
        album_name = audio.get("ALBUM", [""])[0]
        duration = int(audio.info.length)
        return track_name, artist_name, album_name, duration
    except Exception as e:
        print(f"Error reading FLAC metadata: {e}")
        return None, None, None, None

def check_embedded_lyrics(flac_file_path):
    """Checks for embedded lyrics in a FLAC file."""
    try:
        audio = mutagen.flac.FLAC(flac_file_path)
        lyrics_unsynced = audio.get("UNSYNCEDLYRICS")
        lyrics_synced = audio.get("LYRICS")
        if lyrics_unsynced or lyrics_synced:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error reading FLAC file: {e}")
        return False

def process_flac_file(flac_file_path):
    """Processes a single FLAC file."""
    if check_embedded_lyrics(flac_file_path):
        print(f"Lyrics already embedded in {flac_file_path}, skipping.")
        return

    track_name, artist_name, album_name, duration = get_flac_metadata(flac_file_path)

    if not track_name or not artist_name:
        print(f"Could not retrieve track name or artist name from {flac_file_path}.")
        return

    lyrics_data = get_lrc_from_api(track_name, artist_name, album_name, duration)

    if lyrics_data and lyrics_data.get("syncedLyrics"):
        lrc_text = lyrics_data["syncedLyrics"]
        embed_lrc_into_flac(flac_file_path, lrc_text)
        save_lrc_to_file(flac_file_path, lrc_text)

    elif lyrics_data and lyrics_data.get("plainLyrics"):
        lrc_text = lyrics_data["plainLyrics"]
        embed_lrc_into_flac(flac_file_path, lrc_text)
        save_lrc_to_file(flac_file_path, lrc_text)

    else:
        print(f"No lyrics found or available for {flac_file_path}.")

def process_directory(directory_path):
    """Recursively processes all FLAC files in a directory."""
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(".flac"):
                file_path = os.path.join(root, file)
                process_flac_file(file_path)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <directory_or_flac_file>")
        sys.exit(1)

    path = sys.argv[1]

    if not os.path.exists(path):
        print("Path not found.")
        sys.exit(1)

    if os.path.isfile(path) and path.lower().endswith(".flac"):
        process_flac_file(path)
    elif os.path.isdir(path):
        process_directory(path)
    else:
        print("Invalid path. Please enter a directory or a flac file.")
        sys.exit(1)

if __name__ == "__main__":
    main()