import os
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

def get_db_client():
    """Initializes and returns a ClickHouse client."""
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "8443"))
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    database = os.getenv("CLICKHOUSE_DATABASE", "default")
    secure = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"

    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        database=database,
        secure=secure
    )

def init_tables():
    """Creates the shared studio tables in ClickHouse if they do not exist."""
    try:
        client = get_db_client()
        
        # Table 1: Scenes metadata (populated by Pre-Production)
        client.command("""
        CREATE TABLE IF NOT EXISTS scenes (
            project_id String,
            scene_num UInt32,
            header String,
            description String,
            characters Array(String),
            props Array(String),
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (project_id, scene_num);
        """)

        # Table 2: Call sheets (populated by On-Set Crew)
        client.command("""
        CREATE TABLE IF NOT EXISTS call_sheets (
            project_id String,
            shoot_date String,
            call_time String,
            location String,
            scenes_to_shoot Array(UInt32),
            notes String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (project_id, shoot_date);
        """)

        # Table 3: Dailies & continuity flags (populated by Post-Production)
        client.command("""
        CREATE TABLE IF NOT EXISTS dailies (
            project_id String,
            scene_num UInt32,
            take_num UInt32,
            clip_name String,
            visual_summary String,
            continuity_status String,
            flagged_issues String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (project_id, scene_num, take_num);
        """)
        return True, "Database initialized successfully."
    except Exception as e:
        return False, f"ClickHouse connection error: {str(e)}"

def save_scene(project_id, scene_num, header, description, characters, props):
    client = get_db_client()
    client.insert(
        "scenes",
        [[project_id, scene_num, header, description, characters, props]],
        column_names=["project_id", "scene_num", "header", "description", "characters", "props"]
    )

def get_project_scenes(project_id):
    client = get_db_client()
    result = client.query(f"SELECT scene_num, header, description, characters, props FROM scenes WHERE project_id = '{project_id}' ORDER BY scene_num")
    return result.result_rows

def save_call_sheet(project_id, shoot_date, call_time, location, scenes, notes):
    client = get_db_client()
    client.insert(
        "call_sheets",
        [[project_id, shoot_date, call_time, location, scenes, notes]],
        column_names=["project_id", "shoot_date", "call_time", "location", "scenes_to_shoot", "notes"]
    )

def get_call_sheets(project_id):
    client = get_db_client()
    result = client.query(f"SELECT shoot_date, call_time, location, scenes_to_shoot, notes FROM call_sheets WHERE project_id = '{project_id}' ORDER BY shoot_date DESC")
    return result.result_rows

def save_daily_take(project_id, scene_num, take_num, clip_name, summary, status, flags):
    client = get_db_client()
    client.insert(
        "dailies",
        [[project_id, scene_num, take_num, clip_name, summary, status, flags]],
        column_names=["project_id", "scene_num", "take_num", "clip_name", "visual_summary", "continuity_status", "flagged_issues"]
    )

def search_dailies(project_id, query_text):
    client = get_db_client()
    query = f"""
    SELECT scene_num, take_num, clip_name, visual_summary, continuity_status, flagged_issues 
    FROM dailies 
    WHERE project_id = '{project_id}' AND (positionCaseInsensitive(visual_summary, '{query_text}') > 0 OR positionCaseInsensitive(flagged_issues, '{query_text}') > 0)
    """
    result = client.query(query)
    return result.result_rows
