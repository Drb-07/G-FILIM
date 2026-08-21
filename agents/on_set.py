import os
from google import genai
from tools.database import get_project_scenes, save_call_sheet

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def create_dynamic_call_sheet(project_id: str, shoot_date: str, call_time: str, location: str, selected_scene_nums: list):
    """Generates an optimized call sheet referencing scenes stored in ClickHouse."""
    all_scenes = get_project_scenes(project_id)
    target_scenes = [s for s in all_scenes if s[0] in selected_scene_nums]

    scene_context = "\n".join([
        f"Scene {s[0]}: {s[1]} | Cast: {', '.join(s[3])} | Props: {', '.join(s[4])}"
        for s in target_scenes
    ])

    client = get_gemini_client()
    prompt = f"""
    You are a production 1st AD. Draft an executive production call sheet summary.
    Shoot Date: {shoot_date}
    Call Time: {call_time}
    Main Location: {location}
    
    Scheduled Scenes:
    {scene_context}
    
    Output a structured daily call sheet including cast call times, department safety notes, and equipment requirements.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    notes = response.text
    save_call_sheet(project_id, shoot_date, call_time, location, selected_scene_nums, notes)
    return notes
