import streamlit as st
import os
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="CineHub Studio OS",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CINEMATIC CUSTOM CSS ---
st.markdown("""
<style>
    /* Global Styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics & Stats Cards */
    .metric-card {
        background: #1e222d;
        border: 1px solid #2d3343;
        border-radius: 10px;
        padding: 16px 20px;
        color: white;
        margin-bottom: 15px;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f59e0b;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Studio Header */
    .studio-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid #312e81;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    
    /* Status Badges */
    .badge-pass {
        background-color: #064e3b;
        color: #6ee7b7;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-flag {
        background-color: #7f1d1d;
        color: #fca5a5;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    
    /* Card Component */
    .scene-card {
        background: #181b24;
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- SAFE IMPORTS FROM TEAM MODULES ---
try:
    from tools.database import init_tables, get_project_scenes, get_call_sheets, search_dailies
    from agents.pre_prod import process_script_and_breakdown, generate_table_read_rehearsal
    from agents.on_set import create_dynamic_call_sheet
    from agents.post_prod import inspect_take_continuity, query_project_footage
    MODULES_LOADED = True
except ImportError:
    MODULES_LOADED = False

# --- SESSION STATE INITIALIZATION ---
if "project_id" not in st.session_state:
    st.session_state.project_id = "PRJ_BLOCKBUSTER_ALPHA"
if "db_connected" not in st.session_state:
    st.session_state.db_connected = False

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/clapperboard.png", width=64)
    st.title("CineHub OS")
    st.caption("Agentic Autonomous Studio Workspace")
    
    st.divider()
    st.session_state.project_id = st.text_input(
        "Project Scope ID",
        value=st.session_state.project_id,
        help="All scene breakdowns, call sheets, and dailies link to this ID."
    )
    
    st.divider()
    st.markdown("### 🔌 Infrastructure & DB")
    
    if st.button("⚡ Connect ClickHouse", use_container_width=True):
        if MODULES_LOADED:
            success, msg = init_tables()
            st.session_state.db_connected = success
            if success:
                st.toast("ClickHouse Database Active", icon="🟢")
            else:
                st.error(msg)
        else:
            st.session_state.db_connected = True
            st.toast("Demo Mode Active (No local backends detected)", icon="🟡")

    status_color = "🟢" if st.session_state.db_connected else "🔴"
    status_text = "ClickHouse Online" if st.session_state.db_connected else "Offline / Disconnected"
    st.caption(f"Status: **{status_color} {status_text}**")
    
    st.divider()
    st.markdown("### 👥 Agent Crew Fleet")
    st.caption("🟢 `Writer/Director Agent` (Gemini 2.5)")
    st.caption("🟢 `1st AD Crew Agent` (Gemini 2.5)")
    st.caption("🟢 `Dailies Continuity Inspector` (Multimodal)")

# --- LIVE METRIC STRIP ---
try:
    scenes_count = len(get_project_scenes(st.session_state.project_id)) if MODULES_LOADED else 4
    sheets_count = len(get_call_sheets(st.session_state.project_id)) if MODULES_LOADED else 1
except:
    scenes_count, sheets_count = 0, 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">Active Project</div><div class="metric-val">{st.session_state.project_id[:12]}...</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">Ingested Scenes</div><div class="metric-val">{scenes_count}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">Active Call Sheets</div><div class="metric-val">{sheets_count}</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">Continuity Index</div><div class="metric-val">98.4%</div></div>', unsafe_allow_html=True)

# --- WORKSPACE TABS ---
tab_pre, tab_set, tab_post = st.tabs([
    "✍️  Pre-Production Studio", 
    "🎥  On-Set Operations", 
    "✂️  Post-Production & Dailies"
])

# ==============================================================================
# TAB 1: PRE-PRODUCTION
# ==============================================================================
with tab_pre:
    st.markdown("### 📄 Screenplay Ingestion & Automated Breakdown")
    st.caption("Ingest raw screenplay files to extract scene elements directly into the persistent project state.")

    col_script, col_preview = st.columns([1.1, 0.9], gap="large")

    with col_script:
        sample_screenplay = """EXT. NEO TOKYO ALLEYWAY - NIGHT
Heavy rain drenches the neon asphalt. DETECTIVE VANCE (40s, damp trench coat) inspects a glowing cypher-deck with his left hand.
A surveillance drone hovers quietly above.

VANCE
(whispering into comms)
The cipher is intact. Moving to checkpoint 4.

EXT. SUBWAY ENTRANCE - CONTINUOUS
Vance enters the glowing terminal. OFFICER CHEN waits by the turnstiles carrying a tactical duffle bag."""

        script_text = st.text_area("Screenplay Paste / File Feed", value=sample_screenplay, height=260)
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            run_breakdown = st.button("🚀 Ingest & Extract Breakdown", use_container_width=True, type="primary")
        with btn_col2:
            run_rehearsal = st.button("🎙️ Generate Director Table-Read", use_container_width=True)

        if run_breakdown:
            with st.spinner("Gemini Agent parsing scenes, characters, and props..."):
                if MODULES_LOADED:
                    try:
                        scenes = process_script_and_breakdown(st.session_state.project_id, script_text)
                        st.success(f"Parsed {len(scenes)} scenes into ClickHouse state.")
                    except Exception as e:
                        st.error(f"Execution Error: {e}")
                else:
                    time.sleep(1)
                    st.success("Parsed 2 scenes into ClickHouse state (Demo Mode).")

    with col_preview:
        if run_rehearsal:
            with st.spinner("Synthesizing audio subtext and actor delivery notes..."):
                if MODULES_LOADED:
                    try:
                        notes = generate_table_read_rehearsal(script_text)
                        st.session_state.table_read_notes = notes
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.session_state.table_read_notes = "**VANCE (Subtext):** Exhausted, hyper-vigilant. Pacing should be rapid with heavy breath marks."

        if "table_read_notes" in st.session_state:
            st.markdown("#### 🎭 Director's Table-Read Notes")
            st.info(st.session_state.table_read_notes)

        st.markdown("#### 🗄️ ClickHouse Scene Graph")
        if MODULES_LOADED:
            try:
                scenes_data = get_project_scenes(st.session_state.project_id)
                if scenes_data:
                    for sc in scenes_data:
                        st.markdown(f"""
                        <div class="scene-card">
                            <b>Scene {sc[0]}: {sc[1]}</b><br>
                            <small style="color: #cbd5e1;">{sc[2]}</small><br>
                            <div style="margin-top: 8px;">
                                <span style="color: #f59e0b; font-size: 0.8rem;">Cast:</span> <span style="font-size: 0.8rem;">{", ".join(sc[3])}</span> | 
                                <span style="color: #38bdf8; font-size: 0.8rem;">Props:</span> <span style="font-size: 0.8rem;">{", ".join(sc[4])}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No scene breakdown ingested for this Project ID yet.")
            except Exception as e:
                st.warning("Click 'Connect ClickHouse' in the sidebar to view live table state.")
        else:
            st.caption("Connect backend to render live ClickHouse table graph.")

# ==============================================================================
# TAB 2: ON-SET OPERATIONS
# ==============================================================================
with tab_set:
    st.markdown("### 📋 Dynamic Call-Sheet & Set Dispatcher")
    st.caption("Generates deterministic crew schedules based on scene dependencies.")

    c1, c2, c3 = st.columns(3)
    with c1:
        shoot_date = st.date_input("Shoot Date").strftime("%Y-%m-%d")
    with c2:
        call_time = st.time_input("First Unit Call Time").strftime("%H:%M")
    with c3:
        location = st.text_input("Production Unit / Stage", value="Stage 2 — Virtual Rain Stage")

    selected_scenes = st.multiselect(
        "Select Ingested Scenes for Today's Shoot",
        options=[1, 2, 3, 4],
        default=[1, 2]
    )

    if st.button("⚡ Dispatch Production Call Sheet", type="primary"):
        with st.spinner("AD Agent calculating cast schedules and props..."):
            if MODULES_LOADED:
                try:
                    sheet = create_dynamic_call_sheet(
                        st.session_state.project_id, shoot_date, call_time, location, selected_scenes
                    )
                    st.success("Call sheet dispatched and logged to ClickHouse.")
                    st.markdown(sheet)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                time.sleep(1)
                st.success("Call sheet dispatched and logged to ClickHouse (Demo Mode).")
                st.markdown(f"""
                ### 🎬 OFFICIAL CALL SHEET — {shoot_date}
                * **Location:** {location} | **Crew Call:** {call_time}
                * **Scheduled Scenes:** Scene {selected_scenes}
                * **Safety Directives:** Wet set protocols active. Shield electronic props (cypher-deck).
                """)

    st.divider()
    st.markdown("#### 📜 Recent Production Call Logs")
    if MODULES_LOADED:
        try:
            call_logs = get_call_sheets(st.session_state.project_id)
            if call_logs:
                st.dataframe(call_logs, headers=["Date", "Call Time", "Location", "Scenes", "Notes"], use_container_width=True)
        except:
            pass

# ==============================================================================
# TAB 3: POST-PRODUCTION & DAILIES
# ==============================================================================
with tab_post:
    st.markdown("### 🔍 Dailies Quality & Continuity Inspector")
    st.caption("Multimodal cross-auditing between raw filmed video metadata and locked screenplay specs.")

    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("#### Log Filmed Take")
        s_num = st.number_input("Target Scene #", min_value=1, value=1)
        t_num = st.number_input("Take #", min_value=1, value=1)
        clip_label = st.text_input("Raw Clip Name / Camera Roll", value="ROLL_A_TAKE_01.MOV")

        take_obs = st.text_area(
            "Video Take Visual Notes / AI Video Feed",
            value="Detective Vance runs into the frame. He pulls out the cypher-deck with his RIGHT hand while wiping rain from his face.",
            height=120
        )

        audit_btn = st.button("🔬 Run Continuity Audit", type="primary", use_container_width=True)

    with col_result:
        st.markdown("#### Audit Verdict")
        if audit_btn:
            with st.spinner("Auditing take notes against ClickHouse baseline..."):
                if MODULES_LOADED:
                    try:
                        res = inspect_take_continuity(st.session_state.project_id, s_num, t_num, clip_label, take_obs)
                        is_pass = res.get("continuity_status") == "PASSED"
                        
                        if is_pass:
                            st.markdown('<span class="badge-pass">✅ CONTINUITY VERIFIED</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge-flag">⚠️ DISCREPANCY FLAGGED</span>', unsafe_allow_html=True)
                        
                        st.json(res)
                    except Exception as e:
                        st.error(f"Audit Error: {e}")
                else:
                    time.sleep(1)
                    st.markdown('<span class="badge-flag">⚠️ DISCREPANCY FLAGGED</span>', unsafe_allow_html=True)
                    st.json({
                        "scene_num": s_num,
                        "take_num": t_num,
                        "visual_summary": "Actor Vance holding cypher-deck in RIGHT hand.",
                        "continuity_status": "FLAGGED",
                        "flagged_issues": "Prop Hand Mismatch: Script specifies LEFT hand in Scene 1."
                    })

    st.divider()
    st.markdown("#### 🔎 Studio Dailies Search Engine")
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        query_input = st.text_input("Query Archive (e.g. 'cypher-deck', 'right hand', 'rain')", label_visibility="collapsed")
    with search_col2:
        search_btn = st.button("Search Dailies", use_container_width=True)

    if search_btn and query_input:
        if MODULES_LOADED:
            try:
                results = query_project_footage(st.session_state.project_id, query_input)
                if results:
                    st.dataframe(results, headers=["Scene", "Take", "Clip", "Summary", "Status", "Issues"], use_container_width=True)
                else:
                    st.info("No matching takes found for this query.")
            except Exception as e:
                st.error(f"Search Error: {e}")
        else:
            st.info("Connect ClickHouse backend to run real-time search queries.")
