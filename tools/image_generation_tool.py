import requests
import os
from google.adk.tools import FunctionTool

from utils.env import load_env
from utils.logger import get_logger

from typing import Optional
from pydantic import PrivateAttr


# --- Config & Logging ---
logger = get_logger(__name__)
env = load_env()


class ImageGenerationTool(FunctionTool):

    _api_key: Optional[str] = PrivateAttr()
    _api_url: str = PrivateAttr()

    def __init__(self):
        super().__init__(func=self.call)
        self._api_key = env.get("STABLECOG_API_KEY")
        self._api_url = "https://api.stablecog.com/v1/image/generation/create"
        if not self._api_key:
            logger.error("STABLECOG_API_KEY not found. Image generation will fail.")

    def name(self):
        return "image_generation"

    def description(self):
        return "Generate an image from a prompt and save it locally."

    def call(self, input):
        if not self._api_key:
            return {"image_path": "ERROR_API_KEY_MISSING"}

        prompt = input["prompt"]
        scene_id = input["scene_id"]

        # Define the local save path (the pipeline expects this)
        # The API response URL ends in .jpeg, so we use that
        local_image_path = f"outputs/images/scene_{scene_id}.jpeg"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "prompt": prompt,
            "num_outputs": 1,
            "width": 1024,
            "height": 1024,
        }

        logger.info(f"Calling Stablecog API for scene {scene_id}...")

        try:
            # 1. Make the API call to generate the image
            response = requests.post(self._api_url, headers=headers, json=body)
            response.raise_for_status()  # Raise an error for bad responses

            data = response.json()
            image_url = data["outputs"][0]["url"]

            logger.info(f"API success. Downloading image from: {image_url}")

            # 2. Download the image from the returned URL
            image_data = requests.get(image_url).content

            # 3. Save the image to the local path
            with open(local_image_path, "wb") as f:
                f.write(image_data)

            logger.info(f"Image saved locally to: {local_image_path}")

            # 4. Return the local path, as expected by the pipeline
            return {"image_path": local_image_path}

        except Exception as e:
            logger.error(f"Image generation failed for scene {scene_id}: {e}")
            return {"image_path": f"ERROR_SCENE_{scene_id}"}
