import os
import json
import logging
import click
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv
from dataclasses import dataclass
from datetime import datetime

dotenv.load_dotenv()

# Get the current date
current_date = datetime.now()
datestamp = current_date.strftime("%Y-%m-%d")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Playlist:
    name: str
    description: str
    tracks: list[str]

class SpotifyClient:
    def __init__(self, username) -> None:
        self.username = username
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                                                                 client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                                                                 redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                                                                 scope="user-library-read",
                                                                 username=username))

    def get_saved_tracks(self):
        logging.info(f"Fetching saved tracks for user: {self.username}")
        tracks = []
        results = self.spotify.current_user_saved_tracks(limit=50)
        tracks.extend(results["items"])
        while results["next"]:
            results = self.spotify.next(results)
            tracks.extend(results["items"])
            logging.info(f"Fetched {len(tracks)} tracks so far")

        name = f"{self.username}'s Spotify Liked Songs"
        description = f"Spotify Liked Songs as of {datestamp}"

        # Alphabetize and remove duplicates
        #unique_tracks = {f"{track['track']['artists'][0]['name']} - {track['track']['name']}": track for track in tracks}
        #sorted_tracks = sorted(unique_tracks.values(), key=lambda x: (x['track']['artists'][0]['name'], x['track']['name']))
        #track_list = [f"{track['track']['name']} by {', '.join([artist['name'] for artist in track['track']['artists']])}" for track in sorted_tracks]
        track_list = tracks

        # Save to JSON
        with open(f"saved_tracks_{self.username}.json", "w") as file:
            json.dump({"name": name, "description": description, "tracks": track_list}, file, indent=4)

        logging.info(f"Saved tracks saved to saved_tracks_{self.username}.json")
        return Playlist(name, description, track_list)

@click.command()
@click.argument('username')
def main(username):
    spotify_client = SpotifyClient(username)
    spotify_client.get_saved_tracks()

if __name__ == "__main__":
    main()

