import os
import spotipy
import spotipy.util as util
from tinytag import TinyTag

client_id = ''
client_secret = ''
redirect_uri = 'http://localhost:8080'

# load from config file 
config_files= []

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".cg"):
                config_files.append(os.path.join(root, file))
                
if len(config_files) == 0:
    print("No config file found")
    exit(1)
# prompt all the config files found
print("Select the config file:")
for i, file in enumerate(config_files):
    print(f'{i}: {file}')
    
# prompt for the config file
config_file_index = input("Enter the number of the config file: ")
while not config_file_index.isdigit() or int(config_file_index) >= len(config_files):
    config_file_index = input("Enter the number of the config file: ")
    
# load the config file
config_file = config_files[int(config_file_index)]
with open(config_file, "r") as f:
    lines = f.readlines()
    for line in lines:
        if line.startswith("client_id"):
            client_id = line.split("=")[1].strip()
        elif line.startswith("client_secret"):
            client_secret = line.split("=")[1].strip()

            
# verify that the client_id and client_secret are not empty 
if client_id == "" or client_secret == "":
    print("client_id or client_secret not found in config file")
    exit(1)
    
    

# prompt for username
username = input("Enter your Spotify username: ")

# opne a directory selection dialog
audio_dir = input("Enter the directory containing the audio files: ")
# verify that the directory exists if not, prompt again
while not os.path.isdir(audio_dir):
    audio_dir = input("Directory not found. Enter the directory containing the audio files: ")

# Create a playlist
playlist_name = input("Enter the name of the playlist: ")

# Get authorization token
scope = 'playlist-modify-public'
token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

if token:
    # Create Spotify object
    sp = spotipy.Spotify(auth=token)

    # Create a new playlist
    if playlist_name == "":
        playlist_name = "My Playlist spotify-scanner"
    playlist = sp.user_playlist_create(username, playlist_name, public=True)
    playlist_id = playlist['id']
    
    # Iterate through audio files
    for file_name in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, file_name)
        
        # Read metadata from audio file
        tag = TinyTag.get(file_path)
        artist = tag.artist
        title = tag.title
        
        # Search for the song on Spotify
        results = sp.search(q=f'artist:{artist} track:{title}', type='track', limit=1)
        if results['tracks']['items']:
            track_id = results['tracks']['items'][0]['id']
            
            # Add the song to the playlist
            sp.user_playlist_add_tracks(username, playlist_id, [track_id])
            print(f'Added {artist} - {title} to playlist')
        else:
            # create a file with the songs not found
            print(f'Song not found on Spotify: {artist} - {title} - file: {file_name}')
            with open("songs_not_found.txt", "a") as f:
                f.write(f'{artist} - {title} - { file_name} \n')
else:
    print("Couldn't get token for", username)
    
    

            
