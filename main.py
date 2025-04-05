import os
import yt_dlp
import requests
from mutagen.mp4 import MP4, MP4Cover
from urllib.parse import unquote
import time
import subprocess

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
    
    # Instead of using postprocessors, we'll download the audio directly
    # and then manually convert it with ffmpeg for more control
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',  # Try to get m4a directly first
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'ffmpeg_location': FFMPEG_DIRECTORY,
        'keepvideo': False,
        'quiet': False,  # Show download progress
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', '')
            
            # Wait for file operations to complete
            time.sleep(1)
            
            # Find the new file by comparing directory contents
            files_after = set(os.listdir(DOWNLOAD_DIR))
            new_files = files_after - files_before
            
            if not new_files:
                print("No new files found after download")
                return None, None
            
            # Get the downloaded file (likely not an .m4a yet)
            downloaded_file = None
            for file in new_files:
                downloaded_file = file
                break
            
            if not downloaded_file:
                print("Could not find downloaded file")
                return None, None
            
            # Source file path
            source_path = os.path.join(DOWNLOAD_DIR, downloaded_file)
            
            # Prepare output file name - ensure it ends with .m4a
            base_name = os.path.splitext(downloaded_file)[0]
            output_file = f"{base_name}.m4a"
            output_path = os.path.join(DOWNLOAD_DIR, output_file)
            
            print(f"Converting {source_path} to {output_path}...")
            
            # Use ffmpeg directly for a more controlled conversion
            ffmpeg_path = os.path.join(FFMPEG_DIRECTORY, "ffmpeg.exe")
            ffmpeg_cmd = [
                ffmpeg_path,
                "-i", source_path,
                "-c:a", "aac", 
                "-b:a", "256k",
                "-movflags", "+faststart",
                "-f", "mp4",
                "-y",  # Overwrite if exists
                output_path
            ]
            
            # Run ffmpeg command
            process = subprocess.run(ffmpeg_cmd, check=True, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
            
            # If source and output file are different, remove the source file
            if source_path != output_path and os.path.exists(output_path):
                try:
                    os.remove(source_path)
                    print(f"Removed original file: {source_path}")
                except:
                    print(f"Could not remove original file: {source_path}")
            
            # Verify the new file exists
            if os.path.exists(output_path):
                print(f"Successfully converted to: {output_file}")
                return title, output_file
            else:
                print(f"Conversion failed - output file not found: {output_path}")
                return title, downloaded_file
    
    except Exception as e:
        print(f"Error during download/conversion: {e}")
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

def get_album_art_deezer(query, artist=None):
    """Search album art on Deezer"""
    # If artist is provided, use a more specific query
    search_url = f"https://api.deezer.com/search?q={query}"
    if artist:
        search_url = f"https://api.deezer.com/search?q=artist:\"{artist}\" track:\"{query}\""
    
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

def get_album_art_itunes(query, artist=None):
    """Search album art on iTunes"""
    if artist:
        # Combine artist and query with a space or + for better search results
        combined_query = f"{artist} {query}"
        # URL encode the combined query
        search_url = f"https://itunes.apple.com/search?term={combined_query}&media=music&limit=1"
    else:
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

def get_album_art_and_artist(video_title, video_info=None):
    """Try multiple sources and methods to find album art and artist info"""
    print("Searching for album art and artist info...")
    
    # Clean the title and extract artist if possible
    cleaned_title = clean_title_for_search(video_title)
    extracted_artist, title = extract_artist_title(cleaned_title)
    
    # Use artist from video_info if available
    info_artist = None
    if video_info and video_info.get('artist'):
        info_artist = video_info.get('artist')
        print(f"Using artist from video metadata: {info_artist}")
    
    # Determine the best artist to use (prefer info_artist over extracted_artist)
    best_artist = info_artist if info_artist else extracted_artist
    
    # Try different search combinations
    search_queries = []
    if best_artist and title:
        # Priority 1: Artist + Title (most specific)
        search_queries.append(f"{best_artist} {title}")
        # Priority 2: Just the artist + cleaned title
        search_queries.append(f"{best_artist} {cleaned_title}")
        # Priority 3: Just the title
        search_queries.append(title)
    else:
        # Fallback to just the cleaned title
        search_queries.append(cleaned_title)
    
    # Try each query with each service
    for query in search_queries:
        print(f"Trying search query: {query}")
        
        # Try Deezer
        result = get_album_art_deezer(query, best_artist)
        if result:
            print("Found info on Deezer")
            return result
            
        # Try iTunes
        result = get_album_art_itunes(query, best_artist)
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
        # Verify the file exists
        if not os.path.exists(song_path):
            print(f"File not found: {song_path}")
            return False
        
        # Verify the file is actually an MP4 file before trying to open it
        try:
            # Check file size first - avoid empty files
            file_size = os.path.getsize(song_path)
            if file_size < 1024:  # Less than 1KB
                print(f"File too small to be valid: {song_path} ({file_size} bytes)")
                return False
                
            audio = MP4(song_path)
        except Exception as e:
            print(f"Cannot open as MP4: {e}")
            
            # Try to fix the file with ffmpeg
            print("Attempting to fix the file format...")
            ffmpeg_path = os.path.join(FFMPEG_DIRECTORY, "ffmpeg.exe")
            temp_path = song_path + ".temp.m4a"
            
            ffmpeg_cmd = [
                ffmpeg_path,
                "-i", song_path,
                "-c:a", "copy",  # Just copy the audio stream, no re-encoding
                "-f", "mp4",     # Ensure mp4 container format
                "-y",            # Overwrite if exists
                temp_path
            ]
            
            try:
                subprocess.run(ffmpeg_cmd, check=True, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
                
                # Remove original file and rename temp file
                if os.path.exists(temp_path):
                    os.remove(song_path)
                    os.rename(temp_path, song_path)
                    print("File fixed successfully")
                    # Now try opening it again
                    audio = MP4(song_path)
                else:
                    print("Failed to fix file format")
                    return False
            except Exception as fix_e:
                print(f"Error fixing file: {fix_e}")
                return False
        
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
        return True
    except Exception as e:
        print(f"Error embedding metadata: {e}")
        return False

def process_song(song_url):
    """Process a single song - download and add metadata"""
    # Get video info first
    video_info = get_video_info(song_url)
    if not video_info:
        print("Failed to get video information")
        return False
    
    # Download the song
    downloaded_title, downloaded_filename = download_song(song_url)
    if not downloaded_title or not downloaded_filename:
        print("Failed to download song")
        return False
    
    # Clean the title for better search results
    cleaned_title = clean_title_for_search(video_info['title'])
    print(f"Processing metadata for: {cleaned_title}")
    
    # Get album art and artist info - pass both title and video_info
    metadata_info = get_album_art_and_artist(video_info['title'], video_info)
    
    # Extract artist and art URL from result
    artist = metadata_info.get('artist', None)
    album_art_url = metadata_info.get('art_url', None)
    
    # Embed metadata and album art
    song_path = os.path.join(DOWNLOAD_DIR, downloaded_filename)
    if os.path.exists(song_path):
        success = embed_metadata(song_path, cleaned_title, artist, album_art_url)
        if success:
            result_info = f"{cleaned_title}"
            if artist:
                result_info += f" by {artist}"
            print(f"Successfully processed: {result_info}")
            return True
        else:
            print(f"Failed to embed metadata for {cleaned_title}")
            return False
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