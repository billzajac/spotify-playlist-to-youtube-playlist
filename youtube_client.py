import os
import json
import time
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests
import click

class YouTubeClient:
    def __init__(self):
        if os.path.exists("credentials.json"):
            self.load_credentials()
        else:
            self.authenticate_and_build()

    def authenticate_and_build(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
        )

        creds = flow.run_local_server()

        self.save_credentials(creds)
        self.youtube = build("youtube", "v3", credentials=creds)

    def save_credentials(self, creds):
        credentials_data = creds.to_json()
        with open("credentials.json", "w") as credentials_file:
            json.dump(credentials_data, credentials_file)

    def load_credentials(self):
        with open("credentials.json", "r") as credentials_file:
            credentials_data = json.load(credentials_file)
            creds = Credentials.from_authorized_user_info(json.loads(credentials_data))
            self.youtube = build("youtube", "v3", credentials=creds)

    def create_playlist(self, name: str, description: str, privacy_status: str = "private"):
        playlist = (
            self.youtube.playlists()
            .insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": name,
                        "description": description,
                        "defaultLanguage": "en",
                    },
                    "status": {"privacyStatus": privacy_status},
                },
            )
            .execute()
        )
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
            return None

    def remove_song_playlist(self, playlist_item_id: str):
        request = self.youtube.playlistItems().delete(id=playlist_item_id)
        response = request.execute()
        return response

    def search_video(self, query: str):
        search_url = f"https://www.youtube.com/results?search_query={query}"
        response = requests.get(search_url)

        if response.status_code == 200:
            html_content = response.text
            start_index = html_content.find("/watch?v=")
            if start_index != -1:
                end_index = html_content.find("\"", start_index)
                video_id = html_content[start_index + 9:end_index]
                logging.info(f"Using URL https://www.youtube.com/watch?v={video_id}")
                return video_id
            else:
                logging.warning(f"No video found for query: {query}")
                return None
        else:
            logging.warning(f"Error fetching search results for query: {query}")
            return None

    def get_playlist(self, playlist_id):
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

            videos.extend(response["items"])
            next_page_token = response.get("nextPageToken")

            if not next_page_token:
                break

        return videos

