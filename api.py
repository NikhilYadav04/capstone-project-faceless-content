from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from memory.preferences_memory import preferences_memory
from state import story_state
from main import StoryCrafterCoordinator
from utils.logger import get_logger

logger = get_logger(__name__)

import json

# --- API Data Model ---


class IdeaInput(BaseModel):
    idea: str


# --- Pipeline Function (Keep as-is) ---


def run_pipeline(idea: str) -> dict:
    """
    A helper function to run the full pipeline.
    """
    # 1. Load preferences
    prefs = preferences_memory.load()

    # 2. Create the initial state
    initial_state = story_state.StoryState(idea=idea, preferences=prefs)

    # 3. Create the Coordinator
    coordinator = StoryCrafterCoordinator()

    # 4. Run the coordinator
    final_state = coordinator.call(initial_state)

    # 5. Return the final, packaged result
    return final_state.final_package


# --- FastAPI App ---

app = FastAPI(
    title="StoryCrafter API",
    description="Turns a one-line idea into a full video production package.",
)


@app.post("/generate")
def generate_story_package(input: IdeaInput):
    """
    Run the full multi-agent pipeline to generate a video package.
    """
    logger.info(f"Received API request for idea: {input.idea}")
    try:
        final_output = run_pipeline(input.idea)

        if not final_output:
            logger.error("Pipeline ran but produced no output.")
            return {"error": "Pipeline produced no output."}

        # Save the final output to a file (optional, but good for logging)
        output_path = "outputs/final/final_story_package.json"
        with open(output_path, "w") as f:
            json.dump(final_output, f, indent=2)
        logger.info(f"Final package saved to {output_path}")

        return final_output

    except Exception as e:
        logger.error(f"API Error: Pipeline failed with exception: {e}")
        return {"error": "Pipeline failed", "detail": str(e)}


@app.get("/")
def read_root():
    return {
        "message": "StoryCrafter API is running. POST to /generate to create a story."
    }


# --- Main execution block ---

if __name__ == "__main__":
    logger.info("Starting StoryCrafter API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
