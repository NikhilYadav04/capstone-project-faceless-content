import google.generativeai as genai
import json
from google.adk.agents import Agent

from state.story_state import StoryState
from utils.config import load_config
from utils.env import load_env
from utils.logger import get_logger
from tools.hashtag_tool import HashtagTool

from pydantic import PrivateAttr

# --- Configuration & Logging ---
load_env()
config = load_config()
genai.configure(api_key=config["api_keys"]["google_api_key"])
logger = get_logger(__name__)

# --- System Prompts ---
# Guides the agent to act as a social media expert
SYSTEM_PROMPT = """
You are "Boost", a social media optimization AI. Your job is to take a
completed video script and concept, and generate a full posting guide
to maximize engagement.

You MUST output a JSON object with the following exact keys:
- "caption": A short, catchy caption for platforms like Instagram Reels or TikTok.
- "hashtags": A list of relevant, trending hashtags.
- "thumbnail_text_ideas": A list of 3 short, "clickable" text ideas for the video thumbnail.
- "best_post_time": A suggested best time to post (e.g., "6:30 PM T").
- "video_title_variants": A list of 3 alternative, catchy titles for YouTube.
"""


# --- Agent Definition ---
class SocialOptimizationAgent(Agent):
    """
    Agent 5: Generates a social media posting guide.
    """

    name: str = "social_optimizer_agent"
    description: str = "Generates captions, hashtags, and posting tips."
    _llm: genai.GenerativeModel = PrivateAttr()
    _hashtag_tool: HashtagTool = PrivateAttr()

    def __init__(self):
        super().__init__()
        # Initialize the LLM
        self._llm = genai.GenerativeModel(
            model_name=config["models"]["social_optimizer"],
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"},
        )

        # Initialize the tool this agent needs
        self._hashtag_tool = HashtagTool()

    def call(self, story_state: StoryState) -> StoryState:
        """
        Takes the script and concept to generate a social media package.
        """

        if not story_state.script or not story_state.expanded_idea:
            logger.warning("No script or concept found. Skipping social optimization.")
            story_state.metadata["error_social_optimizer"] = (
                "Missing script or expanded_idea"
            )
            return story_state

        logger.info("Generating social media optimization package...")

        try:
            # 1. Use the HashTagTool to get some base hashtags
            topic = story_state.expanded_idea.get("theme", "general")

            base_hashtags = self._hashtag_tool.call({"topic": topic})["hashtags"]

            # 2. Prepare the prompt for the LLM
            logline = story_state.script.get("logline", "A short video.")
            title = story_state.script.get("title", "New Video")

            user_prompt = f"""
            Generate a social media package for the following video:

            Title: "{title}"
            Logline: "{logline}"
            Base Hashtags to include: {base_hashtags}
            """

            # 3. Call the LLM
            response = self._llm.generate_content(user_prompt)

            # 4. Store the output in the state
            social_json = response.text
            story_state.social_output = json.loads(social_json)

            logger.info("Social media package generated.")

            # Record metadata
            story_state.metadata["social_optimizer_tokens"] = (
                response.usage_metadata.total_token_count
            )
        except Exception as e:
            logger.error(f"Error during social optimization: {e}")
            story_state.metadata["error_social_optimizer"] = str(e)

        return story_state
