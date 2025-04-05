# Music Downloader With Album Art Manager

A simple solution for downloading high-quality music from YouTube and managing album artwork with a user-friendly graphical interface.
currently works with m4a files for itunes compatibility.

## Features

- **YouTube Music Download**
  - Download high-quality audio from YouTube videos
  - Automatically extract song metadata
  - Select audio quality (128k to 320k)
  - Real-time download progress and console output
  - Automatically search for matching album artwork

- **Album Art Manager**
  - View and modify album artwork for downloaded songs
  - Search for album art from multiple sources (iTunes, Deezer)
  - Browse through multiple artwork options
  - Upload custom artwork from your computer

- **Metadata Management**
  - Automatically extract artist and title from video names
  - Embed metadata in the audio files
  - Clean up video titles to get better search results

## Requirements

### Python Libraries
The following Python libraries are required:

```
yt-dlp>=2023.3.4
mutagen>=1.46.0
requests>=2.28.2
Pillow>=9.4.0
tkinter (comes with Python)
```

You can install all dependencies by using the included requirements.txt file:

```
pip install -r requirements.txt
```

### FFmpeg
This application requires FFmpeg for audio conversion. You need to:

1. Download FFmpeg from the official website: https://ffmpeg.org/download.html
   - For Windows: Download the "Windows Builds" from https://github.com/BtbN/FFmpeg-Builds/releases
   - For macOS: You can use Homebrew: `brew install ffmpeg`
   - For Linux: Use your package manager, e.g., `sudo apt install ffmpeg`

2. Extract the FFmpeg archive to a location on your computer

3. Update the `FFMPEG_DIRECTORY` variable in the script to point to your FFmpeg installation:
   ```python
   FFMPEG_DIRECTORY = r"path\to\your\ffmpeg\bin"
   ```

## Installation

1. Clone this repository or download the source code
2. Install the required Python libraries using pip:
   ```
   pip install -r requirements.txt
   ```
3. Download and extract FFmpeg as described above
4. Update the `FFMPEG_DIRECTORY` path in the script
5. Run the application:
   ```
   python main.py
   ```
6. Running the application will auto fetch album art and meta data.
   Incase of Album art variations use the alternate album art editor to manually select the album art: 
   ```
   python editAlbumArt.py
   ```

## How to Use

### Downloading Music

1. Start the application
2. Press 1 to paste the url, paste a YouTube URL in the input field
3. The application will:
   - Download the audio from YouTube
   - Convert it to high-quality AAC format
   - Automatically search for matching album artwork
   - Add metadata to the file
   - Display the song information when complete

### Managing Album Artwork

#### After downloading a song:
Use the editAlbumArt.py script to manually check and modify the album art 

#### To edit artwork for any song:
1. Go to the "Album Art Editor" tab
2. Click "Browse" to select an M4A file
3. The current metadata and artwork will be displayed
4. Enter a search term in the search field (pre-filled with artist and title)
5. Click "Search" to find artwork options
6. Use the "Previous" and "Next" buttons to browse through results
7. Click "Apply Album Art" to update the file with the selected artwork

#### To use a custom image:
1. Click "Upload Image" to select a JPG or PNG file from your computer
2. Click "Apply Album Art" to use this image as album artwork

### Update Album Names (optional):
If you would like to Update Album names for songs and other tags available
1. Run albumUpdater.py script
2. It will Run through all the files in the downloads folder and assign album names and any other data for all the downloaded songs

## Customization

You can customize the following settings in the script:

- `DOWNLOAD_DIR`: Change the download directory
- `DEFAULT_IMG_SIZE`: Change the size of displayed artwork
- Quality settings: Modify the quality combo box values

## Troubleshooting

### Common Issues

- **Download fails**: Check your internet connection and verify the YouTube URL is valid
- **Metadata not found**: Try editing the song details manually in the Album Art Editor
- **File format errors**: The application will attempt to fix incorrect formats automatically
- **Incorrect Album art**: Try changing the search queries for the album art. 

### Error Logs

When encountering issues, check the console output for detailed error messages that can help diagnose the problem.

## License

This project is released under the GLU 3.0 License. See the LICENSE file for details.

## Credits

- Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading
- Uses [Mutagen](https://github.com/quodlibet/mutagen) for audio metadata handling
- Album artwork retrieved from iTunes and Deezer APIs
