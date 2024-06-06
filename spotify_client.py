import os
from dataclasses import dataclass

from datetime import datetime

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
        if (id == "current_user_saved_tracks"):
            playlist = self.spotify.current_user_saved_tracks()
            name = "Liked Songs"
            description = f"Spotify Liked Songs as of {datestamp}"
            tracks = playlist["items"]
        else:
            playlist = self.spotify.playlist(id)
            name = playlist["name"]
            description = playlist["description"]
            tracks = playlist["tracks"]["items"]
        queries = []
        for track in tracks:
            track_name = track["track"]["name"]
            artists = ", ".join(
                [artist["name"] for artist in track["track"]["artists"]]
            )
            queries.append(f"{track_name} by {artists}")
        return Playlist(name, description, queries)
