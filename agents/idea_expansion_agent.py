import google.generativeai as genai
from google.adk.agents import Agent

from state.story_state import StoryState
from utils.config import load_config
from utils.env import load_env
from utils.logger import get_logger
from typing import ClassVar
from pydantic import PrivateAttr

import json

# --- Configuration & Logging ---
load_env()
config = load_config()
genai.configure(api_key=config["api_keys"]["google_api_key"])
logger = get_logger(__name__)

# -- System Prompts ----
# This prompt guides the agent to act as a creative director

SYSTEM_PROMPT = """
You are "Cortex", a Creative Director AI for a short video production house.
Your job is to take a simple, one-line user idea and expand it into a
structured, cinematic concept.

You must output a JSON object with the following exact keys:
- "theme": The central theme or message.
- "genre": The video's genre (e.g., "Comedy", "Sci-Fi", "Documentary").
- "characters": A list of main characters, each with a brief description.
- "mood": The emotional tone (e.g., "Uplifting", "Suspenseful", "Humorous").
- "estimated_duration_sec": An estimated duration in seconds (e.g., 60).
- "cinematic_summary": A one-paragraph summary of the visual story.
"""


# ---Agent Definition -----
class IdeaExpansionAgent(Agent):
    """
    Agent 1 : Expands a one-line idea into a structured cinematic concept.
    """

    MAX_DURATION_SEC: ClassVar[int] = 30
    _llm: genai.GenerativeModel = PrivateAttr()

    name: str = "idea_expansion_agent"
    description: str = "Expands a simple idea into a full cinematic concept."

    def __init__(self):
        super().__init__()
        self._llm = genai.GenerativeModel(
            model_name=config["models"]["idea_expansion"],
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"},
        )

    def call(self, story_state: StoryState) -> StoryState:
        """
        Takes the user's idea and generates an expanded concept.
        """
        logger.info(f"Expanding idea: '{story_state.idea}'...")

        try:
            # Load preferences to guide the expansion
            prefs = story_state.preferences or {}
            user_prompt = f"""
            User Idea: "{story_state.idea}"

            Creator Preferences (use these to guide your choices):
            - Favorite Genres: {prefs.get('favorite_genres', 'Any')}
            - Favorite Styles: {prefs.get('preferred_styles', 'Any')}
            - Max Duration: {prefs.get('max_duration', '30s')}

            IMPORTANT: The 'estimated_duration_sec' MUST be
            less than or equal to {self.MAX_DURATION_SEC} seconds.
            This is a strict creative constraint for a very short video.
            """

            response = self._llm.generate_content(user_prompt)

            # Store the output in the state
            expanded_idea_json = response.text
            story_state.expanded_idea = json.loads(expanded_idea_json)

            # Record metadata
            story_state.metadata["idea_expansion_tokens"] = (
                response.usage_metadata.total_token_count
            )

        except Exception as e:
            logger.error(f"Error during idea expansion: {e}")
            # Handle error appropriately, maybe set a flag in the state
            story_state.metadata["error_idea_expansion"] = str(e)

        return story_state
