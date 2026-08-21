import streamlit as st
import os
from tools.database import init_tables, get_project_scenes, get_call_sheets
from agents.pre_prod import process_script_and_breakdown, generate_table_read_rehearsal
from agents.on_set import create_dynamic_call_sheet
from agents.post_prod import inspect_take_continuity, query_project_footage

st.set_page_config(page_title="CineHub | AI Studio OS", page_icon="🎬", layout="wide")

# Initialize Session State
if "project_id" not in st.session_state:
    st.session_state.project_id = "PRJ_BLOCKBUSTER_01"

# Sidebar Configuration
with st.sidebar:
    st.title("🎬 CineHub OS")
    st.caption("Agentic Multi-Role Studio Platform")
    st.session_state.project_id = st.text_input("Active Project ID", value=st.session_state.project_id)
    
    st.divider()
    if st.button("Initialize / Test ClickHouse DB"):
        success, msg = init_tables()
        if success:
            st.success(msg)
        else:
            st.error(msg)
    
    st.info(f"Connected: `{st.session_state.project_id}`")

# Workspace Tabs
tab1, tab2, tab3 = st.tabs([
    "✍️ 1. Pre-Production (Writers & Directors)", 
    "🎥 2. On-Set Crew (Call Sheets & Schedules)", 
    "✂️ 3. Post-Production (Dailies & Continuity)"
])

# ----------------------------------------------------
# TAB 1: PRE-PRODUCTION
# ----------------------------------------------------
with tab1:
    st.header("Screenplay Breakdown & Table-Read Rehearsal")
    st.write("Upload or paste screenplay pages to extract scenes, props, and cast automatically into ClickHouse.")
    
    sample_script = """EXT. NEO TOKYO ALLEYWAY - NIGHT
Heavy rain drenches the asphalt. DETECTIVE VANCE (40s, trench coat) holds a glowing cypher-deck in his left hand.
He glances behind him. A cybernetic drone buzzes overhead.

VANCE
(into collar mic)
I found the package. Moving to extraction point B."""

    script_input = st.text_area("Screenplay Text", value=sample_script, height=180)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Ingest & Extract Scene Breakdown"):
            with st.spinner("Gemini Agent analyzing script & saving to ClickHouse..."):
                try:
                    scenes = process_script_and_breakdown(st.session_state.project_id, script_input)
                    st.success(f"Successfully processed {len(scenes)} scenes into ClickHouse.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("🎙️ Generate Director Table-Read"):
            with st.spinner("Generating performance subtext..."):
                try:
                    rehearsal = generate_table_read_rehearsal(script_input)
                    st.session_state.rehearsal_output = rehearsal
                except Exception as e:
                    st.error(f"Error: {e}")

    if "rehearsal_output" in st.session_state:
        st.subheader("Annotated Table-Read")
        st.markdown(st.session_state.rehearsal_output)

    st.subheader("Current Project Scenes in Database")
    try:
        current_scenes = get_project_scenes(st.session_state.project_id)
        if current_scenes:
            st.dataframe(
                current_scenes,
                headers=["Scene #", "Header", "Description", "Characters", "Props"],
                use_container_width=True
            )
        else:
            st.caption("No scenes recorded for this Project ID yet.")
    except Exception as e:
        st.warning("ClickHouse tables not yet initialized. Click 'Initialize DB' in sidebar.")

# ----------------------------------------------------
# TAB 2: ON-SET CREW
# ----------------------------------------------------
with tab2:
    st.header("Dynamic Call-Sheet Dispatcher")
    st.write("Pull scene metadata directly from ClickHouse to build and adjust daily shooting schedules.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        shoot_date = st.date_input("Shoot Date").strftime("%Y-%m-%d")
    with col_b:
        call_time = st.time_input("Crew Call Time").strftime("%H:%M")
    with col_c:
        location = st.text_input("Location", value="Stage 4 / Exterior Alley")

    # Get available scene numbers
    try:
        scenes = get_project_scenes(st.session_state.project_id)
        available_nums = [s[0] for s in scenes] if scenes else [1]
    except:
        available_nums = [1]

    selected_scenes = st.multiselect("Select Scenes to Shoot Today", options=available_nums, default=available_nums[:1])

    if st.button("📋 Generate & Dispatch Call Sheet"):
        with st.spinner("AD Agent synthesizing schedule..."):
            try:
                sheet = create_dynamic_call_sheet(
                    st.session_state.project_id, 
                    shoot_date, 
                    call_time, 
                    location, 
                    selected_scenes
                )
                st.success("Call sheet saved to ClickHouse and ready for crew access.")
                st.markdown(sheet)
            except Exception as e:
                st.error(f"Error: {e}")

    st.subheader("Dispatched Call Sheets Log")
    try:
        sheets = get_call_sheets(st.session_state.project_id)
        if sheets:
            st.dataframe(sheets, headers=["Date", "Call Time", "Location", "Scenes", "Notes"], use_container_width=True)
    except:
        pass

# ----------------------------------------------------
# TAB 3: POST-PRODUCTION
# ----------------------------------------------------
with tab3:
    st.header("Dailies Quality & Continuity Inspector")
    st.write("Cross-reference filmed takes against script specifications in ClickHouse.")

    col_x, col_y, col_z = st.columns(3)
    with col_x:
        scene_num_input = st.number_input("Scene #", min_value=1, value=1)
    with col_y:
        take_num_input = st.number_input("Take #", min_value=1, value=1)
    with col_z:
        clip_name_input = st.text_input("Clip / Asset Name", value="A001_C004_RAW.MOV")

    take_desc = st.text_area(
        "Take Visual Notes / Multimodal Video Summary",
        value="Vance walks through the alley under light rain. He holds the cypher-deck in his RIGHT hand and speaks into the collar mic."
    )

    if st.button("🔍 Run Dailies Continuity Audit"):
        with st.spinner("Post-Production Agent auditing take against ClickHouse database..."):
            try:
                result = inspect_take_continuity(
                    st.session_state.project_id,
                    scene_num_input,
                    take_num_input,
                    clip_name_input,
                    take_desc
                )
                if result.get("continuity_status") == "PASSED":
                    st.success("✅ Continuity Verification Passed!")
                else:
                    st.error("⚠️ Continuity Issue Detected!")
                st.json(result)
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.subheader("Search Dailies Library")
    search_q = st.text_input("Natural Language Footage Search", placeholder="e.g. cypher-deck, rain, right hand")
    if st.button("Search Archive"):
        try:
            results = query_project_footage(st.session_state.project_id, search_q)
            if results:
                st.dataframe(
                    results,
                    headers=["Scene", "Take", "Clip Name", "Visual Summary", "Status", "Flags"],
                    use_container_width=True
                )
            else:
                st.info("No matching footage found.")
        except Exception as e:
            st.error(f"Error: {e}")
