import json
import os
from google import genai
from google.genai import types
from tools.database import save_scene

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def process_script_and_breakdown(project_id: str, script_text: str):
    """Uses Gemini to parse raw script text into structured scenes and saves to ClickHouse."""
    client = get_gemini_client()
    
    prompt = f"""
    You are an expert film 1st AD and script breakdown supervisor.
    Parse the following screenplay text and return a strict JSON list of scenes.
    Each item must contain:
    - scene_num (integer)
    - header (e.g. EXT. STREET - NIGHT)
    - description (concise action summary)
    - characters (list of character names present)
    - props (list of key props required)

    Screenplay:
    {script_text}

    Return ONLY a raw JSON array matching this schema. No markdown wrapping.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    scenes = json.loads(response.text)
    for s in scenes:
        save_scene(
            project_id=project_id,
            scene_num=int(s.get("scene_num", 1)),
            header=s.get("header", "UNKNOWN"),
            description=s.get("description", ""),
            characters=s.get("characters", []),
            props=s.get("props", [])
        )
    return scenes

def generate_table_read_rehearsal(scene_text: str):
    """Formats dialogue for rehearsal with performance and emotional direction."""
    client = get_gemini_client()
    prompt = f"""
    Convert the following scene dialogue into an annotated table-read rehearsal script.
    Add vocal tone, pacing notes, and emotional subtext for the actors.
    
    Scene:
    {scene_text}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text
