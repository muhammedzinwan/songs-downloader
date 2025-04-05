#!/usr/bin/env python3
"""
m4a_inspector.py - Inspect all metadata tags in M4A files
"""

import os
import sys
import logging
from pathlib import Path
from mutagen.mp4 import MP4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def inspect_m4a_file(file_path):
    """
    Display all metadata tags in an M4A file
    """
    try:
        # Load the M4A file
        audio = MP4(file_path)
        
        print(f"\n{'='*80}")
        print(f"File: {file_path}")
        print(f"{'='*80}")
        
        # Check if there are any tags
        if not audio.tags:
            print("No metadata tags found in this file.")
            return
        
        # Get all tag keys
        tags = audio.tags.keys()
        
        # Common tag meanings for reference
        tag_meanings = {
            '©nam': 'Title',
            '©ART': 'Artist',
            'aART': 'Album Artist/Contributing Artist',
            '©alb': 'Album',
            '©gen': 'Genre',
            '©day': 'Year',
            '©wrt': 'Composer',
            'trkn': 'Track Number',
            'disk': 'Disc Number',
            '©too': 'Encoding Tool',
            'covr': 'Cover Art',
            'cprt': 'Copyright',
            'purd': 'Purchase Date',
            'pgap': 'Gapless Playback',
            'sonm': 'Sort Name',
            'soar': 'Sort Artist',
            'soal': 'Sort Album',
            'soco': 'Sort Composer',
            'sosn': 'Sort Show',
            'tvsh': 'TV Show Name',
            'desc': 'Description',
            'ldes': 'Long Description',
        }
        
        # Print all tags and their values
        print("Standard Tags:")
        print("-" * 80)
        
        # First list standard tags
        standard_tags = [tag for tag in tags if tag in tag_meanings]
        for tag in standard_tags:
            meaning = tag_meanings.get(tag, "Unknown")
            value = audio.tags[tag]
            
            # Handle binary data like cover art
            if tag == 'covr':
                print(f"{tag} - {meaning}: [Binary data - {len(value)} bytes]")
            else:
                print(f"{tag} - {meaning}: {value}")
        
        # Then list any custom/unknown tags
        custom_tags = [tag for tag in tags if tag not in tag_meanings]
        if custom_tags:
            print("\nCustom or Unknown Tags:")
            print("-" * 80)
            for tag in custom_tags:
                value = audio.tags[tag]
                if isinstance(value[0], bytes):
                    print(f"{tag}: [Binary data - {len(value[0])} bytes]")
                else:
                    print(f"{tag}: {value}")
        
        # Special handling for artist information
        artist_tags = [tag for tag in tags if 'ART' in tag.upper()]
        if artist_tags:
            print("\nAll Artist-related tags found:")
            print("-" * 80)
            for tag in artist_tags:
                meaning = tag_meanings.get(tag, "Custom Artist Tag")
                value = audio.tags[tag]
                print(f"{tag} - {meaning}: {value}")
        
    except Exception as e:
        print(f"Error inspecting {file_path}: {e}")

def main():
    """
    Main function to parse arguments and start the inspection
    """
    if len(sys.argv) > 1:
        # If path is provided as argument
        path = sys.argv[1]
    else:
        # Default to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, 'downloads')
    
    path = Path(path)
    
    # Check if path exists
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.")
        return
    
    # Process single file or directory
    if path.is_file() and path.suffix.lower() == '.m4a':
        inspect_m4a_file(path)
    elif path.is_dir():
        # Collect all M4A files
        m4a_files = list(path.glob('**/*.m4a'))
        
        if not m4a_files:
            print(f"No M4A files found in {path}")
            return
            
        print(f"Found {len(m4a_files)} M4A files in {path}")
        
        # Process each file
        for file_path in m4a_files:
            inspect_m4a_file(file_path)
    else:
        print("Please provide either an M4A file or a directory containing M4A files.")

if __name__ == "__main__":
    main()