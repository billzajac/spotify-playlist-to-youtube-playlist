import os
import json
import time
import click
from spotify_client import SpotifyClient
from sync_manager import SyncManager
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

manager = SyncManager()

@click.group()
def cli():
    """
    Tune2Tube \n
    From Spotify's Groove to YouTube's Show: Seamless Conversion! \n
    GitHub: https://github.com/yogeshwaran01/spotify-playlist-to-youtube-playlist
    """

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

    def create_playlist(
        self, name: str, description: str, privacy_status: str = "private"
    ):
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

    def remove_song_playlist(self, playlist_id: str, video_id: str):
        request = self.youtube.playlistItems().delete(id=video_id)
        response = request.execute()
        return response

    def search_videos(self, queries):
        cached_results = self.load_cache()

        results = {}
        for query in queries:
            if query in cached_results:
                results[query] = cached_results[query]
            else:
                response = self.youtube.search().list(
                    q=query,
                    part="id",
                    maxResults=1,
                    type="video"
                ).execute()

                if response["items"]:
                    video_id = response["items"][0]["id"]["videoId"]
                    results[query] = video_id
                    cached_results[query] = video_id

                time.sleep(1)  # Add a delay between requests

        self.save_cache(cached_results)
        return results

    def load_cache(self):
        if os.path.exists("cache.json"):
            with open("cache.json", "r") as cache_file:
                return json.load(cache_file)
        return {}

    def save_cache(self, cache):
        with open("cache.json", "w") as cache_file:
            json.dump(cache, cache_file)

@click.command()
@click.argument("spotify_playlist_id")
@click.option("--public", is_flag=True, help="Create a public playlist")
@click.option("--private", is_flag=True, help="Create a public playlist")
@click.option("--name", "-n", help="Name of the YouTube playlist to be created")
@click.option("--description", "-d", help="Description of the playlist")
@click.option(
    "--only-link",
    "-l",
    default=False,
    help="just only link of playlist, logs not appear",
    is_flag=True,
)
@click.option(
    "--save-to-sync", "-s", is_flag=True, help="Save to list of playlist to sync"
)
def create(
    spotify_playlist_id: str,
    public: bool,
    private: bool,
    name: str,
    description: str,
    only_link: bool,
    save_to_sync: bool,
):
    """Create a YouTube Playlist from Spotify Playlist"""

    spotify = SpotifyClient()
    youtube = YouTubeClient()

    click.secho("Fetching saved tracks from Spotify...", fg="blue")
    spotify_playlist = spotify.get_playlist(spotify_playlist_id)
    click.secho("Fetched saved tracks from Spotify.", fg="blue")

    if public:
        privacy_status = "public"
    elif private:
        privacy_status = "private"
    else:
        privacy_status = "private"

    # Generate YouTube Playlist
    if name and description:
        youtube_playlist_id = youtube.create_playlist(
            name,
            description,
            privacy_status=privacy_status,
        )["id"]
    elif description:
        youtube_playlist_id = youtube.create_playlist(
            spotify_playlist.name,
            description,
            privacy_status=privacy_status,
        )["id"]
    elif name:
        youtube_playlist_id = youtube.create_playlist(
            name,
            spotify_playlist.description,
            privacy_status=privacy_status,
        )["id"]
    else:
        youtube_playlist_id = youtube.create_playlist(
            spotify_playlist.name,
            spotify_playlist.description,
            privacy_status=privacy_status,
        )["id"]

    # Collect all track names to search on YouTube
    queries = [f"{track['name']} by {track['artist']}" for track in spotify_playlist.tracks]

    # Search for videos on YouTube
    click.secho("Searching for videos on YouTube...", fg="blue")
    video_ids = youtube.search_videos(queries)
    click.secho("Search completed.", fg="blue")

    # Add songs to the playlist
    for query, video_id in video_ids.items():
        click.secho(f"Adding {query} to the YouTube playlist...", fg="blue")
        youtube.add_song_playlist(youtube_playlist_id, video_id)
        click.secho(f"Added {query}.", fg="green")

    if not only_link:
        click.secho(f"Playlist {privacy_status} playlist created", fg="blue")
        click.secho(
            f"Playlist found at https://www.youtube.com/playlist?list={youtube_playlist_id}", fg="blue"
        )
        click.secho(f"Playlist ID: {youtube_playlist_id}", fg="blue")
    else:
        click.secho(f"https://www.youtube.com/playlist?list={youtube_playlist_id}", fg="blue")

    if save_to_sync:
        manager.add_playlist(spotify_playlist_id, youtube_playlist_id, spotify_playlist.name, name, f"https://open.spotify.com/playlist/{spotify_playlist_id}", f"https://www.youtube.com/playlist?list={youtube_playlist_id}")
        manager.commit()


@click.command()
@click.option("-s", "--spotify_playlist_id", help="Spotify playlist ID")
@click.option("-y", "--youtube_playlist_id", help="YouTube playlist ID")
@click.option(
    "--only-link",
    "-l",
    default=False,
    help="just only link of playlist, logs not appear",
    is_flag=True,
)
def sync(
    spotify_playlist_id: str,
    youtube_playlist_id: str,
    only_link: bool,
):
    """Sync your YouTube playlist with Spotify Playlist"""

    playlists_to_be_synced = []

    if spotify_playlist_id is None and youtube_playlist_id is None:
        click.secho("Syncing Playlists ..", fg="blue")
        playlists_to_be_synced = manager.playlists_to_be_synced

    else:
        playlists_to_be_synced.append(
            {
                "spotify_playlist_id": spotify_playlist_id,
                "youtube_playlist_id": youtube_playlist_id,
            }
        )

    spotify = SpotifyClient()
    youtube = YouTubeClient()

    for playlist in playlists_to_be_synced:
        if not only_link:
            click.secho(
                f"Syncing YouTube: {playlist['youtube_playlist_id']} to Spotify: {playlist['spotify_playlist_id']}", fg="blue"
            )

        spotify_playlist = spotify.get_playlist(playlist["spotify_playlist_id"])

        searched_playlist = []
        for track in spotify_playlist.tracks:
            query = f"{track['name']} by {track['artist']}"
            if query in cached_results:
                searched_playlist.append(cached_results[query])
            else:
                response = youtube.search_videos([query])
                if response[query]:
                    searched_playlist.append(response[query])

        existing_video_ids = youtube.get_playlist_items(playlist["youtube_playlist_id"])

        songs_to_be_added = [video_id for video_id in searched_playlist if video_id not in existing_video_ids]
        songs_to_be_removed = [video_id for video_id in existing_video_ids if video_id not in searched_playlist]

        if not only_link:
            click.secho("Adding songs ...", fg="green")
        with click.progressbar(songs_to_be_added) as bar:
            for video_id in bar:
                try:
                    youtube.add_song_playlist(playlist["youtube_playlist_id"], video_id)
                    time.sleep(1)  # Add a delay to prevent hitting the quota too quickly
                except Exception as e:
                    click.secho(f"Error adding song: {e}", fg="red")
                    with open("remaining_songs.json", "w") as file:
                        json.dump({
                            "name": spotify_playlist.name,
                            "description": spotify_playlist.description,
                            "tracks": songs_to_be_added[bar.pos:],
                            "youtube_playlist_id": playlist["youtube_playlist_id"]
                        }, file, indent=4)
                    click.secho("Quota exceeded. Remaining songs saved to remaining_songs.json", fg="red")
                    return

        if not only_link:
            click.secho("Removing songs ...", fg="green")
        with click.progressbar(songs_to_be_removed) as bar:
            for video_id in bar:
                try:
                    youtube.remove_song_playlist(playlist["youtube_playlist_id"], video_id)
                    time.sleep(1)  # Add a delay to prevent hitting the quota too quickly
                except Exception as e:
                    click.secho(f"Error removing song: {e}", fg="red")

    if save_to_sync:
        manager.add_playlist(spotify_playlist_id, youtube_playlist_id, spotify_playlist.name, name, f"https://open.spotify.com/playlist/{spotify_playlist_id}", f"https://www.youtube.com/playlist?list={youtube_playlist_id}")
        manager.commit()

@cli.command()
@click.argument("spotify_playlist_id")
@click.option("--public", is_flag=True, help="Create a public playlist")
@click.option("--private", is_flag=True, help="Create a public playlist")
@click.option("--name", "-n", help="Name of the YouTube playlist to be created")
@click.option("--description", "-d", help="Description of the playlist")
@click.option(
    "--only-link",
    "-l",
    default=False,
    help="just only link of playlist, logs not appear",
    is_flag=True,
)
@click.option(
    "--save-to-sync", "-s", is_flag=True, help="Save to list of playlist to sync"
)
def create(
    spotify_playlist_id: str,
    public: bool,
    private: bool,
    name: str,
    description: str,
    only_link: bool,
    save_to_sync: bool,
):
    """Create a YouTube Playlist from Spotify Playlist"""

    spotify = SpotifyClient()
    youtube = YouTubeClient()

    click.secho("Fetching saved tracks from Spotify...", fg="blue")
    spotify_playlist = spotify.get_playlist(spotify_playlist_id)
    click.secho("Fetched saved tracks from Spotify.", fg="blue")

    if public:
        privacy_status = "public"
    elif private:
        privacy_status = "private"
    else:
        privacy_status = "private"

    # Generate YouTube Playlist
    if name and description:
        youtube_playlist_id = youtube.create_playlist(
            name,
            description,
            privacy_status=privacy_status,
        )["id"]
    elif description:
        youtube_playlist_id = youtube.create_playlist(
            spotify_playlist.name,
            description,
            privacy_status=privacy_status,
        )["id"]
    elif name:
        youtube_playlist_id = youtube.create_playlist(
            name,
            spotify_playlist.description,
            privacy_status=privacy_status,
        )["id"]
    else:
        youtube_playlist_id = youtube.create_playlist(
            spotify_playlist.name,
            spotify_playlist.description,
            privacy_status=privacy_status,
        )["id"]

    # Collect all track names to search on YouTube
    queries = [f"{track['name']} by {track['artist']}" for track in spotify_playlist.tracks]

    # Search for videos on YouTube
    click.secho("Searching for videos on YouTube...", fg="blue")
    video_ids = youtube.search_videos(queries)
    click.secho("Search completed.", fg="blue")

    # Add songs to the playlist
    for query, video_id in video_ids.items():
        click.secho(f"Adding {query} to the YouTube playlist...", fg="blue")
        youtube.add_song_playlist(youtube_playlist_id, video_id)
        click.secho(f"Added {query}.", fg="green")

    if not only_link:
        click.secho(f"Playlist {privacy_status} playlist created", fg="blue")
        click.secho(
            f"Playlist found at https://www.youtube.com/playlist?list={youtube_playlist_id}", fg="blue"
        )
        click.secho(f"Playlist ID: {youtube_playlist_id}", fg="blue")
    else:
        click.secho(f"https://www.youtube.com/playlist?list={youtube_playlist_id}", fg="blue")

    if save_to_sync:
        manager.add_playlist(spotify_playlist_id, youtube_playlist_id, spotify_playlist.name, name, f"https://open.spotify.com/playlist/{spotify_playlist_id}", f"https://www.youtube.com/playlist?list={youtube_playlist_id}")
        manager.commit()

if __name__ == "__main__":
    cli()

