from google.adk.memory import InMemoryMemoryService

# Handles per-session storage for agents
session_memory = InMemoryMemoryService()


def get_session_memory():
    return session_memory
