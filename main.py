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
    print("4. Merge playlists")
    print("5. playlist genres into playlists")
    print("q. Quit")
    choice = input("Enter your choice: ")
    if choice == "1":
        scan_music()
    elif choice == "2":
        classify_music()
    elif choice == "3":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(auto_tag())
    elif choice == "4":
        merge_playlists()
    elif choice == "5":
        playlist_genres_into_playlists()
    elif choice == "q":
        print("Goodbye")
        exit(0)
    else:
        print("Invalid choice")
        # prompt again
        main()
    
def get_credentials():
    # load from config file 
    client_id = ""
    client_secret = ""
    username = ""
    config_files= []

    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".cg"):
                    config_files.append(os.path.join(root, file))
                    
    if len(config_files) == 0:
        print("No config file found")
        print("Enter your credentials manually")
        client_id = input("Enter your client_id: ")
        client_secret = input("Enter your client_secret: ")
        username = input("Enter your username: ")
        return client_id, client_secret, username
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
    if client_id == "" :
        print("client_id is empty")
        client_id = input("Enter your client_id: ")
    if client_secret == "":
        print("client_secret is empty")
        client_secret = input("Enter your client_secret: ")
    if username == "":
        print("username is empty")
        username = input("Enter your username: ")

    return client_id, client_secret, username
def get_directory():
    # opne a directory selection dialog
    audio_dir = input("Enter the directory containing the audio files: ")
    # verify that the directory exists if not, prompt again
    while not os.path.isdir(audio_dir):
        audio_dir = input("Directory not found. Enter the directory containing the audio files: ")
    return audio_dir
def scan_music():
    
    client_id,client_secret,username= get_credentials()
    redirect_uri = 'http://localhost:8080'

            

    # opne a directory selection dialog
    audio_dir = get_directory()

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
    audio_dir = get_directory()
    # clear log file
    log_file = os.path.join(os.getcwd(), "spotify-classifier.log")
    with open(log_file, "w") as f:
        pass
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
                # write log file, if it doesn't exist, create it
                # create the log file in the root directory of the project
                # if the log file exists, append to it
                log_file = os.path.join(os.getcwd(), "spotify-classifier.log")
                with open(log_file, "a",encoding='utf-8') as f:
                    f.write(f'Error getting : {artist} - {title} - {file_path}\n')
        else:
            genre_dir = os.path.join(audio_dir, genre)
            if not os.path.isdir(genre_dir):
                # handle the genre that contains a slash
                if "/" in genre:
                    genre = genre.replace("/", "-")
                    genre_dir = os.path.join(audio_dir, genre)
                    if not os.path.isdir(genre_dir):
                        os.mkdir(genre_dir)
                else:
                    os.mkdir(genre_dir)
        if genre_dir != None:
            shutil.move(file_path, genre_dir)
            print(f'Moved {artist} - {title} to {genre_dir}')
            # write log file, if it doesn't exist, create it
            # create the log file in the root directory of the project
            # if the log file exists, append to it
            log_file = os.path.join(os.getcwd(), "spotify-classifier.log")
            with open(log_file, "a",encoding='utf-8') as f:
                f.write (f'moved {artist} - {title} - {file_path} to {genre_dir}\n')
            
            
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
            
# Function to handle pagination and get all tracks
def get_all_tracks(sp, username, playlist_id):
    results = sp.user_playlist_tracks(username, playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks
    
def merge_playlists():
        # get the credentials
    client_id,client_secret,username= get_credentials()
    redirect_uri = 'http://localhost:8080'

    # Get authorization token
    scope = 'playlist-modify-public playlist-modify-private user-library-read' 
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    if token:
        # show the playlists
        sp = spotipy.Spotify(auth=token)
        playlists = sp.user_playlists(username)
        for i, playlist in enumerate(playlists['items']):
            print(f'{i}: {playlist["name"]}')
        # prompt for the playlists to merge
        playlist_index1 = input("Enter the number of the first playlist: ")
        while not playlist_index1.isdigit() or int(playlist_index1) >= len(playlists['items']):
            playlist_index1 = input("Enter the number of the first playlist: ")
        playlist_index2 = input("Enter the number of the second playlist: ")
        while not playlist_index2.isdigit() or int(playlist_index2) >= len(playlists['items']):
            playlist_index2 = input("Enter the number of the second playlist: ")
        # get the playlists
        playlist1 = playlists['items'][int(playlist_index1)]
        playlist2 = playlists['items'][int(playlist_index2)]
        # merge the playlists
        # get the tracks of the first playlist
        tracks1 = get_all_tracks(sp, username, playlist1['id'])
        # get the tracks of the second playlist
        tracks2 = get_all_tracks(sp, username, playlist2['id'])
        # get the tracks ids
        track_ids1 = [track['track']['id'] for track in tracks1]
        track_ids2 = [track['track']['id'] for track in tracks2]
        print(f'Playlist 1: {playlist1["name"]} - {len(track_ids1)} tracks')
        print(f'Playlist 2: {playlist2["name"]} - {len(track_ids2)} tracks')
        # merge the tracks
        track_ids = track_ids1 + track_ids2
        # identify duplicates
        track_id_counts = {}
        for track_id in track_ids:
            if track_id in track_id_counts:
                track_id_counts[track_id] += 1
        else:
            track_id_counts[track_id] = 1
        duplicates = [track_id for track_id, count in track_id_counts.items() if count > 1]
        # write duplicates to a file
        with open('duplicates.txt', 'w') as f:
            for track_id in duplicates:
                f.write(f'{track_id}\n')
        # remove duplicates
        track_ids = list(set(track_ids))
       # create a new playlist
        playlist_name = input("Enter the name of the playlist: ")
        if playlist_name == "":
            playlist_name = f'{playlist1["name"]} + {playlist2["name"]}'
        playlist = sp.user_playlist_create(username, playlist_name, public=True)
        playlist_id = playlist['id']
        # add the tracks to the new playlist
        for i in range(0, len(track_ids), 100):
            sp.user_playlist_add_tracks(username, playlist_id, track_ids[i:i+100])
        print(f'Created playlist {playlist_name}')
    else:
        print("Can't get token for", username)


def playlist_genres_into_playlists():
    # get the credentials
    client_id,client_secret,username= get_credentials()
    redirect_uri = 'http://localhost:8080'

    # Get authorization token
    scope = 'playlist-modify-public playlist-modify-private user-library-read'
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    if token:
        # show the playlists
        sp = spotipy.Spotify(auth=token)
        playlists = sp.user_playlists(username)
        for i, playlist in enumerate(playlists['items']):
            print(f'{i}: {playlist["name"]}')
        # prompt the user for the playlist to use
        playlist_index = input("Enter the number of the playlist: ")
        while not playlist_index.isdigit() or int(playlist_index) >= len(playlists['items']):
            playlist_index = input("Enter the number of the playlist: ")
        # get the playlist
        playlist = playlists['items'][int(playlist_index)]
        # get the tracks of the playlist
        tracks = get_all_tracks(sp, username, playlist['id'])
        # create playlists for each genre
        genres = {}
        for track in tracks:
            # get the genre of the track
            genre = track['track']['album']['genres'][0]
            if genre in genres:
                genres[genre].append(track['track']['id'])
            else:
                genres[genre] = [track['track']['id']]
        # create a playlist for each genre
        for genre, track_ids in genres.items():
            # create a new playlist
            playlist_name = f'{playlist["name"]} - {genre}'
            playlist = sp.user_playlist_create(username, playlist_name, public=True)
            playlist_id = playlist['id']
            # add the tracks to the new playlist
            for i in range(0, len(track_ids), 100):
                sp.user_playlist_add_tracks(username, playlist_id, track_ids[i:i+100])
            print(f'Created playlist {playlist_name}')
    else:
        print("Can't get token for", username)
        
            
# signal handler for ctrl+c
def signal_handler(sig, frame):
    print("Exiting...")
    exit(0)
                    

    
if __name__ == "__main__":
    main()