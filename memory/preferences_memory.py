import json
import os
from utils.config import load_config


class PreferencesMemory:
    def __init__(self):
        config = load_config()
        self.file_path = config["memory"]["preferences_file"]
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)

    def load(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save(self, preferences: dict):
        with open(self.file_path, "w") as f:
            json.dump(preferences, f, indent=2)

    def update(self, new_prefs: dict):
        prefs = self.load()
        prefs.update(new_prefs)
        self.save(prefs)


preferences_memory = PreferencesMemory()
