"""
Spotify Smart Playlist Creator Crew
"""

from crewai import Crew, Agent, Task
from spotify_smart_playlist_creator.tools.custom_tool import (
    SpotifyCreatePlaylistTool,
    SpotifySearchTool,
    SpotifyAddTracksToPlaylistTool,
    SpotifyGetCurrentUserTool
)

class SpotifySmartPlaylistCreator:
    """Crew for creating Spotify playlists based on user prompts."""
    
    def __init__(self):
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()
    
    def _create_agents(self):
        """Create the agents for the crew."""
        
        # Music Curator Agent
        music_curator = Agent(
            role="AI Music Curator specialized in thematic playlist generation",
            goal="Curate a list of songs that matches the user's prompt in mood, genre, era, and optionally length or song count",
            backstory="""You're a skilled music curator with deep knowledge of global music genres, decades, and cultural moods.
            You understand natural language prompts and can translate them into well-balanced playlists that capture the user's intent,
            whether they ask for a specific vibe, decade, theme, or playlist duration.
            Your suggestions are precise, era-appropriate, and creatively curated to fit the desired context.""",
            verbose=True,
            allow_delegation=False,
            human_input=False
        )
        
        # Spotify URI Fetcher Agent
        uri_fetcher = Agent(
            role="Spotify Metadata Integration Agent",
            goal="Search for and retrieve accurate Spotify URIs for a list of songs using Spotify's public API",
            backstory="""You are an expert in music metadata lookup and Spotify API integration.
            Your job is to take structured song information—typically a title and artist name—and search Spotify's catalog to retrieve accurate track URIs.
            You are precise, efficient, and reliable, and you handle missing or ambiguous matches gracefully.""",
            tools=[SpotifySearchTool()],
            verbose=True,
            allow_delegation=False,
            human_input=False
        )
        
        # Playlist Creator Agent
        playlist_creator = Agent(
            role="Spotify Playlist Automation Agent",
            goal="Create a new playlist for the user and add the specified songs using Spotify's Web API",
            backstory="""You are an expert in automating playlist creation on Spotify using their public API.
            You understand how to create playlists with user-defined names and descriptions, and how to add specific tracks to them based on their URIs.
            You ensure the playlist is successfully created and populated with the requested songs, and return a sharable playlist link.""",
            tools=[SpotifyGetCurrentUserTool(), SpotifyCreatePlaylistTool(), SpotifyAddTracksToPlaylistTool()],
            verbose=True,
            allow_delegation=False,
            human_input=False
        )
        
        return {
            'music_curator': music_curator,
            'uri_fetcher': uri_fetcher,
            'playlist_creator': playlist_creator
        }
    
    def _create_tasks(self):
        """Create the tasks for the crew."""
        
        # Task 1: Generate music list
        generate_music_list = Task(
            description="""Interpret the user's prompt describing the type of playlist they want to create.
            The prompt may include genre, era, occasion, mood, and optionally the desired number of songs or total duration of the playlist (in minutes).
            Based on this input, generate a list of songs that match the theme and approximate the requested length or song count.
            User Prompt is: {user_prompt}""",
            expected_output="""A list of songs formatted as:
            - "Song Title" by Artist Name

            The list should include approximately the number of songs or total duration specified by the user.
            If the user does not specify either, generate a default playlist of 10 songs.""",
            agent=self.agents['music_curator']
        )
        
        # Task 2: Fetch Spotify URIs
        fetch_uris = Task(
            description="""Receive a list of songs with their respective artist names and use the Spotify Web API to search for each one.
            Retrieve the Spotify URL for each track, ensuring the match is as accurate as possible based on title and artist.
            This task relies on an external Tool that queries the Spotify API directly.
            Handle edge cases where a song may not be found by skipping or logging it for review.
            Use the Spotify Web API to search for tracks. The token is already available as the `token` input. Do not generate or hardcode it.""",
            expected_output="""Use the Spotify Web API to search for tracks. The token is already available as the `token` input {token}. Do not generate or hardcode it.
            A single comma-separated string (without spaces) containing only the valid Spotify url (example: uris=spotify:track:4iV5W9uYEdYUVa79Axb7Rh,spotify:track:1301WleyT98MSxVHPZCA6M,spotify:episode:512ojhOuo1ktJprKbVcKyQ).
            If a track cannot be found, omit it from the output.""",
            agent=self.agents['uri_fetcher']
        )
        
        # Task 3: Create and populate playlist
        create_playlist = Task(
            description="""Using the provided Spotify access token, user ID, list of track URIs, playlist name and description,
            create a new playlist in the user's Spotify account and add the songs to it.
            This task uses the Spotify Web API and assumes valid authentication via OAuth.
            Do not attempt to generate or refresh the token manually.
            Use the Spotify Web API to search for tracks. The token is already available as the `token` input {token}. Do not generate or hardcode it.""",
            expected_output="""A JSON object containing the playlist URL and name. For example:
            {
              "playlist_url": "https://open.spotify.com/playlist/7wDH1tHMWUcdq5yMb5vVeK",
              "name": "My Playlist from Crew"
            }""",
            agent=self.agents['playlist_creator']
        )
        
        return {
            'generate_music_list': generate_music_list,
            'fetch_uris': fetch_uris,
            'create_playlist': create_playlist
        }
    
    def crew(self):
        """Create and return the crew."""
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            verbose=True
        ) 