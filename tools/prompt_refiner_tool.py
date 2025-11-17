import google.generativeai as genai
from google.adk.tools import FunctionTool
from utils.config import load_config
from utils.env import load_env
from utils.logger import get_logger
from typing import Optional

# --- Configuration & Logging ---
load_env()
config = load_config()
genai.configure(api_key=config["api_keys"]["google_api_key"])
logger = get_logger(__name__)

# --- System Prompts ---
# This is the "brain" of the refiner
SYSTEM_PROMPT = """
You are "Vivid", an expert prompt engineer for generative AI image models.
Your job is to take a simple scene description and expand it into a
rich, detailed, and cinematic prompt.

Focus on:
- **Visuals:** Colors, lighting, textures, camera angles, lens effects.
- **Mood:** The feeling (e.g., "moody," "joyful," "suspenseful").
- **Style:** A cinematic style (e.g., "film noir," "cinematic," "sci-fi").

**Output ONLY the final, single, expanded prompt string. Do not say anything else.**

Example Input: "Wide Shot. A man walks on a rainy street."
Example Output: "Cinematic wide shot, a man in a black trench coat walks down a lonely, rain-slicked street, neon-lit reflections in the puddles, moody atmosphere, film noir style, 8K, hyperrealistic."
"""


# --- Tool Definition ---
class PromptRefinerTool(FunctionTool):
    _llm: Optional[genai.GenerativeModel]

    def __init__(self):
        super().__init__(func=self.call)
        # We create a *new* LLM instance just for this tool
        try:
            self._llm = genai.GenerativeModel(
                model_name=config["models"].get("prompt_refiner", "gemini-1.5-flash"),
                system_instruction=SYSTEM_PROMPT,
            )
        except Exception as e:
            logger.error(f"Failed to initialize PromptRefiner LLM: {e}")
            self._llm = None

    def name(self):
        return "prompt_refiner"

    def description(self):
        return "Refines a simple scene description into a detailed, cinematic image prompt."

    def input_schema(self):
        return {
            "type": "object",
            "properties": {"scene_text": {"type": "string"}},
            "required": ["scene_text"],
        }

    def output_schema(self):
        return {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
        }

    def call(self, input):
        scene_text = input["scene_text"]

        if not self._llm:
            logger.warning("PromptRefiner LLM not available. Passing through text.")
            return {"prompt": scene_text}  # Fallback to dummy behavior

        try:
            logger.info(f"Refining prompt for: '{scene_text}'")
            # This is an LLM call *inside* your tool
            response = self._llm.generate_content(scene_text)

            refined_prompt = response.text.strip()

            logger.info(f"Refined prompt: '{refined_prompt}'")
            return {"prompt": refined_prompt}

        except Exception as e:
            logger.error(f"Error during prompt refinement: {e}")
            return {"prompt": scene_text}
