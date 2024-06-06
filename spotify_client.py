import os
from dataclasses import dataclass

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv

dotenv.load_dotenv()


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
        else:
            playlist = self.spotify.playlist(id)
        queries = []
        tracks = playlist["tracks"]["items"]
        for track in tracks:
            track_name = track["track"]["name"]
            artists = ", ".join(
                [artist["name"] for artist in track["track"]["artists"]]
            )
            queries.append(f"{track_name} by {artists}")
        return Playlist(playlist["name"], playlist["description"], queries)
