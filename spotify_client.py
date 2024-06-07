import os
from dataclasses import dataclass
from datetime import datetime
import json

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv
import logging

dotenv.load_dotenv()

# Get the current date
current_date = datetime.now()

# Format the date as YYYY-MM-DD
datestamp = current_date.strftime("%Y-%m-%d")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Playlist:
    name: str
    description: str
    tracks: list[str]


class SpotifyClient:
    def __init__(self) -> None:
        CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
        CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
        REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
        SCOPE = "user-library-read"

        if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
            raise ValueError("Missing Spotify API credentials. Please set them in the .env file.")

        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

    def get_playlist(self, id: str):
        if id == "current_user_saved_tracks":
            logging.info("Fetching current user saved tracks")
            tracks = []
            results = self.spotify.current_user_saved_tracks(limit=50)
            tracks.extend(results["items"])
            while results["next"]:
                results = self.spotify.next(results)
                tracks.extend(results["items"])
                logging.info(f"Fetched {len(tracks)} tracks so far")

            name = "Spotify Liked Songs"
            description = f"Spotify Liked Songs as of {datestamp}"

            # Alphabetize and remove duplicates
            unique_tracks = {f"{track['track']['artists'][0]['name']} - {track['track']['name']}": track for track in tracks}
            sorted_tracks = sorted(unique_tracks.values(), key=lambda x: (x['track']['artists'][0]['name'], x['track']['name']))
            track_list = [f"{track['track']['name']} by {', '.join([artist['name'] for artist in track['track']['artists']])}" for track in sorted_tracks]

            # Save to JSON
            with open("saved_tracks.json", "w") as file:
                json.dump({"name": name, "description": description, "tracks": track_list}, file, indent=4)

            return Playlist(name, description, track_list)
        else:
            logging.info(f"Fetching playlist with ID: {id}")
            playlist = self.spotify.playlist(id)
            name = playlist["name"]
            description = playlist["description"]
            tracks = playlist["tracks"]["items"]
            queries = []
            for track in tracks:
                track_name = track["track"]["name"]
                artists = ", ".join([artist["name"] for artist in track["track"]["artists"]])
                queries.append(f"{track_name} by {artists}")
            return Playlist(name, description, queries)

    def get_playlist_from_json(self, json_data):
        name = json_data["name"]
        description = json_data["description"]
        tracks = json_data["tracks"]
        return Playlist(name, description, tracks)

