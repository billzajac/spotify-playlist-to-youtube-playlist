import os
from dataclasses import dataclass

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv

dotenv.load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE")

# Authenticate and get a token
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

# Get current user's playlists
playlists = sp.current_user_playlists()

# List playlists with their IDs
for playlist in playlists['items']:
    print(f"Name: {playlist['name']}, ID: {playlist['id']}")

# Paginate through all playlists
while playlists['next']:
    playlists = sp.next(playlists)
    for playlist in playlists['items']:
        print(f"Name: {playlist['name']}, ID: {playlist['id']}")

