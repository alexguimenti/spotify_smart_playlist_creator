# SpotifySmartPlaylistCreator Crew

Welcome to the **SpotifySmartPlaylistCreator** project, powered by [crewAI](https://crewai.com). This AI system leverages Spotify's Web API and intelligent agents to generate personalized music playlists based on natural language prompts. Whether you're in the mood for "punk pop from the 2000s" or "chill jazz for a rainy day," this app will understand and deliver.

---

## 🎧 What It Does

This multi-agent system takes a user-provided prompt (e.g. mood, genre, decade, or context) and:

1. **Generates a list of songs** matching the theme.
2. **Searches Spotify's API** to retrieve accurate URIs for each song.
3. **Creates a new playlist** in the user's Spotify account.
4. **Adds the selected tracks** into the newly created playlist.

The user authenticates with Spotify using OAuth2, and all playlist operations happen under their account.

---

## ⚡ Features

- Natural language playlist generation
- Spotify OAuth integration
- Accurate song matching via Spotify Search API
- Automatic playlist creation and track population
- CrewAI-powered multi-agent collaboration

---

## 🧵 Installation

Make sure you have Python >=3.10 <3.13 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency and environment management.

Install UV (if not yet installed):
```bash
pip install uv
```

Clone the repository and install dependencies:
```bash
cd spotify_smart_playlist_creator
crewai install  # Optional: will install and lock dependencies
```

---

## ⚙️ Customization

Set your OpenAI key in `.env`:
```
OPENAI_API_KEY=your-key-here
```

To define or modify your AI logic:
- `src/spotify_smart_playlist_creator/config/agents.yaml`: configure agents (e.g. playlist creator, URI fetcher)
- `src/spotify_smart_playlist_creator/config/tasks.yaml`: define multi-step workflows
- `src/spotify_smart_playlist_creator/crew.py`: orchestrate your crew
- `src/spotify_smart_playlist_creator/main.py`: run with custom inputs

---

## 🚀 Running the Project

Launch the full pipeline from the root folder:
```bash
crewai run
```

This will:
- Load all agents and tasks
- Execute the end-to-end process of generating and populating a Spotify playlist based on user input

---

## 🧑‍💼 Understanding the Crew

This project uses multiple AI agents:

- **Music Curator**: Interprets prompts and curates matching songs
- **Spotify Metadata Integration Agent**: Searches Spotify for accurate track URIs
- **Playlist Automation Agent**: Creates the playlist and uploads the tracks

These agents are defined in `config/agents.yaml` and work together through tasks in `config/tasks.yaml`, using custom tools that wrap Spotify's Web API.

---

## 🚫 Notable Limitations

- You must authorize with a real Spotify account
- Only supports public/private playlist creation (no collaborative playlists)
- Spotify token expires after a period; not yet auto-refreshed

---

## 🚑 Support

For help with the project or crewAI:
- 📖 [Documentation](https://docs.crewai.com)
- 👤 [GitHub Repository](https://github.com/joaomdmoura/crewai)
- 🤝 [Join Discord](https://discord.com/invite/X4JWnZnxPb)
- 🧠 [Chat with the Docs](https://chatg.pt/DWjSBZn)

---

Let's build smarter, more musical AI together with the power of **crewAI** 🎵

