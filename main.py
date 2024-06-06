import datetime
import json
import time

import click

from spotify_client import SpotifyClient
from youtube_client import YouTubeClient

@click.group()
def cli():
    """
    Tune2Tube \n
    From Spotify's Groove to YouTube's Show: Seamless Conversion! \n
    GitHub: https://github.com/yogeshwaran01/spotify-playlist-to-youtube-playlist
    """

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
@click.option(
    "--resume", is_flag=True, help="Resume adding songs to YouTube playlist from a saved JSON file"
)
def create(
    spotify_playlist_id: str,
    public: bool,
    private: bool,
    name: str,
    description: str,
    only_link: bool,
    save_to_sync: bool,
    resume: bool,
):
    """Create a YouTube Playlist from Spotify Playlist"""

    spotify = SpotifyClient()
    youtube = YouTubeClient()

    if resume:
        with open("remaining_songs.json", "r") as file:
            remaining_songs = json.load(file)
        spotify_playlist = Playlist(
            name=remaining_songs["name"],
            description=remaining_songs["description"],
            tracks=remaining_songs["tracks"]
        )
        youtube_playlist_id = remaining_songs["youtube_playlist_id"]
    else:
        spotify_playlist = spotify.get_playlist(spotify_playlist_id)

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

    # Search Song on YouTube
    remaining_tracks = []
    for track in spotify_playlist.tracks:
        if not only_link:
            click.secho(f"Searching for {track}", fg="blue")
        video = youtube.search_video(track)
        if not only_link:
            click.secho(f"Song found: {video.title}", fg="green")
        response = youtube.add_song_playlist(youtube_playlist_id, video.video_id)
        if response is None:
            remaining

