import google.generativeai as genai
import json
from google.adk.agents import Agent

from state.story_state import StoryState
from utils.config import load_config
from utils.env import load_env
from utils.logger import get_logger

from pydantic import PrivateAttr

# --- Configuration & Logging ---
load_env()
config = load_config()
genai.configure(api_key=config["api_keys"]["google_api_key"])
logger = get_logger(__name__)

# ---System Prompts ---
# This prompt guides the agent to act as a professionals screenwriter
SYSTEM_PROMPT = """
You are "Scribe", a professional screenwriter AI. Your task is to write a
complete, engaging short video script based on a given cinematic concept.

The video duration should be close to the "estimated_duration_sec" from the concept.

You MUST output a JSON object with the following exact keys:
- "title": A catchy title for the video.
- "logline": A one-sentence summary of the script.
- "scenes": A list of scene objects.
- "total_duration_sec": The final calculated duration of this script.

Each "scene" object in the "scenes" list MUST have these keys:
- "scene_number": The number of the scene (e.g., 1, 2, 3).
- "location": A brief description of the location (e.g., "INT. COFFEE SHOP - DAY").
- "action": A description of the visual action and what is happening.
- "dialogue": A list of dialogue objects, or an empty list [].
- "voiceover": A string for any voiceover.

Each "dialogdialogue" object MUST have these keys:
- "character": The name of the character speaking.
- "line": The words the character says.
"""


# --Agent Definition ----
class ScriptWriterAgent(Agent):
    """
    Agent 2: Writes a full script based on the expanded idea.
    """

    name: str = "script_writer_agent"
    description: str = "Writes a short video script from a cinematic concept."

    _llm: genai.GenerativeModel = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._llm = genai.GenerativeModel(
            model_name=config["models"]["script_writer"],
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"},
        )

    def call(self, story_state: StoryState) -> StoryState:
        if not story_state.expanded_idea:
            logger.warning("No expanded idea found. Skipping script writing.")
            story_state.metadata["error_script_writer"] = "Missing expanded_idea"
            return story_state

        logger.info("Writing script...")

        try:
            # We MUST define concept_json FIRST
            concept_json = json.dumps(story_state.expanded_idea, indent=2)

            # THEN we can USE it to build the user_prompt
            user_prompt = f"""
            Write a complete script based on the following cinematic concept:

            {concept_json}
            """

            response = self._llm.generate_content(user_prompt)

            script_json = response.text
            story_state.script = json.loads(script_json)

            logger.info(
                f"Script writing complete. Title: '{story_state.script.get('title')}'"
            )

            story_state.metadata["script_writer_tokens"] = (
                response.usage_metadata.total_token_count
            )

        except Exception as e:
            logger.error(f"Error during script writing: {e}")
            story_state.metadata["error_script_writer"] = str(e)

        return story_state
