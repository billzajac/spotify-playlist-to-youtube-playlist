import os
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
@click.option("--private", is_flag=True, help="Create a private playlist")
@click.option("--name", "-n", help="Name of the YouTube playlist to be created")
@click.option("--description", "-d", help="Description of the playlist")
@click.option("--only-link", "-l", default=False, help="Just only link of playlist, logs not appear", is_flag=True)
@click.option("--save-to-sync", "-s", is_flag=True, help="Save to list of playlist to sync")
def create(spotify_playlist_id: str, public: bool, private: bool, name: str, description: str, only_link: bool, save_to_sync: bool):
    """Create a YouTube Playlist from Spotify Playlist"""

    spotify = SpotifyClient()
    youtube = YouTubeClient()

    click.secho("Fetching saved tracks from Spotify...", fg="blue")
    spotify_playlist = spotify.get_playlist(spotify_playlist_id)
    click.secho("Fetched saved tracks from Spotify.", fg="green")

    if public:
        privacy_status = "public"
    elif private:
        privacy_status = "private"
    else:
        privacy_status = "private"

    # Generate YouTube Playlist
    if name and description:
        youtube_playlist_id = youtube.create_playlist(name, description, privacy_status=privacy_status)["id"]
    elif description:
        youtube_playlist_id = youtube.create_playlist(spotify_playlist.name, description, privacy_status=privacy_status)["id"]
    elif name:
        youtube_playlist_id = youtube.create_playlist(name, spotify_playlist.description, privacy_status=privacy_status)["id"]
    else:
        youtube_playlist_id = youtube.create_playlist(spotify_playlist.name, spotify_playlist.description, privacy_status=privacy_status)["id"]

    # Collect all track names to search on YouTube
    queries = []
    for track in spotify_playlist.tracks:
        query = f"{track}"
        if len(query) < 8:
            click.secho(f"Skipping track: {query} (too short)", fg="yellow")
        else:
            queries.append(query)

    # Search and add songs to YouTube playlist one at a time
    click.secho("Adding songs to YouTube playlist...", fg="blue")
    for query in queries:
        try:
            click.secho(f"Searching for {query}", fg="blue")
            video_id = youtube.search_video(query)
            if video_id:
                click.secho(f"Song found: {query}", fg="green")
                youtube.add_song_playlist(youtube_playlist_id, video_id)
                click.secho("Song added", fg="green")
            else:
                click.secho(f"Could not find video for {query}", fg="red")
            time.sleep(1)  # Add delay to prevent hitting quota too quickly
        except Exception as e:
            if "quotaExceeded" in str(e):
                click.secho("Quota exceeded. Saving progress to resume later.", fg="red")
                save_progress(queries[queries.index(query):], youtube_playlist_id)
            else:
                click.secho(f"Error: {e}", fg="red")
            return

    if not only_link:
        click.secho(f"Playlist {privacy_status} playlist created", fg="blue")
        click.secho(f"Playlist found at https://www.youtube.com/playlist?list={youtube_playlist_id}", fg="blue")
        click.secho(f"Playlist ID: {youtube_playlist_id}", fg="blue")
    else:
        click.secho(f"https://www.youtube.com/playlist?list={youtube_playlist_id}", fg="blue")

    if save_to_sync:
        manager.add_playlist(spotify_playlist_id, youtube_playlist_id, spotify_playlist.name, name,
                             f"https://open.spotify.com/playlist/{spotify_playlist_id}",
                             f"https://www.youtube.com/playlist?list={youtube_playlist_id}")
        manager.commit()

def save_progress(queries, youtube_playlist_id):
    with open("remaining_songs.json", "w") as file:
        json.dump({"queries": queries, "youtube_playlist_id": youtube_playlist_id}, file)

@click.command()
def resume():
    """Resume adding songs to the YouTube playlist"""
    youtube = YouTubeClient()

    if not os.path.exists("remaining_songs.json"):
        click.secho("No remaining songs to add.", fg="red")
        return

    with open("remaining_songs.json", "r") as file:
        data = json.load(file)

    queries = data["queries"]
    youtube_playlist_id = data["youtube_playlist_id"]

    click.secho("Resuming adding songs to YouTube playlist...", fg="blue")
    for query in queries:
        try:
            video_id = youtube.search_video(query)
            if video_id:
                youtube.add_song_playlist(youtube_playlist_id, video_id)
                click.secho(f"Added {query} to YouTube playlist.", fg="green")
            else:
                click.secho(f"Could not find video for {query}", fg="red")
            time.sleep(1)  # Add delay to prevent hitting quota too quickly
        except Exception as e:
            if "quotaExceeded" in str(e):
                click.secho("Quota exceeded. Saving progress to resume later.", fg="red")
                save_progress(queries[queries.index(query):], youtube_playlist_id)
            else:
                click.secho(f"Error: {e}", fg="red")
            return

cli.add_command(create)
cli.add_command(resume)

if __name__ == "__main__":
    cli()

