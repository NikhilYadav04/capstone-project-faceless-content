# The Faceless Engine 🤖🎬

A multi-agent pipeline built with Google ADK that turns a single, one-line idea into a complete, "camera-ready" production package for faceless content.

## 1. The Problem: The "Faceless" Bottleneck

The internet is seeing a massive trend in "faceless" content. Creators are building huge audiences by producing anonymous videos using AI-generated visuals and voiceovers.

This process, however, is a **major creative bottleneck**. It's tedious, manual, and requires the creator to be a jack-of-all-trades:

- **A Scriptwriter:** To write an engaging story.
- **An Art Director:** To break the script into visual scenes.
- **A Prompt Engineer:** To craft hundreds of meticulous prompts for an image model.
- **A Marketer:** To write catchy captions and find trending hashtags.

**The Faceless Engine** solves this. It's an end-to-end, multi-agent system that automates the entire creative workflow, acting as a complete AI production team.

## 2. The Solution: A 5-Agent Pipeline

This project is a multi-agent system where a central **Coordinator Agent** passes a `StoryState` (a central data packet) through a five-stage, automated assembly line:

1.  **💡 Idea Expansion Agent:** Takes a simple idea (e.g., "a cat trying to steal pizza") and expands it into a full cinematic concept, defining the genre, mood, and a strict time limit.
2.  **✍️ Script Writer Agent:** Writes a complete, structured script based on the concept, including a title, logline, and scene-by-scene action.
3.  **🎬 Scene Breakdown Agent:** Acts as the Director of Photography, translating the _narrative_ script into a _visual_ shot list (e.g., "Scene 1: WIDE SHOT - A cat peeks over a kitchen counter.").
4.  **🖼️ Storyboard Visual Agent (Parallel):** This is the core of the engine. Using Python's `ThreadPoolExecutor`, it runs a `PromptRefinerTool` and `ImageGenerationTool` for all scenes simultaneously, generating a complete, artistic storyboard in seconds.
5.  **📈 Social Optimization Agent:** This "go-to-market" agent uses a `HashtagTool` (Tavily API) to find real, trending hashtags and then uses a Gemini LLM to write the complete social media package.

## 3. The Final Output 📦

The user receives a single, comprehensive JSON package containing:

- The expanded cinematic concept.
- The complete script, with dialogue and actions.
- A list of all visual scenes.
- A list of all AI-generated cinematic prompts.
- A list of all file paths for the generated storyboard images.
- A full social media kit (caption, titles, and real hashtags).

A creator can now feed these assets directly into an image-to-video model (like Pika or Runway) to complete their faceless video.

## 🛠️ Tech Stack & Core Components

- **Core Framework:** Google ADK (Agent Development Kit)
- **API Server:** FastAPI, Uvicorn
- **LLMs:** Google Gemini (1.5 Flash & Pro)
- **Image Generation:** Stablecog API
- **Live Search:** Tavily API
- **Memory:**
  - **Session Memory:** A `StoryState` dataclass.
  - **Long-Term Memory:** A `preferences.json` file for user styles.
- **Concurrency:** Python's `ThreadPoolExecutor` for parallel image generation.

---

## 🚀 How to Run This Project

### 1. Setup & Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Generate and install requirements:**

    - (First, make sure you have all packages installed from our debugging session: `google-adk`, `google-generativeai`, `fastapi`, `uvicorn`, `tavily-python`, `requests`, `pydantic`, `python-dotenv`, `rich`)
    - Create a `requirements.txt` file in your venv:
      ```bash
      pip freeze > requirements.txt
      ```
    - (Now, anyone else can just run this):
      ```bash
      pip install -r requirements.txt
      ```

4.  **Create your `.env` file:**
    Create a file named `.env` in the root of your project and add your API keys:

    ```env
    GOOGLE_API_KEY="your-google-api-key"
    STABLECOG_API_KEY="your-stablecog-api-key"
    TAVILY_API_KEY="your-tavily-api-key"
    ```

5.  **Configure `configs/settings.yaml`:**
    This is the main configuration file for the project. Create it at `configs/settings.yaml` and paste in the following:

    ```yaml
    app:
      name: "StoryCrafter Agent System"
      environment: "development"

    api_keys:
      google_api_key: "YOUR_GOOGLE_API_KEY_HERE"

    models:
      idea_expansion: "gemini-2.0-flash"
      script_writer: "gemini-2.0-flash"
      scene_breakdown: "gemini-2.0-flash"
      social_optimizer: "gemini-2.0-flash"
      prompt_refiner: "gemini-2.0-flash"

    paths:
      final: "outputs/final"
      images: "outputs/images"
      prompts: "outputs/prompts"
      scenes: "outputs/scenes"
      scripts: "outputs/scripts"

    memory:
      preferences_file: "memory/preferences.json"
    ```

    **Note:** Make sure to replace `"YOUR_GOOGLE_API_KEY_HERE"` with your actual key.

### 2. Run the API Server

With your virtual environment active, run the following command from your terminal:

```bash
uvicorn main:app --reload --port 8000
Your API is now running at http://localhost:8000.

3. Test the Endpoint
You can use any API client (like Postman or Insomnia) or the following curl command to run the entire pipeline:

Bash

curl -X POST "http://localhost:8000/generate" \
-H "Content-Type: application/json" \
-d '{
    "idea": "A short sci-fi video about a robot that finds a plant in a ruined city"
}'
```
