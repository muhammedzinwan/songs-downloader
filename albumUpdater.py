#!/usr/bin/env python3
"""
albumUpdater.py - Update album metadata for music files using MusicBrainz API
"""

import os
import time
import argparse
import logging
from pathlib import Path
import musicbrainzngs
from mutagen import File
from mutagen.id3 import ID3, TALB
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
import mutagen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up MusicBrainz API
musicbrainzngs.set_useragent(
    "AlbumMetadataUpdater", 
    "1.0", 
    "https://github.com/yourusername/album-updater"
)

def get_album_info(artist, title):
    """
    Query MusicBrainz API to get album information for a song
    """
    try:
        # Search for recordings (songs) with the given title and artist
        result = musicbrainzngs.search_recordings(
            query=f'recording:"{title}" AND artist:"{artist}"', 
            limit=5
        )
        
        if result and 'recording-list' in result and result['recording-list']:
            for recording in result['recording-list']:
                # Check if the recording has release (album) information
                if 'release-list' in recording:
                    # Return the first album name found
                    album_name = recording['release-list'][0]['title']
                    return album_name
        
        logger.warning(f"No album found for {artist} - {title}")
        return None
    
    except musicbrainzngs.WebServiceError as e:
        logger.error(f"MusicBrainz API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving album info: {e}")
        return None

def update_album_metadata(file_path, force_update=False):
    """
    Update the album metadata for a single music file
    """
    try:
        # Load the audio file
        audio = File(file_path)
        
        if audio is None:
            logger.warning(f"Unsupported file format: {file_path}")
            return False
        
        # Print all available tags for debugging
        logger.debug(f"Available tags for {file_path.name}: {audio.keys() if hasattr(audio, 'keys') else 'No keys method'}")
        
        # Extract artist and title from existing metadata
        artist = None
        title = None
        
        # Handle different tag formats
        # For debugging, print all available tags
        if isinstance(audio, mutagen.mp4.MP4):
            logger.debug(f"All M4A tags for {file_path.name}: {list(audio.keys())}")
            
            # For M4A files
            if '©ART' in audio:
                artist = str(audio['©ART'][0])
                logger.debug(f"Found main artist tag: {artist}")
            # Check for contributing artists if main artist is missing
            elif 'aART' in audio:
                artist = str(audio['aART'][0])
                logger.debug(f"Found album artist tag: {artist}")
            # Check for additional artist fields that might be custom
            else:
                # Look for any tag containing 'ART' (case insensitive)
                artist_tags = [key for key in audio.keys() if 'ART' in key.upper()]
                if artist_tags:
                    artist = str(audio[artist_tags[0]][0])
                    logger.debug(f"Found alternative artist tag {artist_tags[0]}: {artist}")
                    
            if '©nam' in audio:
                title = str(audio['©nam'][0])
                logger.debug(f"Found title tag: {title}")
                
            # Check if album is already set
            if not force_update and '©alb' in audio and audio['©alb'][0].strip():
                logger.info(f"Album already set for {file_path.name}: {audio['©alb'][0]}")
                return True
                
        elif isinstance(audio, mutagen.mp3.MP3):
            # For MP3 files
            if audio.tags:
                tags = audio.tags
                if isinstance(tags, ID3):
                    # Try to get info from ID3 tags
                    if 'TPE1' in tags:
                        artist = str(tags['TPE1'])
                    if 'TIT2' in tags:
                        title = str(tags['TIT2'])
                    
                    # Check if album is already set and not forcing update
                    if not force_update and 'TALB' in tags and str(tags['TALB']).strip():
                        logger.info(f"Album already set for {file_path.name}: {str(tags['TALB'])}")
                        return True
        
        # For FLAC, OGG, etc. that use a more standard interface
        else:
            if 'artist' in audio:
                artist = str(audio['artist'][0])
            if 'title' in audio:
                title = str(audio['title'][0])
                
            # Check if album is already set and not forcing update
            if not force_update and 'album' in audio and audio['album'][0].strip():
                logger.info(f"Album already set for {file_path.name}: {audio['album'][0]}")
                return True
        
        # If artist or title is missing from metadata, try to extract from filename
        if not artist or not title:
            logger.warning(f"Missing artist or title metadata for {file_path}, attempting to extract from filename")
            try:
                # Extract from filename (assuming format "Artist ♦ Title ♦.extension" or similar patterns)
                filename = file_path.stem  # Get filename without extension
                
                # Handle common separators like ♦, -, _, etc.
                for separator in ['♦', '-', '_', '–', '|']:
                    if separator in filename:
                        parts = [part.strip() for part in filename.split(separator)]
                        if len(parts) >= 2:
                            # Assuming first part is artist, second is title
                            if not artist:
                                artist = parts[0]
                            if not title:
                                title = parts[1]
                            break
                
                if not artist or not title:
                    logger.warning(f"Could not extract artist and title from filename: {filename}")
                    return False
                
                logger.info(f"Extracted from filename - Artist: {artist}, Title: {title}")
            except Exception as e:
                logger.error(f"Error extracting from filename: {e}")
                return False
        
        # Get album information from MusicBrainz
        album_name = get_album_info(artist, title)
        
        if not album_name:
            logger.warning(f"Could not find album info for {artist} - {title}")
            return False
        
        # Update the album metadata based on file type
        if isinstance(audio, mutagen.mp3.MP3):
            # For MP3 files using ID3 tags
            if not audio.tags:
                audio.tags = ID3()
            audio.tags.add(TALB(encoding=3, text=album_name))
        elif isinstance(audio, mutagen.mp4.MP4):
            # For M4A files
            audio['©alb'] = [album_name]
        else:
            # For other file types
            audio['album'] = album_name
        
        # Save the updated metadata
        audio.save()
        logger.info(f"Updated album for {file_path.name}: {album_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {file_path}: {e}")
        return False

def process_directory(directory_path, force_update=False):
    """
    Process all music files in the given directory
    """
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory not found: {directory}")
        return
    
    # List of common music file extensions
    music_extensions = {'.mp3', '.flac', '.ogg', '.m4a', '.wma', '.wav'}
    
    # Counter for statistics
    stats = {
        'total': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }
    
    logger.info(f"Scanning directory: {directory}")
    
    # Process each file in the directory
    for file_path in directory.glob('*'):
        if file_path.is_file() and file_path.suffix.lower() in music_extensions:
            stats['total'] += 1
            logger.info(f"Processing file {stats['total']}: {file_path.name}")
            
            # Update album metadata
            result = update_album_metadata(file_path, force_update)
            
            if result:
                stats['updated'] += 1
            else:
                stats['failed'] += 1
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
    
    # Print statistics
    logger.info(f"\nMetadata Update Summary:")
    logger.info(f"Total files processed: {stats['total']}")
    logger.info(f"Files updated: {stats['updated']}")
    logger.info(f"Files failed: {stats['failed']}")

def main():
    """
    Main function to parse arguments and start the update process
    """
    parser = argparse.ArgumentParser(description='Update album metadata for music files')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument('--directory', '-d', 
                        default=os.path.join(script_dir, 'downloads'),
                        help='Directory containing music files (default: script_location/downloads)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force update even if album metadata already exists')
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='Recursively process subdirectories')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    # Handle M4A files specifically
    try:
        from mutagen.mp4 import MP4
        logger.info("Mutagen MP4 support loaded")
    except ImportError:
        logger.warning("Mutagen MP4 support not available")
    
    process_directory(args.directory, args.force)

if __name__ == "__main__":
    main()