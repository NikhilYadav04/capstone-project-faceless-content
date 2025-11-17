import google.generativeai as genai
import json
from google.adk.agents import Agent

from state.story_state import StoryState
from utils.config import load_config
from utils.env import load_env
from utils.logger import get_logger

from typing import ClassVar
from pydantic import PrivateAttr

# --- Configuration & Logging ---
load_env()
config = load_config()
genai.configure(api_key=config["api_keys"]["google_api_key"])
logger = get_logger(__name__)

# --- System Prompts ---
SYSTEM_PROMPT = """
You are "Shot-Caller", a Director of Photography AI. Your job is to take a
final script and break it down into a shot-by-shot list for the storyboard
artist.

For each scene in the script, you may need to create *multiple* shots (e.g.,
an establishing wide shot, then a medium shot, then a close-up).

You MUST output a JSON object with a single key: "scenes".
The value of "scenes" must be a list of scene/shot objects.

Each object in the "scenes" list MUST have these exact keys:
- "scene_id": A unique ID for this shot (e.g., 1, 2, 3).
- "shot_description": A brief, *purely visual* description of what is on screen.
- "camera_angle": The camera shot type (e.g., "Wide Shot", "Medium Shot", "Close-up", "Point of View").
- "location": The location from the script.
- "key_action": The single most important action happening in this shot.
"""


# --- Agent Definition ---
class SceneBreakdownAgent(Agent):
    """
    Agent 3 : Breaks the script into a list of specific visual shots.
    """

    MAX_SCENES: ClassVar[int] = 10
    name: str = "scene_breakdown_agent"
    description: str = "Breaks a script down into a visual shot list."
    _llm: genai.GenerativeModel = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._llm = genai.GenerativeModel(
            model_name=config["models"]["scene_breakdown"],
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"},
        )

    def call(self, story_state: StoryState) -> StoryState:
        """
        Takes the script and generates a list of visual shots.
        """

      
        if not story_state.script:
            logger.warning("No script found. Skipping scene breakdown.")
            story_state.metadata["error_scene_breakdown"] = "Missing script"
            return story_state

        logger.info("Breaking down script into visual shots...")

        try:
            # Prepare the prompt, sending the full script
            script_json = json.dumps(story_state.script, indent=2)
            user_prompt = f"""
            Break down the following script into a visual shot list:

            IMPORTANT: Do not generate more than {self.MAX_SCENES} total shots,
            even if the script is long. Focus on the most important
            key moments.

            Script:
            {script_json}
            """

           
            response = self._llm.generate_content(user_prompt)

            # The response will be {"scenes": [...]}
            # We extract the list and save it.
            response_data = json.loads(response.text)
            story_state.scenes = response_data.get("scenes", [])

            logger.info(
                f"Script breakdown complete. Generated {len(story_state.scenes)} shots."
            )

            # Record metadata
            story_state.metadata["scene_breakdown_tokens"] = (
                response.usage_metadata.total_token_count
            )

        except Exception as e:
            logger.error(f"Error during scene breakdown: {e}")
            story_state.metadata["error_scene_breakdown"] = str(e)

        return story_state
