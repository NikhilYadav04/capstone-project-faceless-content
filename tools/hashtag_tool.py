import re
from google.adk.tools import FunctionTool
from tavily import TavilyClient
from pydantic import PrivateAttr
from typing import Optional

from utils.env import load_env
from utils.logger import get_logger

# --- Config & Logging ---
logger = get_logger(__name__)
env = load_env()


class HashtagTool(FunctionTool):
    _search_tool: Optional[TavilyClient] = PrivateAttr()
    _api_key: Optional[str] = PrivateAttr()

    def __init__(self):
        super().__init__(func=self.call)
        self._api_key = env.get("TAVILY_API_KEY")

        if not self._api_key:
            logger.error("TAVILY_API_KEY missing. Hashtag tool will fail.")
            self._search_tool = None
        else:
            self._search_tool = TavilyClient(api_key=self._api_key)

    def name(self):
        return "hashtags"

    def description(self):
        return "Finds relevant and trending hashtags for a given topic using Tavily Search."

    def input_schema(self):
        return {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"],
        }

    def output_schema(self):
        return {
            "type": "object",
            "properties": {"hashtags": {"type": "array", "items": {"type": "string"}}},
            "required": ["hashtags"],
        }

    def call(self, input):
        if not self._search_tool:
            return {"hashtags": ["#error", "#config_missing"]}

        topic = input["topic"]
        query = f"trending hashtags for {topic} 2025"
        logger.info(f"Searching for hashtags with query: {query}")

        try:
            # 1. Call the Tavily Search tool
            search_results = self._search_tool.search(query=query)

            # 2. Extract text from snippets
            text_blob = " ".join(
                result.get("content", "")
                for result in search_results.get("results", [])
            )

            # 3. Find all hashtags using regex
            found_hashtags = re.findall(r"#(\w+)", text_blob)

            # 4. Create a clean, unique list
            unique_hashtags = list(set([f"#{tag}" for tag in found_hashtags]))

            # 5. Add the base topic hashtag
            base_hashtag = f"#{topic.replace(' ', '')}"
            if base_hashtag not in unique_hashtags:
                unique_hashtags.insert(0, base_hashtag)

            # Limit to a reasonable number
            final_list = unique_hashtags[:15]

            logger.info(f"Found {len(final_list)} hashtags.")
            return {"hashtags": final_list}

        except Exception as e:
            logger.error(f"Hashtag tool failed: {e}")
            # Fallback to the original dummy implementation
            t = topic.replace(" ", "")
            return {"hashtags": [f"#{t}", "#ai", "#shorts"]}
