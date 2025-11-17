import json
from google.adk.agents import Agent  # <-- Corrected import
from state.story_state import StoryState
from memory.session_memory import get_session_memory
from memory.preferences_memory import preferences_memory
from pydantic import PrivateAttr

# Import all our agents
from agents.idea_expansion_agent import IdeaExpansionAgent
from agents.script_writer_agent import ScriptWriterAgent
from agents.scene_breakdown_agent import SceneBreakdownAgent
from agents.storyboard_visual_agent import StoryboardVisualAgent
from agents.social_optimizer_agent import SocialOptimizationAgent

# Import utils
from utils.env import load_env
from utils.config import load_config
from utils.file_utils import ensure_directories
from utils.logger import get_logger

# --- Setup ---
load_env()
load_config()
ensure_directories()
logger = get_logger(__name__)

# --- Coordinator Definition ---


class StoryCrafterCoordinator(Agent):
    """
    The main Coordinator Agent.
    It runs the 5 agents in a specific sequence to build the story.
    """

    name: str = "story_crafter_coordinator"
    description: str = "The main coordinator for the StoryCrafter pipeline."

    # -- ANNOTATIONS --
    _idea_expander: IdeaExpansionAgent = PrivateAttr()
    _script_writer: ScriptWriterAgent = PrivateAttr()
    _scene_breaker: SceneBreakdownAgent = PrivateAttr()
    _visual_generator: StoryboardVisualAgent = PrivateAttr()
    _social_optimizer: SocialOptimizationAgent = PrivateAttr()

    def __init__(self):
        super().__init__()
        # Instantiate all the agents the coordinator will use
        self._idea_expander = IdeaExpansionAgent()
        self._script_writer = ScriptWriterAgent()
        self._scene_breaker = SceneBreakdownAgent()
        self._visual_generator = StoryboardVisualAgent()
        self._social_optimizer = SocialOptimizationAgent()
        logger.info("Coordinator initialized with all agents.")

    def call(self, state: StoryState) -> StoryState:
        """
        Executes the full agent pipeline in sequence.
        """

        try:
            logger.info("--- Pipeline Start ---")

            # Agent 1: Idex Expansion
            logger.info("Running IdeaExpansionAgent...")
            state = self._idea_expander.call(state)
            if "error_idea_expansion" in state.metadata:
                raise Exception(state.metadata["error_idea_expansion"])

            # Agent 2: Script Writer
            logger.info("Running ScriptWriterAgent...")
            state = self._script_writer.call(state)
            if "error_script_writer" in state.metadata:
                raise Exception(state.metadata["error_script_writer"])

            # Agent 3: Scene Breakdown
            logger.info("Running SceneBreakdownAgent...")
            state = self._scene_breaker.call(state)
            if "error_scene_breakdown" in state.metadata:
                raise Exception(state.metadata["error_scene_breakdown"])

            # Agent 4: Storyboard Visuals (Parallel)
            logger.info("Running StoryboardVisualAgent (Parallel)...")
            state = self._visual_generator.call(state)
            if "error_storyboard" in state.metadata:
                raise Exception(state.metadata["error_storyboard"])

            # Agent 5: Social Optimizer
            logger.info("Running SocialOptimizationAgent...")
            state = self._social_optimizer.call(state)
            if "error_social_optimizer" in state.metadata:
                raise Exception(state.metadata["error_social_optimizer"])

            # Final Step: Package the output
            logger.info("Packaging final output...")
            state = self._create_final_package(state)

            logger.info("--- Pipeline Complete ---")
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            state.metadata["pipeline_error"] = str(e)

        return state

    def _create_final_package(self, state: StoryState) -> StoryState:
        """
        Gathers all data from the state into the 'final_package' field.
        """
        state.final_package = {
            "idea": state.idea,
            "expanded_idea": state.expanded_idea,
            "script": state.script,
            "scenes_list": state.scenes,
            "storyboard_prompts": state.storyboard_prompts,
            "storyboard_images": state.storyboard_images,
            "social_media_guide": state.social_output,
            "metadata": state.metadata,
        }
        return state


# -- Main execution block ---


def run_pipeline(idea: str) -> dict:
    """
    A helper function to run the full pipeline.
    """

    # 1. Load preferences
    prefs = preferences_memory.load()

    # 2. Create the initial state
    initial_state = StoryState(idea=idea, preferences=prefs)

    # 3. Get session memory (from ADK)
    session_memory = get_session_memory()

    # 4. Create the Coordinator
    coordinator = StoryCrafterCoordinator()

    # 5. Run the coordinator
    # We pass the coordinator, the initial state, and the memory
    final_state = coordinator.call(initial_state)

    # 6. Return the final, packaged result
    return final_state.final_package


if __name__ == "__main__":
    logger.info("Starting StoryCrafter pipeline...")

    # --- INPUT ---
    TEST_IDEA = "A short horror video about a person who finds an old, unplugged radio that starts talking"

    # Run the entire pipeline
    final_output = run_pipeline(TEST_IDEA)

    # Pretty-print the final JSON output
    print("\n--- FINAL OUTPUT PACKAGE ---")
    print(json.dumps(final_output, indent=2))
    print("-----------------------------")

    # Save the final output to a file
    output_path = "outputs/final/final_story_package.json"
    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=2)
    logger.info(f"Final package saved to {output_path}")
