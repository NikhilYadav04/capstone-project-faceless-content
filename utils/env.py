from dotenv import load_dotenv
import os


def load_env():
    load_dotenv()
    env = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "FLUX_API_KEY": os.getenv("FLUX_API_KEY"),
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "STABLECOG_API_KEY": os.getenv("STABLECOG_API_KEY"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
    }
    return env
