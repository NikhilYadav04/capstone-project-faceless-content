import yaml
import os

def load_config():
    config_path = os.path.join("configs", "settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
