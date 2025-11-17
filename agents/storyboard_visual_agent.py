import google.generativeai as genai
from google.adk.agents import Agent
from pydantic import PrivateAttr
import json
from concurrent.futures import ThreadPoolExecutor

from state.story_state import StoryState
from utils.config import load_config
from utils.env import load_env
from utils.logger import get_logger
from tools.image_generation_tool import ImageGenerationTool
from tools.prompt_refiner_tool import PromptRefinerTool

# --- Configuration & Logging ---
load_env()
config = load_config()
genai.configure(api_key=config["api_keys"]["google_api_key"])
logger = get_logger(__name__)

# --- Agent 1: The Worker (Processes one scene) ---


class SingleSceneVisualAgent(Agent):
    """
    Worker Agent: Processes a single scene to generate a prompt and an image.
    Input: A scene dictionary.
    Output: A dictionary with the scene_id, prompt, and image_path.
    """

    name: str = "single_scene_visual_agent"
    description: str = "Generates a prompt and image for one scene."
    _refiner_tool: PromptRefinerTool = PrivateAttr()
    _image_tool: ImageGenerationTool = PrivateAttr()

    def __init__(
        self, refiner_tool: PromptRefinerTool, image_tool: ImageGenerationTool
    ):
        super().__init__()
        self._refiner_tool = refiner_tool
        self._image_tool = image_tool

    def call(self, scene: dict) -> dict:
        """
        Processes one scene.
        """
        scene_id = scene.get("scene_id", "unknown")
        logger.info(f"Generating visuals for scene {scene_id}...")

        try:
            scene_text = (
                f"Shot: {scene.get('camera_angle', '')}. "
                f"Location: {scene.get('location', '')}. "
                f"Action: {scene.get('key_action', '')}. "
                f"Description: {scene.get('shot_description', '')}"
            )

            refiner_input = {"scene_text": scene_text}
            refiner_output = self._refiner_tool.call(refiner_input)
            final_prompt = refiner_output["prompt"]

            image_input = {"prompt": final_prompt, "scene_id": scene_id}
            image_output = self._image_tool.call(image_input)
            image_path = image_output["image_path"]

            logger.info(f"Visuals complete for scene {scene_id}.")

            return {
                "scene_id": scene_id,
                "prompt": final_prompt,
                "image_path": image_path,
            }

        except Exception as e:
            logger.error(f"Error processing scene {scene_id}: {e}")
            return {"scene_id": scene_id, "prompt": "Error", "image_path": "Error"}


# --- Agent 2: The Orchestrator (Manages parallel workers) ---


class StoryboardVisualAgent(Agent):
    """
    Agent 4: Manages the parallel generation of all storyboard visuals.
    """

    name: str = "storyboard_visual_agent"
    description: str = "Generates storyboard prompts and images in parallel."

    _worker_agent: SingleSceneVisualAgent = PrivateAttr()

    def __init__(self):
        super().__init__()
        refiner_tool = PromptRefinerTool()
        image_tool = ImageGenerationTool()
        self._worker_agent = SingleSceneVisualAgent(refiner_tool, image_tool)

    def call(self, story_state: StoryState) -> StoryState:
        """
        Takes the list of scenes and generates visuals for all of them in parallel.
        """
        if not story_state.scenes:
            logger.warning("No scenes found. Skipping storyboard generation.")
            story_state.metadata["error_storyboard"] = "Missing scenes"
            return story_state

        logger.info(
            f"Starting parallel visual generation for {len(story_state.scenes)} scenes..."
        )

        try:
            # --- THIS IS THE REAL, WORKING FIX ---
            # We use Python's built-in ThreadPoolExecutor
            # to run our worker agent's .call() method
            # on every scene in the list.

            visual_outputs = []
            with ThreadPoolExecutor() as executor:
                # The .map() function here is from the ThreadPoolExecutor
                # It runs the worker's call method on each scene
                results = executor.map(self._worker_agent.call, story_state.scenes)
                visual_outputs = list(results)

            # --- End of Fix ---

            story_state.storyboard_prompts = []
            story_state.storyboard_images = []

            for output in visual_outputs:
                if output["image_path"] != "Error":
                    story_state.storyboard_prompts.append(
                        {"scene_id": output["scene_id"], "prompt": output["prompt"]}
                    )
                    story_state.storyboard_images.append(output["image_path"])

            logger.info(
                f"Parallel visual generation complete. {len(story_state.storyboard_images)} images created."
            )

        except Exception as e:
            logger.error(f"Error during parallel storyboard generation: {e}")
            story_state.metadata["error_storyboard"] = str(e)

        return story_state
