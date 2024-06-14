import os
import json
import time
import logging
import click
from spotify_client import SpotifyClient
from sync_manager import SyncManager
from youtube_client import YouTubeClient

manager = SyncManager()

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
    privacy_status = "private"

    if os.path.exists("saved_tracks.json"):
        click.secho("Loading saved tracks from saved_tracks.json...", fg="blue")
        with open("saved_tracks.json", "r") as file:
            saved_tracks = json.load(file)
        click.secho("Loaded saved tracks from saved_tracks.json.", fg="blue")

        # Search for existing YouTube playlist named "Spotify Liked Songs"
        click.secho('Searching for "Spotify Liked Songs" playlist on YouTube...', fg="blue")
        playlist = youtube.find_playlist_by_name("Spotify Liked Songs")

        if playlist:
            click.secho('Found "Spotify Liked Songs" playlist on YouTube.', fg="blue")
            youtube_playlist_id = playlist["id"]
        else:
            click.secho('Creating new "Spotify Liked Songs" playlist on YouTube...', fg="blue")
            youtube_playlist_id = youtube.create_playlist(
                "Spotify Liked Songs",
                "Spotify Liked Songs playlist",
                privacy_status="private",
            )["id"]
    else:
        click.secho("Fetching saved tracks from Spotify...", fg="blue")
        spotify_playlist = spotify.get_playlist(spotify_playlist_id)
        click.secho("Fetched saved tracks from Spotify.", fg="blue")

        if public:
            privacy_status = "public"
        elif private:
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
    if os.path.exists("saved_tracks.json"):
        queries = saved_tracks["tracks"]
    else:
        queries = [f"{track['name']} by {track['artist']}" for track in spotify_playlist.tracks]

    # Add songs to the playlist
    click.secho("Adding songs to YouTube playlist...", fg="blue")
    # Youtube limits only allow me to add 199 songs per day
    for query in queries[:199]:
        click.secho(f"Searching for {query}", fg="blue")
        video_id = youtube.search_video(query)
        if video_id:
            click.secho(f"Song found: {query}", fg="green")
            youtube.add_song_playlist(youtube_playlist_id, video_id)
            click.secho("Song added", fg="green")
        else:
            click.secho(f"Could not find video for {query}", fg="red")
        time.sleep(1)  # Add delay to avoid hitting quota too quickly

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

    # Finally, update the saved_tracks.json
    # Check if there are at least 199 tracks
    if os.path.exists("saved_tracks.json"):
        if len(saved_tracks['tracks']) >= 199:
            # Remove the first 199 tracks
            saved_tracks['tracks'] = saved_tracks['tracks'][199:]
        else:
            click.secho("There are fewer than 199 tracks in the file.", fg="red")

        # Save the updated list back to the file
        with open("saved_tracks.json", "w") as file:
            json.dump(saved_tracks, file, indent=4)

        click.secho("Updated saved_tracks.json with the remaining tracks.", fg="green")

cli.add_command(create)

if __name__ == "__main__":
    cli()

