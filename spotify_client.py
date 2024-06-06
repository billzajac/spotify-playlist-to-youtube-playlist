import os
from dataclasses import dataclass
from datetime import datetime
import json

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv

dotenv.load_dotenv()

# Get the current date
current_date = datetime.now()

# Format the date as YYYY-MM-DD
datestamp = current_date.strftime("%Y-%m-%d")

@dataclass
class Playlist:
    name: str
    description: str
    tracks: list[str]

class SpotifyClient:
    def __init__(self) -> None:
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        REDIRECT_URI = os.getenv("REDIRECT_URI")
        SCOPE = os.getenv("SCOPE")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                                 client_secret=CLIENT_SECRET,
                                                                 redirect_uri=REDIRECT_URI,
                                                                 scope=SCOPE))

    def get_playlist(self, id: str):
        if id == "current_user_saved_tracks":
            tracks = []
            results = self.spotify.current_user_saved_tracks()
            while results:
                tracks.extend(results["items"])
                results = self.spotify.next(results) if results['next'] else None

            tracks = [track["track"] for track in tracks]
            unique_tracks = {f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}": track for track in tracks}.values()
            sorted_tracks = sorted(unique_tracks, key=lambda track: (track["artists"][0]["name"], track["name"]))

            name = "Liked Songs"
            description = f"Spotify Liked Songs as of {datestamp}"
            track_queries = [f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}" for track in sorted_tracks]

            with open("sorted_tracks.json", "w") as file:
                json.dump(track_queries, file, indent=4)

            return Playlist(name, description, track_queries)
        else:
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

