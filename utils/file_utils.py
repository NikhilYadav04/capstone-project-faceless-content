import os
from utils.config import load_config

def ensure_directories():
    config = load_config()
    for key, path in config["paths"].items():
        os.makedirs(path, exist_ok=True)
