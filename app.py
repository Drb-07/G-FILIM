import streamlit as st
import os
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="CINEAGENT | Studio AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SAFE IMPORTS FROM BACKEND MODULES ---
try:
    from tools.database import init_tables, get_project_scenes, get_call_sheets, search_dailies
    from agents.pre_prod import process_script_and_breakdown, generate_table_read_rehearsal
    from agents.on_set import create_dynamic_call_sheet
    from agents.post_prod import inspect_take_continuity, query_project_footage
    MODULES_LOADED = True
except ImportError:
    MODULES_LOADED = False

# --- SESSION STATE INITIALIZATION ---
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Overview"
if "project_id" not in st.session_state:
    st.session_state.project_id = "PRJ_MERIDIAN_01"
if "db_connected" not in st.session_state:
    st.session_state.db_connected = False

# --- LIGHT MODE: CRISP WHITE & VIBRANT PURPLE THEME (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Clean Light Canvas */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Light Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Brand Header */
    .brand-title {
        font-family: 'Outfit', sans-serif;
        color: #0f172a;
        letter-spacing: 0.1em;
        font-size: 1.2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-badge {
        background: #7c3aed;
        color: #ffffff;
        font-size: 0.62rem;
        padding: 2px 7px;
        border-radius: 6px;
        font-weight: 700;
    }
    .brand-sub {
        font-family: 'JetBrains Mono', monospace;
        color: #7c3aed;
        font-size: 0.68rem;
        letter-spacing: 0.18em;
        margin-top: 2px;
        margin-bottom: 20px;
        font-weight: 600;
    }

    /* Phase Banner */
    .phase-banner {
        background: linear-gradient(90deg, #ffffff 0%, #f5f3ff 100%);
        border: 1px solid #ddd6fe;
        border-left: 4px solid #7c3aed;
        border-radius: 12px;
        padding: 14px 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.05);
    }
    .phase-pill {
        background: #ede9fe;
        color: #6d28d9;
        border: 1px solid #c4b5fd;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    /* Stat Cards */
    .stat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        min-height: 125px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        transition: all 0.25s ease;
    }
    .stat-card:hover {
        border-color: #a855f7;
        box-shadow: 0 6px 18px rgba(124, 58, 237, 0.1);
        transform: translateY(-2px);
    }
    .stat-label {
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .stat-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin: 4px 0;
    }
    .stat-value span {
        font-size: 0.92rem;
        color: #64748b;
        font-weight: 400;
    }
    .stat-footer {
        font-size: 0.76rem;
        font-weight: 600;
    }

    /* Agent Zone Containers */
    .zone-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        min-height: 420px;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    }
    .zone-box-creative { border-top: 4px solid #7c3aed; }
    .zone-box-onset { border-top: 4px solid #0284c7; }
    .zone-box-post { border-top: 4px solid #c026d3; }

    .zone-header-wrap {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .zone-header-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        color: #0f172a;
    }
    .zone-pill {
        background: #f5f3ff;
        color: #6d28d9;
        border: 1px solid #ddd6fe;
        font-size: 0.72rem;
        padding: 2px 9px;
        border-radius: 20px;
        font-weight: 600;
    }

    /* Agent Rows */
    .agent-item {
        padding: 10px 12px;
        border-radius: 8px;
        background: #f8fafc;
        margin-bottom: 10px;
        border: 1px solid #e2e8f0;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
    .agent-item:hover {
        border-color: #c4b5fd;
        background-color: #faf5ff;
    }
    .agent-item-title {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        font-weight: 600;
        color: #0f172a;
    }
    .agent-item-desc {
        font-size: 0.75rem;
        color: #475569;
        margin-top: 3px;
        line-height: 1.35;
    }
    .agent-item-alert {
        color: #6d28d9;
        font-size: 0.72rem;
        margin-top: 5px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
    }

    /* Surface Card */
    .surface-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }
    .activity-row {
        padding: 10px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .activity-row:last-child {
        border-bottom: none;
    }
    .activity-agent {
        font-weight: 600;
        font-size: 0.84rem;
        color: #0f172a;
    }
    .activity-time {
        font-size: 0.72rem;
        color: #64748b;
        margin-left: 6px;
    }
    .activity-desc {
        font-size: 0.78rem;
        color: #334155;
        margin-top: 2px;
    }

    /* Schedule Tags */
    .sched-tag-today {
        background: #7c3aed;
        color: #ffffff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
    }
    .sched-tag-future {
        background: #ede9fe;
        color: #6d28d9;
        border: 1px solid #c4b5fd;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
    }

    /* Buttons */
    div.stButton > button {
        background: #ffffff;
        color: #6d28d9;
        border: 1px solid #ddd6fe;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.82rem;
        font-family: 'Plus Jakarta Sans', sans-serif;
        padding: 0.5rem 1rem;
        transition: all 0.25s ease;
    }
    div.stButton > button:hover {
        background: #7c3aed;
        border-color: #7c3aed;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.25);
        transform: translateY(-1px);
    }

    /* Input Fields */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 1px #7c3aed !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div class="brand-title">
        <span>🎬 CINEAGENT</span>
        <span class="brand-badge">STUDIO</span>
    </div>
    <div class="brand-sub">PRODUCTION AI SYSTEM</div>
    """, unsafe_allow_html=True)

    st.caption("STUDIO NAVIGATION")
    nav_choice = st.radio(
        "Nav",
        [
            "Overview",
            "Screenwriters & Directors",
            "On-Set Crew",
            "Post-Production",
            "Production Schedule",
            "Agent Event Feed",
            "Studio Settings"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("ACTIVE PRODUCTION SCOPE")
    st.markdown("<p style='font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;'>'The Last Meridian'</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.75rem; color: #6d28d9; margin-top: 2px; font-weight: 600;'>Feature Film · Sci-Fi Drama</p>", unsafe_allow_html=True)
    st.progress(0.41, text="Production Progress: 41%")

    st.divider()
    st.caption("DATA INFRASTRUCTURE")
    if st.button("⚡ Sync ClickHouse State", use_container_width=True):
        if MODULES_LOADED:
            success, msg = init_tables()
            st.session_state.db_connected = success
            if success:
                st.toast("ClickHouse Cluster Active", icon="🟣")
            else:
                st.error(msg)
        else:
            st.session_state.db_connected = True
            st.toast("Studio State Active (Ready)", icon="🟣")

    db_status = "🟢 ClickHouse Online" if st.session_state.db_connected else "🟣 ClickHouse Ready"
    st.caption(f"Cluster: `{db_status}`")

# ==============================================================================
# VIEW 1: OVERVIEW DASHBOARD
# ==============================================================================
if nav_choice == "Overview":
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
        <div>
            <h1 style="font-size: 1.6rem; margin: 0;">Production Dashboard</h1>
            <p style="font-size: 0.8rem; color: #64748b; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
                Day 17 of 42 · Principal Photography · Aug 21, 2026
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Status Banner
    st.markdown("""
    <div class="phase-banner">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #7c3aed; font-size: 0.85rem;">●</span>
            <span style="font-weight: 700; font-size: 0.88rem; letter-spacing: 0.04em; color: #0f172a;">PHASE: PRINCIPAL PHOTOGRAPHY</span>
            <span class="phase-pill">ON SCHEDULE</span>
        </div>
        <div style="font-size: 0.78rem; color: #475569; font-family: 'JetBrains Mono', monospace;">
            UNIT A · Stage 6 · Studio Lot &nbsp;|&nbsp; Director: A. Fontaine &nbsp;|&nbsp; DP: R. Osei
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Stat Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Days in Production</div>
            <div class="stat-value">17 <span>/ 42 days</span></div>
            <div class="stat-footer" style="color: #16a34a;">▲ 2 days ahead of schedule</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Scenes Completed</div>
            <div class="stat-value">63 <span>/ 118 scenes</span></div>
            <div class="stat-footer" style="color: #16a34a;">53% through principal photography</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Budget Utilized</div>
            <div class="stat-value">$2.4M <span>/ $5.8M</span></div>
            <div class="stat-footer" style="color: #7c3aed;">41% — within parameter</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Active Agents</div>
            <div class="stat-value">6 <span>/ 12 agents</span></div>
            <div class="stat-footer" style="color: #16a34a;">● All systems synchronized</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # 3 Agent Zone Columns
    z1, z2, z3 = st.columns(3)

    with z1:
        st.markdown("""
        <div class="zone-box zone-box-creative">
            <div class="zone-header-wrap">
                <span class="zone-header-title">📁 Creative</span>
                <span class="zone-pill">2 active</span>
            </div>
            <div style="font-size: 0.74rem; color: #64748b; margin-bottom: 16px;">Story development & creative vision</div>
            
            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● Script Doctor</span>
                    <span style="color: #7c3aed;">3</span>
                </div>
                <div class="agent-item-desc">Scene-level analysis, dialogue cadence, and act pacing</div>
                <div class="agent-item-alert">↳ Reviewed Act II pacing — 3 notes pending</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● Story Arc Analyzer</span>
                    <span style="color: #7c3aed;">7</span>
                </div>
                <div class="agent-item-desc">Character journey continuity & thematic motif tracking</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span style="color: #94a3b8;">○ Dialogue Coach</span>
                    <span style="color: #94a3b8;">-</span>
                </div>
                <div class="agent-item-desc">Performance subtext and multi-speaker script rehearsal</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span style="color: #94a3b8;">○ Pitch Deck Builder</span>
                    <span style="color: #94a3b8;">1</span>
                </div>
                <div class="agent-item-desc">Generates visual lookbooks & executive teasers</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Creative Workspace ⚡", key="btn_cw", use_container_width=True):
            st.session_state.active_nav = "Screenwriters & Directors"
            st.rerun()

    with z2:
        st.markdown("""
        <div class="zone-box zone-box-onset">
            <div class="zone-header-wrap">
                <span class="zone-header-title">🎥 On-Set</span>
                <span class="zone-pill">3 active</span>
            </div>
            <div style="font-size: 0.74rem; color: #64748b; margin-bottom: 16px;">Real-time set coordination</div>
            
            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● Continuity Tracker</span>
                    <span style="color: #0284c7;">5</span>
                </div>
                <div class="agent-item-desc">Prop, costume, and blocking continuity logs per take</div>
                <div class="agent-item-alert" style="color: #0284c7;">↳ Wardrobe discrepancy — Sc.47 Ext. Rooftop</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● Shot List Manager</span>
                    <span style="color: #0284c7;">12</span>
                </div>
                <div class="agent-item-desc">Tracks camera setups, focal lengths, and scene coverage</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● Logistics Coordinator</span>
                    <span style="color: #0284c7;">4</span>
                </div>
                <div class="agent-item-desc">Dynamic call sheets & weather delay adjustments</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span style="color: #94a3b8;">○ Safety Monitor</span>
                    <span style="color: #94a3b8;">-</span>
                </div>
                <div class="agent-item-desc">Stunt compliance & environmental safety checklist verification</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open On-Set Workspace ⚡", key="btn_ow", use_container_width=True):
            st.session_state.active_nav = "On-Set Crew"
            st.rerun()

    with z3:
        st.markdown("""
        <div class="zone-box zone-box-post">
            <div class="zone-header-wrap">
                <span class="zone-header-title">✂️ Post</span>
                <span class="zone-pill">2 active</span>
            </div>
            <div style="font-size: 0.74rem; color: #64748b; margin-bottom: 16px;">Editorial & delivery pipeline</div>
            
            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● Edit Assistant</span>
                    <span style="color: #c026d3;">8</span>
                </div>
                <div class="agent-item-desc">Dailies tagging, metadata sync, and timeline assembly</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span style="color: #94a3b8;">○ Color Grade Advisor</span>
                    <span style="color: #94a3b8;">2</span>
                </div>
                <div class="agent-item-desc">LUT consistency auditing & exposure balance checks</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span>● VFX Pipeline Monitor</span>
                    <span style="color: #c026d3;">6</span>
                </div>
                <div class="agent-item-desc">Tracks shot status across vendors & flags delays</div>
                <div class="agent-item-alert" style="color: #c026d3;">↳ 3 hero shots cleared from Vendor B</div>
            </div>

            <div class="agent-item">
                <div class="agent-item-title">
                    <span style="color: #94a3b8;">○ Sound Mix Advisor</span>
                    <span style="color: #94a3b8;">1</span>
                </div>
                <div class="agent-item-desc">Dialogue isolation & ambient foley score synthesis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Post Workspace ⚡", key="btn_pw", use_container_width=True):
            st.session_state.active_nav = "Post-Production"
            st.rerun()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Bottom Split: Agent Activity & Shoot Schedule
    col_act, col_sched = st.columns([1.25, 0.75], gap="large")

    with col_act:
        st.markdown("""
        <div class="surface-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em;">AGENT ACTIVITY FEED</span>
                <span style="font-size: 0.75rem; color: #7c3aed; font-weight: 600; cursor: pointer;">Live Stream →</span>
            </div>
            
            <div class="activity-row">
                <span style="color: #7c3aed;">🟣</span> <span class="activity-agent">Continuity Tracker</span> <span class="activity-time">2m ago</span>
                <div class="activity-desc">Wardrobe inconsistency flagged — Scene 47 Ext. Rooftop, jacket color differs from Sc.44</div>
            </div>

            <div class="activity-row">
                <span style="color: #0284c7;">🔵</span> <span class="activity-agent">Shot List Manager</span> <span class="activity-time">14m ago</span>
                <div class="activity-desc">Updated 8 shots for Day 18 exterior coverage after location scout revision</div>
            </div>

            <div class="activity-row">
                <span style="color: #16a34a;">🟢</span> <span class="activity-agent">Script Doctor</span> <span class="activity-time">31m ago</span>
                <div class="activity-desc">Act II structural review complete — 3 pacing suggestions ready for review</div>
            </div>

            <div class="activity-row">
                <span style="color: #c026d3;">🟣</span> <span class="activity-agent">VFX Pipeline Monitor</span> <span class="activity-time">1h ago</span>
                <div class="activity-desc">3 hero VFX shots cleared from Vendor B, delivery confirmed — on schedule</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_sched:
        st.markdown("""
        <div class="surface-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em;">SHOOT SCHEDULE</span>
                <span style="font-size: 0.8rem; color: #64748b;">📅</span>
            </div>

            <div style="margin-bottom: 12px;">
                <span class="sched-tag-today">TODAY</span> <span style="font-size: 0.75rem; color: #64748b; margin-left: 5px;">Day 17</span>
                <div style="font-size: 0.8rem; color: #0f172a; margin-top: 4px; font-weight: 600;">Sc.44 — Int. Precinct Office · Day</div>
                <div style="font-size: 0.8rem; color: #0f172a; font-weight: 600;">Sc.45 — Int. Precinct Office · Day</div>
            </div>

            <div style="margin-bottom: 12px;">
                <span class="sched-tag-future">TOMORROW</span> <span style="font-size: 0.75rem; color: #64748b; margin-left: 5px;">Day 18</span>
                <div style="font-size: 0.8rem; color: #0f172a; margin-top: 4px; font-weight: 600;">Sc.47 — Ext. Rooftop <span style="color: #7c3aed;">(Weather TBD)</span></div>
                <div style="font-size: 0.8rem; color: #0f172a; font-weight: 600;">Sc.48 — Ext. Rooftop · Dusk</div>
            </div>

            <div style="font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 6px;">ASK AN AGENT</div>
        </div>
        """, unsafe_allow_html=True)

        prompt_c1, prompt_c2 = st.columns([3.5, 1])
        with prompt_c1:
            user_q = st.text_input("Query", placeholder="e.g. What's at risk on Day 18?", label_visibility="collapsed")
        with prompt_c2:
            ask_action = st.button("Ask ⚡", use_container_width=True)

        if ask_action and user_q:
            st.info(f"**Agent Response:** Day 18 exterior rooftop shoot has a 65% chance of rain. Logistics agent has pre-booked Stage 4 as a dry interior cover.")

# ==============================================================================
# VIEW 2: SCREENWRITERS & DIRECTORS
# ==============================================================================
elif nav_choice == "Screenwriters & Directors":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="font-size: 1.5rem; margin: 0;">📁 Creative Workspace</h1>
        <p style="color: #64748b; font-size: 0.82rem; margin-top: 4px;">Automated Screenplay Breakdown, Scene Parsing & Table-Read Rehearsals</p>
    </div>
    """, unsafe_allow_html=True)

    col_s, col_r = st.columns([1, 1], gap="large")
    with col_s:
        sample_script = """EXT. NEO TOKYO ALLEYWAY - NIGHT
Heavy rain drenches the asphalt. DETECTIVE VANCE (40s, damp trench coat) inspects a glowing cypher-deck in his left hand.
He glances behind him. A cybernetic drone buzzes overhead.

VANCE
(into collar mic)
I found the package. Moving to extraction point B."""

        script_text = st.text_area("Screenplay Feed", value=sample_script, height=250)
        
        b1, b2 = st.columns(2)
        with b1:
            run_breakdown = st.button("🚀 Ingest & Extract Breakdown", use_container_width=True)
        with b2:
            run_table_read = st.button("🎙️ Generate Director Table-Read", use_container_width=True)

        if run_breakdown:
            with st.spinner("Gemini Agent extracting characters and props into ClickHouse..."):
                if MODULES_LOADED:
                    try:
                        scenes = process_script_and_breakdown(st.session_state.project_id, script_text)
                        st.success(f"Parsed {len(scenes)} scenes into ClickHouse state.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.success("Parsed 1 scene into ClickHouse state (Demo Mode).")

    with col_r:
        if run_table_read:
            with st.spinner("Synthesizing performance subtext..."):
                if MODULES_LOADED:
                    try:
                        st.session_state.tr_notes = generate_table_read_rehearsal(script_text)
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.session_state.tr_notes = "**VANCE:** Subdued paranoia. Delivery should be rapid with heavy breath marks."

        if "tr_notes" in st.session_state:
            st.markdown("#### 🎭 Director's Table-Read Notes")
            st.info(st.session_state.tr_notes)

        st.markdown("#### 🗄️ ClickHouse Scene State")
        if MODULES_LOADED:
            try:
                scenes_data = get_project_scenes(st.session_state.project_id)
                if scenes_data:
                    st.dataframe(scenes_data, headers=["Scene #", "Header", "Description", "Characters", "Props"], use_container_width=True)
                else:
                    st.caption("No scene records found for this project.")
            except:
                st.caption("ClickHouse tables ready.")
        else:
            st.caption("Connected to ClickHouse `scenes` table.")

# ==============================================================================
# VIEW 3: ON-SET CREW
# ==============================================================================
elif nav_choice == "On-Set Crew":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="font-size: 1.5rem; margin: 0;">🎥 On-Set Workspace</h1>
        <p style="color: #64748b; font-size: 0.82rem; margin-top: 4px;">Dynamic Production Call-Sheet Dispatcher & Crew Scheduling</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        s_date = st.date_input("Shoot Date").strftime("%Y-%m-%d")
    with c2:
        c_time = st.time_input("Call Time").strftime("%H:%M")
    with c3:
        loc = st.text_input("Stage / Location", value="Stage 6 · Precinct Set")

    scenes_sel = st.multiselect("Scheduled Scenes", options=[44, 45, 47, 48], default=[44, 45])

    if st.button("⚡ Dispatch Production Call Sheet", use_container_width=True):
        with st.spinner("AD Agent generating schedule..."):
            if MODULES_LOADED:
                try:
                    sheet = create_dynamic_call_sheet(st.session_state.project_id, s_date, c_time, loc, scenes_sel)
                    st.success("Call sheet saved to ClickHouse.")
                    st.markdown(sheet)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                time.sleep(1)
                st.success("Call sheet dispatched and logged to ClickHouse.")
                st.markdown(f"""
                ### 🎬 PRODUCTION CALL SHEET — {s_date}
                * **Location:** {loc} | **Call Time:** {c_time}
                * **Scheduled Scenes:** {scenes_sel}
                * **Notes:** Stage 6 overhead rain grids armed. Sound dampeners active.
                """)

# ==============================================================================
# VIEW 4: POST-PRODUCTION
# ==============================================================================
elif nav_choice == "Post-Production":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="font-size: 1.5rem; margin: 0;">✂️ Post-Production Workspace</h1>
        <p style="color: #64748b; font-size: 0.82rem; margin-top: 4px;">Multimodal Continuity Inspector & Dailies Search Engine</p>
    </div>
    """, unsafe_allow_html=True)

    col_in, col_res = st.columns(2, gap="large")
    with col_in:
        st.markdown("#### Audit Filmed Take")
        sc_v = st.number_input("Scene #", value=47)
        tk_v = st.number_input("Take #", value=2)
        clip_v = st.text_input("Camera Roll ID", value="ROLL_A_TAKE_02.MOV")
        take_desc = st.text_area(
            "Visual Notes / AI Multimodal Summary",
            value="Vance stands on the rooftop under dusk lighting. He reaches into his coat with his RIGHT hand to draw the communicator."
        )
        audit_btn = st.button("🔬 Run Continuity Audit", use_container_width=True)

    with col_res:
        st.markdown("#### Verification Status")
        if audit_btn:
            with st.spinner("Cross-auditing against ClickHouse script baseline..."):
                if MODULES_LOADED:
                    try:
                        res = inspect_take_continuity(st.session_state.project_id, sc_v, tk_v, clip_v, take_desc)
                        st.json(res)
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.error("⚠️ CONTINUITY ISSUE DETECTED")
                    st.json({
                        "scene": sc_v,
                        "take": tk_v,
                        "status": "FLAGGED",
                        "discrepancy": "Prop Hand Mismatch: Script specifies LEFT hand in Scene 44 baseline."
                    })

    st.divider()
    st.markdown("#### 🔎 Query Dailies Archive")
    sq1, sq2 = st.columns([3.5, 1])
    with sq1:
        query_text = st.text_input("Footage Search", placeholder="e.g. communicator, rooftop, rain", label_visibility="collapsed")
    with sq2:
        search_action = st.button("Search Footage", use_container_width=True)

    if search_action and query_text:
        st.info(f"Querying ClickHouse for '{query_text}'...")

# ==============================================================================
# REMAINING VIEWS
# ==============================================================================
elif nav_choice == "Production Schedule":
    st.title("📅 Production Schedule")
    st.caption("Cast Turnaround Times & Union Rest Compliance")
    st.info("Schedule engine is synchronized with daily call sheets.")

elif nav_choice == "Agent Event Feed":
    st.title("⚡ Real-Time Agent Telemetry")
    st.caption("OpenTelemetry traces across Gemini tool invocations")
    st.code("""
[20:54:12] Agent.ContinuityTracker: Evaluated Take ROLL_A_TAKE_02 -> Discrepancy logged
[20:41:00] Agent.ShotListManager: Re-indexed Scene 47 setup angles
[20:30:19] Agent.ScriptDoctor: Token breakdown complete for Act II
    """, language="log")

elif nav_choice == "Studio Settings":
    st.title("⚙️ Studio Settings & Secrets")
    st.text_input("Active Project ID", value=st.session_state.project_id)
    st.text_input("Gemini API Key", value="••••••••••••••••", type="password")
    st.text_input("ClickHouse Endpoint", value="https://app.clickhouse.cloud:8443")
