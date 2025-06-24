"""
Crew definition for Spotify Smart Playlist Creator
"""

from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from spotify_smart_playlist_creator.tools.custom_tool import (
    SpotifySearchTool,
    SpotifyAddTracksToPlaylistTool,
    SpotifyCreatePlaylistTool,
    SpotifyGetCurrentUserTool
)

# -----------------------------------------------------------------------------
# Crew Definition
# -----------------------------------------------------------------------------

search_tool = SerperDevTool()

@CrewBase
class SpotifySmartPlaylistCreator:
    """
    Crew class for orchestrating Spotify playlist creation using multiple agents and tasks.
    """
    agents: List[BaseAgent]
    tasks: List[Task]

    # ----------------------
    # Agent Definitions
    # ----------------------
    @agent
    def music_researcher(self) -> Agent:
        """Agent responsible for music research."""
        return Agent(
            config=self.agents_config['music_researcher'], # type: ignore[index]
            verbose=True,
            human_input=True,
            tools=[search_tool]
        )

    @agent
    def spotify_uri_fetcher(self) -> Agent:
        """Agent responsible for fetching Spotify URIs."""
        return Agent(
            config=self.agents_config['spotify_uri_fetcher'], # type: ignore[index]
            verbose=True,
            human_input=True,
            tools=[SpotifySearchTool()]
        )

    @agent
    def spotify_playlist_creator(self) -> Agent:
        """Agent responsible for creating and populating Spotify playlists."""
        return Agent(
            config=self.agents_config['spotify_playlist_creator'], # type: ignore[index]
            verbose=True,
            human_input=True,
            tools=[
                SpotifyCreatePlaylistTool(),
                SpotifyAddTracksToPlaylistTool(),
                SpotifyGetCurrentUserTool()
            ]
        )

    # ----------------------
    # Task Definitions
    # ----------------------
    @task
    def generate_music_list_task(self) -> Task:
        """Task to generate a list of music based on user prompt."""
        return Task(
            config=self.tasks_config['generate_music_list_task'], # type: ignore[index]
        )

    @task
    def fetch_spotify_uris_task(self) -> Task:
        """Task to fetch Spotify URIs for the generated music list."""
        return Task(
            config=self.tasks_config['fetch_spotify_uris_task'], # type: ignore[index]
        )

    @task
    def create_and_populate_playlist_task(self) -> Task:
        """Task to create and populate a Spotify playlist with the selected tracks."""
        return Task(
            config=self.tasks_config['create_and_populate_playlist_task'], # type: ignore[index]
        )

    # ----------------------
    # Crew Assembly
    # ----------------------
    @crew
    def crew(self) -> Crew:
        """Creates and returns the SpotifySmartPlaylistCreator crew."""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks,   # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # Uncomment to use hierarchical process
        )
