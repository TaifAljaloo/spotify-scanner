import os
import shutil
import signal
import requests
import spotipy
import spotipy.util as util
from tinytag import TinyTag


def main():
    signal.signal(signal.SIGINT, signal_handler)
   # prompt the user whether to use the music scanner or the music classifier
    print("Welcome to the Spotify Scanner")
    print("1. Scan music")
    print("2. Classify music")
    print("q. Quit")
    choice = input("Enter your choice: ")
    if choice == "1":
        scan_music()
    elif choice == "2":
        classify_music()
    elif choice == "q":
        exit(0)
    else:
        print("Invalid choice")
        # prompt again
        main()
    
def scan_music():
    client_id = ''
    client_secret = ''
    redirect_uri = 'http://localhost:8080'

    # load from config file 
    config_files= []

    for root, _, files in os.walk("."):
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
        
        # Add songs to the playlist
        # walk through the audio directory and all subdirectories
        for root, _, files in os.walk(audio_dir):
            # ignore lrc files
            files = [f for f in files if not f.endswith(".lrc")]
            for file in files:
                # get the full path of the file
                file_path = os.path.join(root, file)
                # Read metadata from audio file
                tag = TinyTag.get(file_path)
                artist = tag.artist
                title = tag.title
                # Search for the song on Spotify
                result = sp.search(q=f'artist:{artist} track:{title}')
                # Get the first result
                if result['tracks']['items']:
                    track = result['tracks']['items'][0]
                    track_id = track['id']
                    # Add the song to the playlist
                    sp.user_playlist_add_tracks(username, playlist_id, [track_id])
                    print(f'Added {artist} - {title} to {playlist_name}')
                else:
                    print(f'No track found for {artist} - {title}')
    else:
        print("Can't get token for", username)
        
        
        
    
def classify_music():
    print("classify_music")
    audio_dir = input("Enter the directory containing the audio files: ")
    # verify that the directory exists if not, prompt again
    while not os.path.isdir(audio_dir):
        audio_dir = input("Directory not found. Enter the directory containing the audio files: ")
    for file_name in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, file_name)
        
        # Read metadata from audio file
        tag = TinyTag.get(file_path)
        artist = tag.artist
        title = tag.title
        genre = tag.genre
        
        genre_dir= None
        if genre == None:
            api_key = "3b40785e5f90f8730344e6d9fca069a3"
            url = f"https://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={title}&format=json"
            response = requests.get(url)
            if response.status_code == 200:
                # get the genre from the response
                genre = response.json()['track']['toptags']['tag'][0]['name']
                genre_dir = os.path.join(audio_dir, genre)
                if not os.path.isdir(genre_dir):
                    os.mkdir(genre_dir)
            else:
                print(f'Error getting genre for {artist} - {title}')
        else:
            genre_dir = os.path.join(audio_dir, genre)
            if not os.path.isdir(genre_dir):
                os.mkdir(genre_dir)
        if genre_dir != None:
            shutil.move(file_path, genre_dir)
            print(f'Moved {artist} - {title} to {genre_dir}')
            
            
            
            
# signal handler for ctrl+c
def signal_handler(sig, frame):
    print("Exiting...")
    exit(0)
                    

    
if __name__ == "__main__":
    main()