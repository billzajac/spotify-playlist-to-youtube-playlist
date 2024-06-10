import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv

dotenv.load_dotenv()

def get_spotify_username():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                                                   client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                                                   redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                                                   scope="user-read-private"))

    user = sp.current_user()
    return user['id']

if __name__ == "__main__":
    username = get_spotify_username()
    print(f"Spotify username: {username}")

