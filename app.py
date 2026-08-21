import streamlit as st
import os
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="CINEAGENT | Production AI Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SAFE IMPORTS FROM TEAM MODULES ---
try:
    from tools.database import init_tables, get_project_scenes, get_call_sheets, search_dailies
    from agents.pre_prod import process_script_and_breakdown, generate_table_read_rehearsal
    from agents.on_set import create_dynamic_call_sheet
    from agents.post_prod import inspect_take_continuity, query_project_footage
    MODULES_LOADED = True
except ImportError:
    MODULES_LOADED = False

# --- SESSION STATE ---
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Overview"
if "project_id" not in st.session_state:
    st.session_state.project_id = "PRJ_MERIDIAN_01"
if "db_connected" not in st.session_state:
    st.session_state.db_connected = False
if "agent_chat_history" not in st.session_state:
    st.session_state.agent_chat_history = []

# --- ROYAL BLUE, GOLD & PURPLE THEME (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Dark Royal Blue Base */
    .stApp {
        background-color: #060913 !important;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #080d1a !important;
        border-right: 1px solid #172033;
    }

    /* Cinematic Brand Logo */
    .brand-title {
        font-family: 'Cinzel', serif;
        color: #f59e0b;
        letter-spacing: 0.18em;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .brand-sub {
        font-family: 'JetBrains Mono', monospace;
        color: #8b5cf6;
        font-size: 0.65rem;
        letter-spacing: 0.25em;
        margin-top: -2px;
        margin-bottom: 15px;
    }

    /* Top Phase Banner */
    .phase-banner {
        background: linear-gradient(90deg, #0f172a 0%, #15102a 50%, #1e1338 100%);
        border: 1px solid #2d2254;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .phase-badge {
        background: #f59e0b22;
        color: #fbbf24;
        border: 1px solid #f59e0b55;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-left: 10px;
    }

    /* Top Metric Stat Cards */
    .metric-box {
        background: #0b1120;
        border: 1px solid #1a233a;
        border-radius: 10px;
        padding: 16px 18px;
        min-height: 125px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-box:hover {
        border-color: #7c3aed;
        transform: translateY(-2px);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .metric-val {
        font-size: 1.85rem;
        font-weight: 700;
        color: #ffffff;
        margin: 4px 0;
    }
    .metric-val span {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 400;
    }
    .metric-footer-green {
        color: #34d399;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .metric-footer-gold {
        color: #fbbf24;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* Agent Zone Containers */
    .zone-card {
        background: #090e1c;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #151e33;
        margin-bottom: 20px;
        min-height: 400px;
    }
    .zone-creative {
        border-top: 3px solid #f59e0b;
    }
    .zone-onset {
        border-top: 3px solid #38bdf8;
    }
    .zone-post {
        border-top: 3px solid #a855f7;
    }

    .zone-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .zone-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #f8fafc;
    }
    .zone-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 16px;
    }
    .zone-pill-gold {
        background: #f59e0b1a;
        color: #fbbf24;
        border: 1px solid #f59e0b44;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
    }
    .zone-pill-blue {
        background: #0284c71a;
        color: #38bdf8;
        border: 1px solid #0284c744;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
    }
    .zone-pill-purple {
        background: #7c3aed1a;
        color: #c084fc;
        border: 1px solid #7c3aed44;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
    }

    /* Agent Row Item */
    .agent-row {
        padding: 8px 10px;
        border-radius: 6px;
        background: #0e1526;
        margin-bottom: 8px;
        border: 1px solid #162035;
    }
    .agent-row-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .agent-row-desc {
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .agent-alert-gold {
        color: #fbbf24;
        font-size: 0.72rem;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .agent-alert-blue {
        color: #38bdf8;
        font-size: 0.72rem;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .agent-alert-purple {
        color: #c084fc;
        font-size: 0.72rem;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Activity Feed & Schedule Section */
    .feed-card {
        background: #090e1c;
        border: 1px solid #172033;
        border-radius: 10px;
        padding: 16px;
    }
    .feed-item {
        padding: 10px 0;
        border-bottom: 1px solid #131b2c;
    }
    .feed-item:last-child {
        border-bottom: none;
    }
    .feed-actor {
        font-weight: 600;
        font-size: 0.8rem;
        color: #f1f5f9;
    }
    .feed-time {
        font-size: 0.7rem;
        color: #64748b;
        margin-left: 6px;
    }
    .feed-msg {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 2px;
    }

    /* Schedule Pills */
    .day-pill-today {
        background: #05966922;
        color: #34d399;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .day-pill-tmrw {
        background: #d9770622;
        color: #fbbf24;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .day-pill-later {
        background: #6d28d922;
        color: #c084fc;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }

    /* Custom Streamlit Buttons */
    div.stButton > button {
        background-color: #111a2e;
        color: #f1f5f9;
        border: 1px solid #23304d;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #f59e0b;
        color: #fbbf24;
        background-color: #17233d;
    }
    div.stButton > button:active {
        border-color: #8b5cf6;
        color: #c084fc;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">🎬 CINEAGENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">PRODUCTION AI OS</div>', unsafe_allow_html=True)

    st.caption("NAVIGATION")
    nav_choice = st.radio(
        "Navigation",
        [
            "Overview",
            "Screenwriters & Directors",
            "On-Set Crew",
            "Post-Production",
            "Schedule",
            "Activity Feed",
            "Settings"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("ACTIVE PROJECT")
    st.markdown("**'The Last Meridian'**")
    st.caption("Feature · Sci-Fi Drama")
    st.progress(0.41, text="Production: 41%")

    st.divider()
    st.caption("INFRASTRUCTURE")
    if st.button("⚡ ClickHouse Live Sync", use_container_width=True):
        if MODULES_LOADED:
            success, msg = init_tables()
            st.session_state.db_connected = success
            if success:
                st.toast("ClickHouse Database Active", icon="🟣")
            else:
                st.error(msg)
        else:
            st.session_state.db_connected = True
            st.toast("Demo Mode Active", icon="🟡")

    db_status = "🟢 ClickHouse Online" if st.session_state.db_connected else "🟡 ClickHouse Ready"
    st.caption(f"Status: `{db_status}`")

# ==============================================================================
# VIEW ROUTER
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. OVERVIEW DASHBOARD VIEW
# ------------------------------------------------------------------------------
if nav_choice == "Overview":
    # Top Header
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #ffffff;">Production Dashboard</h2>
            <p style="margin: 0; font-size: 0.78rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">Day 17 of 42 · Principal Photography · Aug 21, 2026</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Phase Banner
    st.markdown("""
    <div class="phase-banner">
        <div style="display: flex; align-items: center;">
            <span style="color: #fbbf24; font-size: 0.9rem; margin-right: 6px;">●</span>
            <span style="font-weight: 700; font-size: 0.85rem; letter-spacing: 0.05em; color: #ffffff;">PHASE: PRINCIPAL PHOTOGRAPHY</span>
            <span class="phase-badge">ON SCHEDULE</span>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
            UNIT A · Stage 6 · Studio City &nbsp;|&nbsp; Director: A. Fontaine &nbsp;|&nbsp; DP: R. Osei
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Stat Strip
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Days in Production</div>
            <div class="metric-val">17 <span>of 42 days</span></div>
            <div class="metric-footer-green">▲ 2 days ahead of schedule</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Scenes Completed</div>
            <div class="metric-val">63 <span>of 118 scenes</span></div>
            <div class="metric-footer-green">53% through principal photography</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Budget Utilized</div>
            <div class="metric-val" style="color: #fbbf24;">$2.4M <span>of $5.8M total</span></div>
            <div class="metric-footer-gold">41% — on track</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Active Agents</div>
            <div class="metric-val" style="color: #c084fc;">6 <span>of 12 available</span></div>
            <div class="metric-footer-green">● All systems nominal</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

    # 3 Agent Zone Columns
    z1, z2, z3 = st.columns(3)

    # Zone 1: Creative
    with z1:
        st.markdown("""
        <div class="zone-card zone-creative">
            <div class="zone-header">
                <span class="zone-title">📁 Creative</span>
                <span class="zone-pill-gold">2 active</span>
            </div>
            <div class="zone-sub">Story development & creative vision</div>
            
            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #fbbf24;">● Script Doctor</span>
                    <span style="color: #64748b;">3</span>
                </div>
                <div class="agent-row-desc">Scene-level analysis, dialogue quality, and structural feedback for each act</div>
                <div class="agent-alert-gold">↳ Reviewed Act II pacing — 3 notes pending</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #f59e0b;">● Story Arc Analyzer</span>
                    <span style="color: #64748b;">7</span>
                </div>
                <div class="agent-row-desc">Character journey continuity & thematic motif consistency tracking</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #64748b;">○ Dialogue Coach</span>
                    <span style="color: #64748b;">-</span>
                </div>
                <div class="agent-row-desc">Subtext, cadence, and multi-speaker rehearsal generation</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #64748b;">○ Pitch Deck Builder</span>
                    <span style="color: #64748b;">1</span>
                </div>
                <div class="agent-row-desc">Generates visual lookbooks & executive scene teasers</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ Open Creative Workspace", key="btn_creative_ws", use_container_width=True):
            st.session_state.active_nav = "Screenwriters & Directors"
            st.rerun()

    # Zone 2: On-Set
    with z2:
        st.markdown("""
        <div class="zone-card zone-onset">
            <div class="zone-header">
                <span class="zone-title">🎥 On-Set</span>
                <span class="zone-pill-blue">3 active</span>
            </div>
            <div class="zone-sub">Real-time production coordination</div>
            
            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #38bdf8;">● Continuity Tracker</span>
                    <span style="color: #64748b;">5</span>
                </div>
                <div class="agent-row-desc">Prop, costume, and blocking continuity logs per scene</div>
                <div class="agent-alert-blue">↳ Flagged wardrobe mismatch — Sc.47 Ext. Rooftop</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #38bdf8;">● Shot List Manager</span>
                    <span style="color: #64748b;">12</span>
                </div>
                <div class="agent-row-desc">Tracks camera setups, lens choices, and scene coverage</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #f59e0b;">● Logistics Coordinator</span>
                    <span style="color: #64748b;">4</span>
                </div>
                <div class="agent-row-desc">Dynamic call sheet generation & weather contingencies</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #64748b;">○ Safety Monitor</span>
                    <span style="color: #64748b;">-</span>
                </div>
                <div class="agent-row-desc">Stunt compliance & environmental safety checklist verification</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ Open On-Set Workspace", key="btn_onset_ws", use_container_width=True):
            st.session_state.active_nav = "On-Set Crew"
            st.rerun()

    # Zone 3: Post
    with z3:
        st.markdown("""
        <div class="zone-card zone-post">
            <div class="zone-header">
                <span class="zone-title">✂️ Post</span>
                <span class="zone-pill-purple">2 active</span>
            </div>
            <div class="zone-sub">Editorial, VFX, and delivery pipeline</div>
            
            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #fbbf24;">● Edit Assistant</span>
                    <span style="color: #64748b;">8</span>
                </div>
                <div class="agent-row-desc">Dailies tagging, metadata sync, and timeline assembly</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #64748b;">○ Color Grade Advisor</span>
                    <span style="color: #64748b;">2</span>
                </div>
                <div class="agent-row-desc">LUT consistency auditing & exposure balance checks across takes</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #c084fc;">● VFX Pipeline Monitor</span>
                    <span style="color: #64748b;">6</span>
                </div>
                <div class="agent-row-desc">Tracks shot status across vendors, flags delays, manages deliverables</div>
                <div class="agent-alert-purple">↳ 3 hero shots cleared from Vendor B — on schedule</div>
            </div>

            <div class="agent-row">
                <div class="agent-row-header">
                    <span style="color: #64748b;">○ Sound Mix Advisor</span>
                    <span style="color: #64748b;">1</span>
                </div>
                <div class="agent-row-desc">Dialogue isolation & ambient foley score synthesis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ Open Post Workspace", key="btn_post_ws", use_container_width=True):
            st.session_state.active_nav = "Post-Production"
            st.rerun()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Bottom Split: Agent Activity & Shoot Schedule
    col_act, col_sched = st.columns([1.2, 0.8], gap="medium")

    with col_act:
        st.markdown("""
        <div class="feed-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #f8fafc; text-transform: uppercase; letter-spacing: 0.05em;">AGENT ACTIVITY</span>
                <span style="font-size: 0.75rem; color: #f59e0b; font-weight: 600; cursor: pointer;">View all →</span>
            </div>
            
            <div class="feed-item">
                <span style="color: #fbbf24;">⚠️</span> <span class="feed-actor">Continuity Tracker</span> <span class="feed-time">2m ago</span>
                <div class="feed-msg">Wardrobe inconsistency flagged — Scene 47 Ext. Rooftop, jacket color differs from Sc.44</div>
            </div>

            <div class="feed-item">
                <span style="color: #38bdf8;">ℹ️</span> <span class="feed-actor">Shot List Manager</span> <span class="feed-time">14m ago</span>
                <div class="feed-msg">Updated 8 shots for Day 18 exterior coverage after location scout revision</div>
            </div>

            <div class="feed-item">
                <span style="color: #34d399;">✓</span> <span class="feed-actor">Script Doctor</span> <span class="feed-time">31m ago</span>
                <div class="feed-msg">Act II structural review complete — 3 pacing suggestions pending director approval</div>
            </div>

            <div class="feed-item">
                <span style="color: #c084fc;">✓</span> <span class="feed-actor">VFX Pipeline Monitor</span> <span class="feed-time">1h ago</span>
                <div class="feed-msg">3 hero VFX shots cleared from Vendor B, delivery confirmed — on schedule</div>
            </div>

            <div class="feed-item">
                <span style="color: #fbbf24;">⚠️</span> <span class="feed-actor">Logistics Coordinator</span> <span class="feed-time">3h ago</span>
                <div class="feed-msg">Rain alert Day 18 — alternate interior location (Stage 4) suggested and available</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_sched:
        st.markdown("""
        <div class="feed-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #f8fafc; text-transform: uppercase; letter-spacing: 0.05em;">SHOOT SCHEDULE</span>
                <span style="font-size: 0.8rem; color: #64748b;">📅</span>
            </div>

            <div style="margin-bottom: 10px;">
                <span class="day-pill-today">TODAY</span> <span style="font-size: 0.72rem; color: #64748b;">Day 17</span>
                <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">Sc.44 — Int. Precinct Office · Day</div>
                <div style="font-size: 0.78rem; color: #cbd5e1;">Sc.45 — Int. Precinct Office · Day</div>
            </div>

            <div style="margin-bottom: 10px;">
                <span class="day-pill-tmrw">TOMORROW</span> <span style="font-size: 0.72rem; color: #64748b;">Day 18</span>
                <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">Sc.47 — Ext. Rooftop <span style="color: #fbbf24;">⚠️ Weather TBD</span></div>
                <div style="font-size: 0.78rem; color: #cbd5e1;">Sc.48 — Ext. Rooftop · Dusk</div>
            </div>

            <div style="margin-bottom: 14px;">
                <span class="day-pill-later">THURSDAY</span> <span style="font-size: 0.72rem; color: #64748b;">Day 19</span>
                <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">Sc.52 — Int. Apartment · Night</div>
            </div>

            <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 6px;">ASK AN AGENT</div>
        </div>
        """, unsafe_allow_html=True)

        prompt_c1, prompt_c2 = st.columns([3.5, 1])
        with prompt_c1:
            user_agent_q = st.text_input("Ask Agent", placeholder="e.g. What's at risk on Day 18?", label_visibility="collapsed")
        with prompt_c2:
            ask_btn = st.button("Ask ⚡", use_container_width=True)

        if ask_btn and user_agent_q:
            st.info(f"**Agent Response:** Day 18 exterior rooftop shoot has a 65% chance of rain. Logistics agent has pre-booked Stage 4 as a dry interior cover.")

# ------------------------------------------------------------------------------
# 2. SCREENWRITERS & DIRECTORS WORKSPACE
# ------------------------------------------------------------------------------
elif nav_choice == "Screenwriters & Directors":
    st.markdown("""
    <div style="margin-bottom: 15px;">
        <h2 style="color: #fbbf24; font-size: 1.4rem; font-weight: 700; margin: 0;">📁 Creative Workspace — Screenwriters & Directors</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin: 0;">Automated Screenplay Breakdown, Scene Extraction & Table-Read Rehearsals</p>
    </div>
    """, unsafe_allow_html=True)

    col_script, col_output = st.columns([1, 1], gap="large")

    with col_script:
        sample_script = """EXT. NEO TOKYO ALLEYWAY - NIGHT
Heavy rain drenches the asphalt. DETECTIVE VANCE (40s, damp trench coat) inspects a glowing cypher-deck in his left hand.
He glances behind him. A cybernetic drone buzzes overhead.

VANCE
(into collar mic)
I found the package. Moving to extraction point B."""

        script_text = st.text_area("Screenplay Feed", value=sample_script, height=240)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            run_breakdown = st.button("🚀 Ingest & Extract Breakdown", use_container_width=True, type="primary")
        with c_btn2:
            run_table_read = st.button("🎙️ Generate Director Table-Read", use_container_width=True)

        if run_breakdown:
            with st.spinner("Gemini Agent extracting characters, props, and scene graph..."):
                if MODULES_LOADED:
                    try:
                        scenes = process_script_and_breakdown(st.session_state.project_id, script_text)
                        st.success(f"Extracted {len(scenes)} scenes to ClickHouse.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.success("Extracted 1 scene into ClickHouse state (Demo Mode).")

    with col_output:
        if run_table_read:
            with st.spinner("Generating subtext annotations..."):
                if MODULES_LOADED:
                    try:
                        notes = generate_table_read_rehearsal(script_text)
                        st.session_state.tr_notes = notes
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.session_state.tr_notes = "**VANCE:** Subdued paranoia. Keep dialogue hurried and whisper-close to mic."

        if "tr_notes" in st.session_state:
            st.markdown("#### 🎭 Rehearsal Subtext")
            st.info(st.session_state.tr_notes)

        st.markdown("#### 🗄️ ClickHouse Scene Graph")
        if MODULES_LOADED:
            try:
                scenes_data = get_project_scenes(st.session_state.project_id)
                if scenes_data:
                    st.dataframe(scenes_data, headers=["Scene #", "Header", "Description", "Characters", "Props"], use_container_width=True)
                else:
                    st.caption("No scene breakdown stored for this project yet.")
            except:
                st.caption("ClickHouse tables ready to receive data.")
        else:
            st.caption("Connected to ClickHouse `scenes` table.")

# ------------------------------------------------------------------------------
# 3. ON-SET CREW WORKSPACE
# ------------------------------------------------------------------------------
elif nav_choice == "On-Set Crew":
    st.markdown("""
    <div style="margin-bottom: 15px;">
        <h2 style="color: #38bdf8; font-size: 1.4rem; font-weight: 700; margin: 0;">🎥 On-Set Workspace — Crew & Call Sheets</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin: 0;">Dynamic Production Call-Sheet Dispatcher & Daily Schedule Sync</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        s_date = st.date_input("Shoot Date").strftime("%Y-%m-%d")
    with col2:
        c_time = st.time_input("Call Time").strftime("%H:%M")
    with col3:
        loc = st.text_input("Stage / Location", value="Stage 6 · Precinct Set")

    scenes_selected = st.multiselect("Scenes Scheduled for Shoot", options=[44, 45, 47, 48], default=[44, 45])

    if st.button("⚡ Dispatch Production Call Sheet", type="primary", use_container_width=True):
        with st.spinner("AD Agent calculating schedule and equipment needs..."):
            if MODULES_LOADED:
                try:
                    sheet = create_dynamic_call_sheet(st.session_state.project_id, s_date, c_time, loc, scenes_selected)
                    st.success("Call sheet logged to ClickHouse.")
                    st.markdown(sheet)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                time.sleep(1)
                st.success("Call sheet dispatched and synced to ClickHouse.")
                st.markdown(f"""
                ### 🎬 CALL SHEET — {s_date}
                * **Location:** {loc} | **Call Time:** {c_time}
                * **Scheduled Scenes:** {scenes_selected}
                * **Department Notes:** Sound requires rain dampeners on Stage 6 overhead grids.
                """)

# ------------------------------------------------------------------------------
# 4. POST-PRODUCTION WORKSPACE
# ------------------------------------------------------------------------------
elif nav_choice == "Post-Production":
    st.markdown("""
    <div style="margin-bottom: 15px;">
        <h2 style="color: #c084fc; font-size: 1.4rem; font-weight: 700; margin: 0;">✂️ Post-Production Workspace — Dailies & Continuity</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin: 0;">Multimodal Continuity Inspector & Searchable Dailies Library</p>
    </div>
    """, unsafe_allow_html=True)

    c_in, c_res = st.columns(2, gap="large")

    with c_in:
        st.markdown("#### Audit Filmed Take")
        sc_val = st.number_input("Scene #", value=47)
        tk_val = st.number_input("Take #", value=2)
        clip_val = st.text_input("Camera Roll ID", value="A002_C014_RAW.MOV")
        take_desc = st.text_area(
            "Take Visual Notes / Multimodal Video Summary",
            value="Vance stands on the rooftop under dusk lighting. He reaches into his jacket with his RIGHT hand to draw the communicator."
        )
        run_audit = st.button("🔬 Audit Against Script Spec", type="primary", use_container_width=True)

    with c_res:
        st.markdown("#### Inspector Verdict")
        if run_audit:
            with st.spinner("Post Agent cross-referencing take against script specs in ClickHouse..."):
                if MODULES_LOADED:
                    try:
                        res = inspect_take_continuity(st.session_state.project_id, sc_val, tk_val, clip_val, take_desc)
                        st.json(res)
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    time.sleep(1)
                    st.error("⚠️ CONTINUITY ISSUE DETECTED")
                    st.json({
                        "scene": sc_val,
                        "take": tk_val,
                        "status": "FLAGGED",
                        "issue": "Prop Hand Mismatch: Script specifies LEFT hand in Scene 44 baseline."
                    })

    st.divider()
    st.markdown("#### 🔎 Query Dailies Archive")
    q_col1, q_col2 = st.columns([3.5, 1])
    with q_col1:
        search_query = st.text_input("Footage Query", placeholder="e.g. communicator, dusk, right hand", label_visibility="collapsed")
    with q_col2:
        search_exec = st.button("Search Dailies", use_container_width=True)

    if search_exec and search_query:
        st.info(f"Querying ClickHouse for '{search_query}'...")

# ------------------------------------------------------------------------------
# 5. REMAINING VIEWS (Schedule, Activity Feed, Settings)
# ------------------------------------------------------------------------------
elif nav_choice == "Schedule":
    st.title("📅 Production Master Schedule")
    st.caption("Timeline Gantt & Union Rest Period Verification")
    st.info("Schedule module is active and synced with daily call sheets.")

elif nav_choice == "Activity Feed":
    st.title("⚡ Real-Time Agent Telemetry Feed")
    st.caption("Live OpenTelemetry & Multi-Agent Event Stream")
    st.code("""
[14:22:10] Agent.ContinuityTracker: Ingested take A002_C014 -> flagged hand mismatch
[14:15:02] Agent.ShotListManager: Re-indexed Day 18 camera setups
[13:58:44] Agent.ScriptDoctor: Scene 44 token analysis complete
    """, language="log")

elif nav_choice == "Settings":
    st.title("⚙️ Studio Settings & Secrets")
    st.text_input("Active Project ID", value=st.session_state.project_id)
    st.text_input("Gemini API Key", value="••••••••••••••••", type="password")
    st.text_input("ClickHouse Endpoint", value="https://app.clickhouse.cloud:8443")
