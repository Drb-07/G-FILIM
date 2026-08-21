import json
import os
from google import genai
from google.genai import types
from tools.database import get_project_scenes, save_daily_take, search_dailies

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def inspect_take_continuity(project_id: str, scene_num: int, take_num: int, clip_name: str, take_description: str):
    """Checks filmed take notes/metadata against the original script in ClickHouse."""
    scenes = get_project_scenes(project_id)
    matched_scene = next((s for s in scenes if s[0] == scene_num), None)

    script_info = f"Header: {matched_scene[1]}, Action: {matched_scene[2]}, Characters: {matched_scene[3]}, Props: {matched_scene[4]}" if matched_scene else "No prior script breakdown found."

    client = get_gemini_client()
    prompt = f"""
    You are a film script supervisor and post-production editor.
    Compare this filmed take against the original approved scene requirements:
    
    Original Scene Spec:
    {script_info}
    
    Filmed Take Description:
    {take_description}
    
    Respond in JSON format with:
    - visual_summary: short description of what was filmed
    - continuity_status: "PASSED" or "FLAGGED"
    - flagged_issues: list of discrepancies (missing props, lighting mismatch, costume bugs, or 'None')
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )

    data = json.loads(response.text)
    summary = data.get("visual_summary", take_description)
    status = data.get("continuity_status", "PASSED")
    flags = str(data.get("flagged_issues", "None"))

    save_daily_take(project_id, scene_num, take_num, clip_name, summary, status, flags)
    return data

def query_project_footage(project_id: str, search_query: str):
    """Queries ClickHouse for matching dailies metadata."""
    return search_dailies(project_id, search_query)
