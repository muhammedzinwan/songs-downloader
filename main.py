import os
import yt_dlp
import requests
from mutagen.mp4 import MP4, MP4Cover
from urllib.parse import unquote
import time

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
FFMPEG_DIRECTORY = r"D:\Project\SongDownloadPy\ffmpeg\ffmpeg-2025-02-20-git-bc1a3bfd2c-full_build\bin"

def get_video_info(url):
    """Get video title and other info before downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', ''),
                'artist': info.get('artist', ''),
                'track': info.get('track', '')
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

def download_song(url):
    """Download song from YouTube using yt-dlp in high quality AAC format"""
    # Get a list of files before download to compare later
    files_before = set(os.listdir(DOWNLOAD_DIR))
    
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'ffmpeg_location': FFMPEG_DIRECTORY,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'aac',
            'preferredquality': '256',  # High quality AAC
        }],
        'prefer_ffmpeg': True,
        'keepvideo': False,
        'postprocessor_args': [
            '-acodec', 'aac',
            '-vn',
            '-movflags', '+faststart',  # Optimizes for streaming/quick start
            '-profile:a', 'aac_low',    # Ensures maximum compatibility
        ],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', '')
            
            # Wait a moment for file operations to complete
            time.sleep(1)
            
            # Find the new file by comparing directory contents
            files_after = set(os.listdir(DOWNLOAD_DIR))
            new_files = files_after - files_before
            
            # Look for .m4a files among the new files
            for file in new_files:
                if file.endswith('.m4a'):
                    return title, file
            
            # If no .m4a file found but new files exist, take the first new file
            if new_files:
                for file in new_files:
                    return title, file
            
            # Fallback: try to guess the filename based on title
            possible_filename = f"{title}.m4a"
            if os.path.exists(os.path.join(DOWNLOAD_DIR, possible_filename)):
                return title, possible_filename
            
            # Ultimate fallback: search for any recent .m4a file
            for file in sorted(files_after, key=lambda f: os.path.getmtime(os.path.join(DOWNLOAD_DIR, f)), reverse=True):
                if file.endswith('.m4a'):
                    return title, file
                    
            print("Warning: Could not determine the exact downloaded file. Metadata may not be applied correctly.")
            return title, None
    except Exception as e:
        print(f"Error downloading: {e}")
        return None, None

def clean_title_for_search(title):
    """More aggressive cleaning for API search"""
    import re
    
    # Remove common features, remix mentions, etc
    removals = [
        r'ft\..*', r'feat\..*', r'\(Official.*?\)', r'\[Official.*?\]',
        r'\(Lyrics.*?\)', r'\[Lyrics.*?\]', r'\(Audio.*?\)', r'\[Audio.*?\]',
        r'\(Official Video.*?\)', r'\(Official Music Video.*?\)',
        r'\(Visualizer\)', r'\[Visualizer\]', r'Official Music Video',
        r'Official Video', r'Official Audio', r'Official Lyrics Video',
        r'Lyrics Video', r'Audio', r'HD', r'HQ', r'4K',
        r'\(.*?Remix.*?\)', r'\[.*?Remix.*?\]', r'\(.*?Ver.*?\)',
        r'\[.*?Ver.*?\]', r'\d{4}', r'MV', r'M/V'
    ]
    
    cleaned = title
    
    # Apply all removals
    for pattern in removals:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove anything in brackets or parentheses more aggressively
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    
    # Remove special characters but keep spaces
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    
    # Remove multiple spaces and trim
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()

def extract_artist_title(video_title):
    """Try to extract artist and title from video title"""
    # Common separators between artist and title
    separators = [' - ', ' – ', ' — ', ' | ', ': ', '~']
    
    for sep in separators:
        if sep in video_title:
            parts = video_title.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    
    return None, video_title.strip()

def get_album_art_deezer(query):
    """Search album art on Deezer"""
    search_url = f"https://api.deezer.com/search?q={query}"
    try:
        response = requests.get(search_url).json()
        if "data" in response and response["data"]:
            # Return album art and artist name if available
            data = response["data"][0]
            result = {
                'art_url': data["album"]["cover_big"],
                'artist': data.get("artist", {}).get("name", None)
            }
            return result
    except Exception as e:
        print(f"Deezer search error: {e}")
    return None

def get_album_art_itunes(query):
    """Search album art on iTunes"""
    search_url = f"https://itunes.apple.com/search?term={query}&media=music&limit=1"
    try:
        response = requests.get(search_url).json()
        if response["results"]:
            # Get the highest quality artwork by replacing '100x100' with larger dimensions
            result = response["results"][0]
            artwork_url = result["artworkUrl100"].replace('100x100', '1200x1200')
            return {
                'art_url': artwork_url,
                'artist': result.get("artistName", None)
            }
    except Exception as e:
        print(f"iTunes search error: {e}")
    return None

def get_album_art_and_artist(video_title):
    """Try multiple sources and methods to find album art and artist info"""
    print("Searching for album art and artist info...")
    
    # Clean the title and extract artist if possible
    cleaned_title = clean_title_for_search(video_title)
    extracted_artist, title = extract_artist_title(cleaned_title)
    
    # Try different search combinations
    search_queries = []
    if extracted_artist and title:
        search_queries.append(f"{extracted_artist} {title}")
        search_queries.append(title)
    else:
        search_queries.append(cleaned_title)
    
    # Try each query with each service
    for query in search_queries:
        print(f"Trying search query: {query}")
        
        # Try Deezer
        result = get_album_art_deezer(query)
        if result:
            print("Found info on Deezer")
            return result
            
        # Try iTunes
        result = get_album_art_itunes(query)
        if result:
            print("Found info on iTunes")
            return result
    
    # If no result found, return extracted artist if available
    if extracted_artist:
        print("No album art found, but extracted artist from title")
        return {'art_url': None, 'artist': extracted_artist}
    
    print("No album art or artist info found after trying all sources")
    return {'art_url': None, 'artist': None}

def embed_metadata(song_path, title, artist=None, image_url=None):
    """Embed metadata and album art into the M4A file"""
    try:
        audio = MP4(song_path)
        
        # Add title metadata
        audio['\xa9nam'] = [title]  # Title
        
        # Add artist metadata if available
        if artist:
            audio['\xa9ART'] = [artist]  # Artist
            print(f"Added artist metadata: {artist}")
        
        # Add album art if available
        if image_url:
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    cover = MP4Cover(response.content, imageformat=MP4Cover.FORMAT_JPEG)
                    audio['covr'] = [cover]
                    print("Album art added successfully")
            except Exception as e:
                print(f"Error adding album art: {e}")
        
        audio.save()
        print(f"Metadata embedded for: {title}")
    except Exception as e:
        print(f"Error embedding metadata: {e}")

def process_song(song_url):
    """Process a single song - download and add metadata"""
    # Get video info first
    video_info = get_video_info(song_url)
    if not video_info:
        print("Failed to get video information")
        return False
    
    # Download the song
    downloaded_title, downloaded_filename = download_song(song_url)
    if not downloaded_title:
        print("Failed to download song")
        return False
    
    # If we couldn't determine the filename
    if not downloaded_filename:
        print("Could not determine the downloaded file, skipping metadata embedding")
        return False
    
    # Clean the title for better search results
    cleaned_title = clean_title_for_search(video_info['title'])
    print(f"Processing metadata for: {cleaned_title}")
    
    # Get album art and artist info
    metadata_info = get_album_art_and_artist(video_info['title'])
    
    # Extract artist and art URL from result
    artist = metadata_info.get('artist', None)
    album_art_url = metadata_info.get('art_url', None)
    
    # Embed metadata and album art ONLY to the newly downloaded file
    song_path = os.path.join(DOWNLOAD_DIR, downloaded_filename)
    if os.path.exists(song_path):
        embed_metadata(song_path, cleaned_title, artist, album_art_url)
        result_info = f"{cleaned_title}"
        if artist:
            result_info += f" by {artist}"
        print(f"Successfully processed: {result_info}")
        return True
    else:
        print(f"Error: Could not find the downloaded file at {song_path}")
        return False

def main():
    print("=== YouTube Song Downloader ===")
    print("This tool downloads songs from YouTube and adds metadata including artist info.")
    
    while True:
        print("\nOptions:")
        print("1. Download a song")
        print("2. Quit")
        
        choice = input("Enter your choice (1-2): ").strip()
        
        if choice == "1":
            song_url = input("Enter YouTube song URL: ")
            if song_url:
                process_song(song_url)
            else:
                print("No URL provided")
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()