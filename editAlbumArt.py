import os
import sys
import requests
import subprocess
from mutagen.mp4 import MP4, MP4Cover
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

# Constants
FFMPEG_DIRECTORY = r"D:\Project\SongDownloadPy\ffmpeg\ffmpeg-2025-02-20-git-bc1a3bfd2c-full_build\bin"
DEFAULT_IMG_SIZE = (300, 300)

class AlbumArtEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Album Art Editor")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.current_file = None
        self.current_art_data = None
        self.current_art_url = None
        self.search_results = []
        self.current_result_index = 0
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create file selection area
        self.file_frame = ttk.LabelFrame(self.main_frame, text="Song File", padding="10")
        self.file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=60)
        self.file_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.browse_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Create metadata display area
        self.metadata_frame = ttk.LabelFrame(self.main_frame, text="Current Metadata", padding="10")
        self.metadata_frame.pack(fill=tk.X, pady=5)
        
        # Title and artist display
        self.title_label = ttk.Label(self.metadata_frame, text="Title: ")
        self.title_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.artist_label = ttk.Label(self.metadata_frame, text="Artist: ")
        self.artist_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Current album art display
        self.art_frame = ttk.LabelFrame(self.main_frame, text="Album Art", padding="10")
        self.art_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a frame for the current artwork
        self.current_art_frame = ttk.Frame(self.art_frame)
        self.current_art_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.current_art_label = ttk.Label(self.current_art_frame, text="Current Album Art")
        self.current_art_label.pack(pady=5)
        
        self.current_art_display = ttk.Label(self.current_art_frame)
        self.current_art_display.pack(expand=True)
        
        # Create a frame for the new artwork
        self.new_art_frame = ttk.Frame(self.art_frame)
        self.new_art_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.new_art_label = ttk.Label(self.new_art_frame, text="New Album Art")
        self.new_art_label.pack(pady=5)
        
        self.new_art_display = ttk.Label(self.new_art_frame)
        self.new_art_display.pack(expand=True)
        
        # Search controls
        self.search_frame = ttk.LabelFrame(self.main_frame, text="Search for Album Art", padding="10")
        self.search_frame.pack(fill=tk.X, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.search_album_art)
        self.search_button.pack(side=tk.LEFT, padx=5)
        
        # Navigation and action buttons
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(fill=tk.X, pady=10)
        
        self.prev_button = ttk.Button(self.nav_frame, text="< Previous", command=self.previous_result, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.result_label = ttk.Label(self.nav_frame, text="No results")
        self.result_label.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(self.nav_frame, text="Next >", command=self.next_result, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Upload custom image
        self.upload_button = ttk.Button(self.nav_frame, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(side=tk.LEFT, padx=20)
        
        # Apply button
        self.apply_button = ttk.Button(self.nav_frame, text="Apply Album Art", command=self.apply_album_art, state=tk.DISABLED)
        self.apply_button.pack(side=tk.RIGHT, padx=5)
    
    def browse_file(self):
        """Open file dialog to select an M4A file"""
        file_path = filedialog.askopenfilename(
            title="Select M4A File",
            filetypes=[("M4A files", "*.m4a"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.current_file = file_path
            self.load_metadata()
    
    def load_metadata(self):
        """Load and display metadata from the selected file"""
        try:
            if not os.path.exists(self.current_file):
                messagebox.showerror("Error", f"File not found: {self.current_file}")
                return
            
            # Try to open as MP4
            try:
                audio = MP4(self.current_file)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open as MP4: {e}")
                return
            
            # Extract metadata
            title = audio.get('\xa9nam', ['Unknown Title'])[0]
            artist = audio.get('\xa9ART', ['Unknown Artist'])[0]
            
            # Update UI
            self.title_label.config(text=f"Title: {title}")
            self.artist_label.config(text=f"Artist: {artist}")
            
            # Populate search field with artist and title
            self.search_var.set(f"{artist} {title}")
            
            # Extract and display album art
            if 'covr' in audio:
                self.current_art_data = audio['covr'][0]
                self.display_image(self.current_art_data, self.current_art_display)
            else:
                self.current_art_data = None
                self.display_default_image(self.current_art_display, "No Current Album Art")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error loading metadata: {e}")
    
    def search_album_art(self):
        """Search for album art using search term"""
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showinfo("Info", "Please enter a search term")
            return
        
        self.search_results = []
        self.current_result_index = 0
        
        # Try iTunes first
        self.search_itunes(search_term)
        
        # Then try Deezer
        self.search_deezer(search_term)
        
        # Update UI based on results
        if self.search_results:
            self.update_result_display()
            self.update_navigation_buttons()
            self.apply_button.config(state=tk.NORMAL)
        else:
            messagebox.showinfo("No Results", "No album art found. Try a different search term.")
            self.display_default_image(self.new_art_display, "No Results Found")
            self.result_label.config(text="No results")
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.apply_button.config(state=tk.DISABLED)
    
    def search_itunes(self, query):
        """Search album art on iTunes"""
        search_url = f"https://itunes.apple.com/search?term={query}&media=music&limit=10"
        try:
            response = requests.get(search_url).json()
            for result in response.get("results", []):
                if "artworkUrl100" in result:
                    # Get the highest quality artwork by replacing '100x100' with larger dimensions
                    artwork_url = result["artworkUrl100"].replace('100x100', '1200x1200')
                    artist = result.get("artistName", "Unknown Artist")
                    album = result.get("collectionName", "Unknown Album")
                    track = result.get("trackName", "Unknown Track")
                    
                    self.search_results.append({
                        'art_url': artwork_url,
                        'artist': artist,
                        'album': album,
                        'track': track,
                        'source': 'iTunes'
                    })
        except Exception as e:
            print(f"iTunes search error: {e}")
    
    def search_deezer(self, query):
        """Search album art on Deezer"""
        search_url = f"https://api.deezer.com/search?q={query}&limit=10"
        try:
            response = requests.get(search_url).json()
            for item in response.get("data", []):
                if "album" in item and "cover_big" in item["album"]:
                    artwork_url = item["album"]["cover_big"]
                    artist = item.get("artist", {}).get("name", "Unknown Artist")
                    album = item.get("album", {}).get("title", "Unknown Album")
                    track = item.get("title", "Unknown Track")
                    
                    self.search_results.append({
                        'art_url': artwork_url,
                        'artist': artist,
                        'album': album,
                        'track': track,
                        'source': 'Deezer'
                    })
        except Exception as e:
            print(f"Deezer search error: {e}")
    
    def update_result_display(self):
        """Update UI to display current search result"""
        if not self.search_results:
            return
        
        result = self.search_results[self.current_result_index]
        
        # Display the image
        try:
            response = requests.get(result['art_url'])
            if response.status_code == 200:
                image_data = response.content
                self.display_image(image_data, self.new_art_display)
                self.current_art_url = result['art_url']
            else:
                self.display_default_image(self.new_art_display, "Image Load Error")
                self.current_art_url = None
        except Exception as e:
            print(f"Error loading image: {e}")
            self.display_default_image(self.new_art_display, "Image Load Error")
            self.current_art_url = None
        
        # Update result counter
        self.result_label.config(
            text=f"Result {self.current_result_index+1} of {len(self.search_results)}: "
                f"{result['track']} - {result['artist']} ({result['source']})"
        )
    
    def next_result(self):
        """Show next search result"""
        if self.current_result_index < len(self.search_results) - 1:
            self.current_result_index += 1
            self.update_result_display()
            self.update_navigation_buttons()
    
    def previous_result(self):
        """Show previous search result"""
        if self.current_result_index > 0:
            self.current_result_index -= 1
            self.update_result_display()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        if self.current_result_index <= 0:
            self.prev_button.config(state=tk.DISABLED)
        else:
            self.prev_button.config(state=tk.NORMAL)
        
        if self.current_result_index >= len(self.search_results) - 1:
            self.next_button.config(state=tk.DISABLED)
        else:
            self.next_button.config(state=tk.NORMAL)
    
    def upload_image(self):
        """Allow user to upload a custom image as album art"""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Read the image file
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # Display the image
                self.display_image(image_data, self.new_art_display)
                
                # Store image data for later use
                self.current_art_url = None
                self.search_results = [{
                    'art_url': None,
                    'artist': "Custom Image",
                    'album': os.path.basename(file_path),
                    'track': "Custom Upload",
                    'source': 'Local File',
                    'data': image_data
                }]
                self.current_result_index = 0
                
                # Update UI
                self.result_label.config(text=f"Custom image: {os.path.basename(file_path)}")
                self.prev_button.config(state=tk.DISABLED)
                self.next_button.config(state=tk.DISABLED)
                self.apply_button.config(state=tk.NORMAL)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {e}")
    
    def apply_album_art(self):
        """Apply the selected album art to the current file"""
        if not self.current_file:
            messagebox.showinfo("Info", "Please select a song file first")
            return
        
        if not self.search_results:
            messagebox.showinfo("Info", "Please search for album art first")
            return
        
        try:
            # Get the selected result
            result = self.search_results[self.current_result_index]
            
            # Get the image data
            image_data = None
            if 'data' in result:  # For uploaded images
                image_data = result['data']
            elif result['art_url']:  # For search results
                response = requests.get(result['art_url'])
                if response.status_code == 200:
                    image_data = response.content
            
            if not image_data:
                messagebox.showerror("Error", "Could not retrieve image data")
                return
            
            # Create a backup of the original file
            base_dir = os.path.dirname(self.current_file)
            base_name = os.path.basename(self.current_file)
            #backup_file = os.path.join(base_dir, f"backup_{base_name}")
            
            # Copy file as backup
            #try:
               # with open(self.current_file, 'rb') as src, open(backup_file, 'wb') as dst:
              #      dst.write(src.read())
             #   print(f"Backup created: {backup_file}")
           # except Exception as e:
          #      print(f"Warning: Could not create backup: {e}")
            
            # Open the MP4 file
            audio = MP4(self.current_file)
            
            # Create MP4Cover from image data
            cover = MP4Cover(image_data, imageformat=MP4Cover.FORMAT_JPEG)
            
            # Set the cover art
            audio['covr'] = [cover]
            
            # Save the file
            audio.save()
            
            # Update the current display
            self.current_art_data = cover
            self.display_image(image_data, self.current_art_display)
            
            messagebox.showinfo("Success", "Album art has been updated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error applying album art: {e}")
    
    def display_image(self, image_data, label_widget):
        """Display image in the given label widget"""
        try:
            # Convert image data to PIL Image
            img = Image.open(BytesIO(image_data))
            
            # Resize the image to fit the display area
            img.thumbnail(DEFAULT_IMG_SIZE)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update label
            label_widget.config(image=photo)
            label_widget.image = photo  # Keep a reference to prevent garbage collection
            
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.display_default_image(label_widget, "Image Error")
    
    def display_default_image(self, label_widget, text="No Image"):
        """Display a placeholder for missing images"""
        label_widget.config(image='')
        label_widget.config(text=text, font=('Arial', 12))

def fix_mp4_file(file_path):
    """Attempt to fix an MP4 file if it's corrupted"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Check if we can open it as an MP4 file
        MP4(file_path)
        print("File is already a valid MP4, no fixing needed")
        return True
    except Exception as e:
        print(f"File is not a valid MP4: {e}")
        
        # Try to fix the file with ffmpeg
        print("Attempting to fix the file format...")
        ffmpeg_path = os.path.join(FFMPEG_DIRECTORY, "ffmpeg.exe")
        temp_path = file_path + ".temp.m4a"
        
        ffmpeg_cmd = [
            ffmpeg_path,
            "-i", file_path,
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
                os.remove(file_path)
                os.rename(temp_path, file_path)
                print("File fixed successfully")
                return True
            else:
                print("Failed to fix file format")
                return False
        except Exception as fix_e:
            print(f"Error fixing file: {fix_e}")
            return False

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = AlbumArtEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()