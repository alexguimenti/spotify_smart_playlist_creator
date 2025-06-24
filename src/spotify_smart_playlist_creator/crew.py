from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from spotify_smart_playlist_creator.tools.custom_tool import SpotifySearchTool, SpotifyAddTracksToPlaylistTool, SpotifyCreatePlaylistTool, SpotifyGetCurrentUserTool

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
search_tool = SerperDevTool()


@CrewBase
class SpotifySmartPlaylistCreator():
    """SpotifySmartPlaylistCreator crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def music_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['music_researcher'], # type: ignore[index]
            verbose=True,
            human_input = True,
            tools=[search_tool]
        )
    
    @agent
    def spotify_uri_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config['spotify_uri_fetcher'], # type: ignore[index]
            verbose=True,
            human_input = True,
            tools=[SpotifySearchTool()]
        )
    
    @agent
    def spotify_playlist_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['spotify_playlist_creator'], # type: ignore[index]
            verbose=True,
            human_input = True,
            tools=[
                SpotifyCreatePlaylistTool(),
                SpotifyAddTracksToPlaylistTool(),
                SpotifyGetCurrentUserTool()
                ]
        )
    
    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def generate_music_list_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_music_list_task'], # type: ignore[index]
        )
    
    @task
    def fetch_spotify_uris_task(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_spotify_uris_task'], # type: ignore[index]
        )
    
    @task
    def create_and_populate_playlist_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_and_populate_playlist_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SpotifySmartPlaylistCreator crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
