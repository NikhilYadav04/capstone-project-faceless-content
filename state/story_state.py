from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class StoryState:
    """
    Global state container for the StoryCrafter multi-agent system.
    Each agent stores its output here, making it accessible to the next agent.
    """

    # Initial user input
    idea: Optional[str] = None

    # Agent 1 output: Expanded idea
    expanded_idea: Optional[Dict[str, Any]] = None

    # Agent 2 output: script + dialogues + structure
    script: Optional[Dict[str, Any]] = None

    # Agent 3 output: list of scenes with shot details
    scenes: Optional[List[Dict[str, Any]]] = None

    # Agent 4 output: visual prompts + generated image paths
    storyboard_prompts: Optional[List[Dict[str, Any]]] = None
    storyboard_images: Optional[List[str]] = None  # local image file path

    # Agent 5 output: captions, hashtags, posting schedule
    social_output: Optional[Dict[str, Any]] = None

    # Long-term memory preferences loaded here for reuse
    preferences: Optional[Dict[str, Any]] = field(default_factory=dict)

    # Final packaged bundle (merged data for export)
    final_package: Optional[Dict[str, Any]] = None

    # Internal metadata for debugging/evaluation
    metadata: Dict[str, Any] = field(default_factory=dict)
