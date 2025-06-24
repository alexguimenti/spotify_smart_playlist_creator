"""
Custom Spotify tools for CrewAI agents
"""

import os
import json
import http.client
from typing import Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# -----------------------------------------------------------------------------
# Spotify Create Playlist Tool
# -----------------------------------------------------------------------------

class SpotifyCreatePlaylistInput(BaseModel):
    token: str = Field(..., description="Spotify access token of the user")
    user_id: str = Field(..., description="Spotify user ID")
    name: str = Field(..., description="Name of the playlist to create")
    description: str = Field(..., description="Description of the playlist")
    public: bool = Field(False, description="Whether the playlist should be public")

class SpotifyCreatePlaylistTool(BaseTool):
    """Tool to create a new Spotify playlist for a user."""
    name: str = "Spotify Create Playlist Tool"
    description: str = (
        "Creates a new playlist for the given user with a name, description, and visibility."
    )
    args_schema: Type[BaseModel] = SpotifyCreatePlaylistInput

    def _run(self, token: str, user_id: str, name: str, description: str, public: bool) -> str:
        conn = http.client.HTTPSConnection("api.spotify.com")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        body = json.dumps({
            "name": name,
            "description": description,
            "public": public
        })
        url = f"/v1/users/{user_id}/playlists"
        conn.request("POST", url, body, headers)
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))
        if res.status != 201:
            return f"❌ Failed to create playlist: {response}"
        return json.dumps({
            "playlist_id": response.get("id"),
            "playlist_url": response.get("external_urls", {}).get("spotify"),
            "name": response.get("name"),
            "description": response.get("description")
        }, indent=2)

# -----------------------------------------------------------------------------
# Spotify Search Tool
# -----------------------------------------------------------------------------

class SpotifySearchInput(BaseModel):
    token: str = Field(..., description="OAuth access token passed to the task as the 'token' input. Do NOT generate manually.")
    query: str = Field(..., description="Search query, e.g. 'artist:Radiohead track:Creep'")
    search_type: str = Field(..., description="Comma-separated list of item types (e.g. 'track,artist')")
    market: str = Field(default="US", description="Market country code (e.g. 'US')")
    limit: int = Field(default=5, description="Max number of results (1-50)")
    offset: int = Field(default=0, description="Index of the first result")

class SpotifySearchTool(BaseTool):
    """Tool to search Spotify's catalog for tracks, artists, albums, etc."""
    name: str = "Spotify Search Tool"
    description: str = (
        "Searches Spotify's catalog using a query string. You can search across tracks, artists, albums, playlists, etc."
    )
    args_schema: Type[BaseModel] = SpotifySearchInput

    def _run(self, token: str, query: str, search_type: str, market: str = "US", limit: int = 5, offset: int = 0) -> str:
        query_encoded = query.replace(" ", "%20")
        path = f"/v1/search?q={query_encoded}&type={search_type}&market={market}&limit={limit}&offset={offset}"
        curl_cmd = (
            f"curl --request GET \\\n"
            f"  --url 'https://api.spotify.com{path}' \\\n"
            f"  --header 'Authorization: Bearer {token}'"
        )
        print("\n🐚 cURL request:")
        print(curl_cmd)
        print("\n🎧 [SpotifySearchTool] Running with parameters:")
        print(f"  token: {token}...")  # only the first characters, for security
        print(f"  query: {query}")
        print(f"  search_type: {search_type}")
        print(f"  market: {market}")
        print(f"  limit: {limit}")
        print(f"  offset: {offset}")
        conn = http.client.HTTPSConnection("api.spotify.com")
        headers = {"Authorization": f"Bearer {token}"}
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))
        items = response.get("tracks", {}).get("items", [])
        if not items:
            return ""
        # Returns the public Spotify URL (not URI like `spotify:track:id`)
        return items[0]["external_urls"]["spotify"]

# -----------------------------------------------------------------------------
# Spotify Add Tracks To Playlist Tool
# -----------------------------------------------------------------------------

class SpotifyAddTracksInput(BaseModel):
    token: str = Field(..., description="Spotify OAuth access token of the user")
    playlist_id: str = Field(..., description="The Spotify ID of the playlist to add tracks to")
    uris: List[str] = Field(..., description="A list of Spotify track URIs to add (e.g. ['spotify:track:123', ...])")
    position: int = Field(default=0, description="Position in the playlist where tracks should be inserted (0 = beginning)")

class SpotifyAddTracksToPlaylistTool(BaseTool):
    """Tool to add tracks to a Spotify playlist."""
    name: str = "Spotify Add Tracks Tool"
    description: str = (
        "Adds a list of Spotify track URIs to a specific playlist, at the specified position (default is beginning)."
    )
    args_schema: Type[BaseModel] = SpotifyAddTracksInput

    def _run(self, token: str, playlist_id: str, uris: List[str], position: int = 0) -> str:
        conn = http.client.HTTPSConnection("api.spotify.com")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "uris": uris,
            "position": position
        })
        path = f"/v1/playlists/{playlist_id}/tracks"
        conn.request("POST", path, body=payload, headers=headers)
        res = conn.getresponse()
        data = res.read()
        try:
            response = json.loads(data.decode("utf-8"))
        except Exception:
            return f"❌ Could not parse Spotify response: {data}"
        if res.status != 201:
            return f"❌ Failed to add tracks: {response}"
        return json.dumps({
            "snapshot_id": response.get("snapshot_id", "unknown"),
            "status": "Tracks added successfully"
        }, indent=2)

# -----------------------------------------------------------------------------
# Spotify Get Current User Tool
# -----------------------------------------------------------------------------

class SpotifyGetCurrentUserInput(BaseModel):
    token: str = Field(..., description="Spotify OAuth access token with 'user-read-private' scope")

class SpotifyGetCurrentUserTool(BaseTool):
    """Tool to fetch the current authenticated user's Spotify profile."""
    name: str = "Spotify Get Current User Tool"
    description: str = (
        "Fetches the current authenticated user's Spotify profile using the /me endpoint. "
        "Returns the user ID, display name, and profile URL."
    )
    args_schema: Type[BaseModel] = SpotifyGetCurrentUserInput

    def _run(self, token: str) -> str:
        conn = http.client.HTTPSConnection("api.spotify.com")
        headers = {"Authorization": f"Bearer {token}"}
        conn.request("GET", "/v1/me", headers=headers)
        res = conn.getresponse()
        data = res.read()
        if res.status != 200:
            return f"❌ Failed to fetch user profile: HTTP {res.status} - {data.decode('utf-8')}"
        user_info = json.loads(data.decode("utf-8"))
        result = {
            "id": user_info.get("id"),
            "display_name": user_info.get("display_name"),
            "profile_url": user_info.get("external_urls", {}).get("spotify")
        }
        return json.dumps(result, indent=2)