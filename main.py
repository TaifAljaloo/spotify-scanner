import os
import shutil
import signal
import requests
import spotipy
import spotipy.util as util
from shazamio import Shazam
import asyncio
from mutagen import File




def main():
    signal.signal(signal.SIGINT, signal_handler)
   # prompt the user whether to use the music scanner or the music classifier
    print("Welcome to the Spotify Scanner")
    print("1. Scan music")
    print("2. Classify music")
    print("3. Song auto tagger")
    print("q. Quit")
    choice = input("Enter your choice: ")
    if choice == "1":
        scan_music()
    elif choice == "2":
        classify_music()
    elif choice == "3":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(auto_tag())
    elif choice == "q":
        print("Goodbye")
        exit(0)
    else:
        print("Invalid choice")
        # prompt again
        main()
    
def scan_music():
    
    client_id = ''
    client_secret = ''
    username = ''
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
            elif line.startswith("username"):
                username = line.split("=")[1].strip()

                
    # verify that the client_id and client_secret are not empty 
    if client_id == "" or client_secret == "" or username == "":
        print("client_id , client_secret or username not found in config file")
        exit(1)
        

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
        # clear log file
        log_file = os.path.join(os.getcwd(), "spotify-scanner.log")
        with open(log_file, "w") as f:
            pass
        
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
            # allow only files supported by tinytag
            files = [file for file in files if file.endswith(('.mp3', '.flac', '.m4a', '.wma', '.ogg', '.opus'))]
            for file in files:
                # get the full path of the file
                file_path = os.path.join(root, file)
                # Read metadata from audio file
                tag = File(file_path, easy=True)
                artist = tag['artist'][0]
                title = tag['title'][0]
                # Search for the song on Spotify
                result = sp.search(q=f'artist:{artist} track:{title}')
                # Get the first result
                if result['tracks']['items']:
                    track = result['tracks']['items'][0]
                    track_id = track['id']
                    # Add the song to the playlist
                    sp.user_playlist_add_tracks(username, playlist_id, [track_id])
                    print(f'Added {artist} - {title} to {playlist_name}  - {file_path}')
                    # write log file, if it doesn't exist, create it
                    # create the log file in the root directory of the project
                    # if the log file exists, append to it
                    log_file = os.path.join(os.getcwd(), "spotify-scanner.log")
                    with open(log_file, "a",encoding='utf-8') as f:
                        f.write(f'{artist} - {title} - {file_path}\n')
                        
                        
                                
                                
                else:
                    print(f'No track found for {artist} - {title}')
                    # move the file to a folder called "not found"
                    not_found_dir = os.path.join(audio_dir, "not found")
                    if not os.path.isdir(not_found_dir):
                        os.mkdir(not_found_dir)
                    shutil.move(file_path, not_found_dir)
    else:
        print("Can't get token for", username)
        
        
        
    
def classify_music():
    audio_dir = input("Enter the directory containing the audio files: ")
    # verify that the directory exists if not, prompt again
    while not os.path.isdir(audio_dir):
        audio_dir = input("Directory not found. Enter the directory containing the audio files: ")
    for file_name in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, file_name)
        
        # Read metadata from audio file
        tag = File(file_path, easy=True)
        artist = tag['artist'][0]
        title = tag['title'][0]
        genre = tag['genre'][0]
        
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
            
            
async def auto_tag():
    # get the audio directory
    audio_dir = input("Enter the directory containing the audio files: ")
    # verify that the directory exists if not, prompt again
    while not os.path.isdir(audio_dir):
        audio_dir = input("Directory not found. Enter the directory containing the audio files: ")
    # run through all the files in the directory 
    for file_name in os.listdir(audio_dir):
        shazam= Shazam()
        file_path = os.path.join(audio_dir, file_name)
        # get the song name and artist name from the file
        tag = File(file_path, easy=True)
        artist = tag['artist'][0]
        title = tag['title'][0]
        # get the song name and artist name from shazam
        res = await shazam.recognize_song(file_path)
        if res['track']['title'] == title and res['track']['subtitle'] == artist:
            print(f'No change for {artist} - {title}')
        else:
            print(f'Changed {artist} - {title} to {res["track"]["subtitle"]} - {res["track"]["title"]}')
            # update the metadata
            tag['artist'] = res['track']['subtitle']
            tag['title'] = res['track']['title']
            tag.save()
            
            
# signal handler for ctrl+c
def signal_handler(sig, frame):
    print("Exiting...")
    exit(0)
                    

    
if __name__ == "__main__":
    main()