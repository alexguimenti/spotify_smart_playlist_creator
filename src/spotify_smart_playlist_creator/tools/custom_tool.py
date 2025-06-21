import requests
from typing import Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os

class AddTracksToPlaylistInput(BaseModel):
    playlist_id: str = Field(..., description="The ID of the playlist where tracks will be added.")
    track_uris: List[str] = Field(..., description="A list of Spotify track URIs to add.")
    position: int = Field(0, description="Position in the playlist to insert the tracks.")

class AddTracksToPlaylistTool(BaseTool):
    name: str = "add_tracks_to_playlist"
    description: str = "Adds a list of track URIs to a Spotify playlist and returns the playlist ID and URL."
    args_schema: Type[BaseModel] = AddTracksToPlaylistInput

    def _run(self, playlist_id: str, track_uris: List[str], position: int = 0) -> str:
        # Token from environment or elsewhere
        token = os.getenv("SPOTIFY_ACCESS_TOKEN")
        api_key = os.getenv("SPOTIFY_API_KEY")  # If needed

        if not token:
            return "Missing Spotify access token."

        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["api-key"] = api_key

        payload = {
            "uris": track_uris,
            "position": position
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201 or response.status_code == 200:
            playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
            return f"Tracks added successfully. Playlist ID: {playlist_id}, URL: {playlist_url}"
        else:
            return f"Failed to add tracks: {response.status_code} - {response.text}"
