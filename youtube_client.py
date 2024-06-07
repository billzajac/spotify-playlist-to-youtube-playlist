import os
import json
import time
import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class YouTubeClient:
    def __init__(self):
        self.creds = None
        if os.path.exists('credentials.json'):
            self.load_credentials()
        else:
            self.authenticate_and_build()

    def authenticate_and_build(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
        )
        self.creds = flow.run_local_server(port=0)

        self.save_credentials()
        self.youtube = build("youtube", "v3", credentials=self.creds)

    def save_credentials(self):
        with open('credentials.json', 'w') as credentials_file:
            credentials_file.write(self.creds.to_json())

    def load_credentials(self):
        with open('credentials.json', 'r') as credentials_file:
            credentials_data = json.load(credentials_file)
            if isinstance(credentials_data, str):
                credentials_data = json.loads(credentials_data)
            self.creds = Credentials.from_authorized_user_info(credentials_data)
        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
        self.youtube = build("youtube", "v3", credentials=self.creds)

    def create_playlist(self, name: str, description: str, privacy_status: str = "private"):
        playlist = self.youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": name,
                    "description": description,
                    "defaultLanguage": "en",
                },
                "status": {"privacyStatus": privacy_status},
            },
        ).execute()
        return playlist

    def add_song_playlist(self, playlist_id: str, video_id: str):
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            playlist_item = request.execute()
            return playlist_item
        except Exception as e:
            logging.warning(f"Encountered error adding song to playlist: {e}")
            return None

    def remove_song_playlist(self, playlist_item_id: str):
        request = self.youtube.playlistItems().delete(id=playlist_item_id)
        response = request.execute()
        return response

    def search_video(self, query: str):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.youtube.com/results?search_query={query}"
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            time.sleep(1)  # Add a delay between requests
            for video in soup.find_all('a', href=True):
                if '/watch?v=' in video['href']:
                    video_id = video['href'].split('/watch?v=')[1]
                    return video_id
            logging.warning(f"No video found for query: {query}")
            return None
        except Exception as e:
            logging.warning(f"Encountered error searching for video: {e}")
            return None

    def get_playlist_items(self, playlist_id):
        videos = []
        next_page_token = None

        while True:
            request = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )

            response = request.execute()

            videos.extend([item['snippet']['resourceId']['videoId'] for item in response['items']])
            next_page_token = response.get("nextPageToken")

            if not next_page_token:
                break

        return videos

