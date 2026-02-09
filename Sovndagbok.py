# © 2026 Asbjørn Hval Bergestuen
# Licensed under the MIT License. See the LICENSE file for details.

import json
import os
from datetime import datetime, time, date, timedelta
from typing import Dict, Any, List, Optional

import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import streamlit as st  # type: ignore

# --- CONFIG ---
st.set_page_config(page_title="Søvndagbok", layout="wide", page_icon="🌙")

# --- CUSTOM CSS (NAV / Aksel Style) ---
def render_custom_css():
    st.markdown("""
<style>
    /* 1. Global Light Theme Override */
    [data-testid="stAppViewContainer"] {
        background-color: #F1F1F1;
        color: #262626;
    }
    
    /* 2. Text Color Reset */
    h1, h2, h3, p, span, div, label, li {
        color: #262626 !important;
    }
    h1, [data-testid="stMetricValue"] {
        color: #0067C5 !important;
    }
    

    /* 3. Button Styles (Neutral Gray) */
    .stButton > button {
        background-color: #E0E0E0 !important;
        color: #262626 !important;
        border: 1px solid #B0B0B0 !important;
        border-radius: 4px !important;
    }
    .stButton > button:hover {
        background-color: #D0D0D0 !important;
        color: #262626 !important;
        border-color: #A0A0A0 !important;
    }
    .stButton > button:active, .stButton > button:focus {
        background-color: #C0C0C0 !important;
        color: #262626 !important;
        border-color: #909090 !important;
        box-shadow: none !important;
    }
    .stButton > button p {
        color: #262626 !important; /* Force text color */
    }

    /* 4. Input Fields */
    input, textarea, select {
        background-color: white !important;
        color: #262626 !important;
    }
    
    /* 5. The Wrapper Divs for Inputs (Borders & Background) */
    [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
        background-color: white !important;
        border-color: #78706A !important;
        border: 1px solid #78706A !important;
    }
    

    /* 6. The Text Inside Wrapper Divs */
    [data-baseweb="input"] input, [data-baseweb="select"] span, [data-baseweb="textarea"] textarea {
        color: #262626 !important;
        -webkit-text-fill-color: #262626 !important; /* Safari fix */
        caret-color: #262626 !important;
    }

    /* 6b. Number Input: SIMPLIFIED & EXPLICIT */
    [data-testid="stNumberInput"] > div {
        border: 1px solid #262626 !important;
        border-radius: 4px !important;
        background-color: white !important;
    }
    
    [data-testid="stNumberInput"] input {
        border: none !important;
        background-color: transparent !important;
    }

    /* 7. Dropdown Options Menu */
    ul[data-baseweb="menu"] {
        background-color: white !important;
    }
    ul[data-baseweb="menu"] li {
        background-color: white !important;
        color: #262626 !important;
    }

    /* 8. Selected Option in Menu */
    ul[data-baseweb="menu"] li[aria-selected="true"] {
        background-color: #E6F0FF !important; /* Light blue highlight */
    }

    /* 9. Containers */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background-color: white;
        border: 1px solid #E6E6E6;
    }


    /* 10. Sidebar */
    [data-testid="stSidebar"] {
        background-color: #d4edda !important; /* Success Green */
        border-right: 1px solid #E0E0E0;
    }

    /* 11. Print Specific Styles */
    @media print {
        /* Nullstill marginer på selve siden */
        @page {
            margin: 0.5cm; /* Liten marg rundt hele arket */
        }
        
        /* Tving hovedcontainer helt til toppen */
        .main .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-top: 0 !important;
            max-width: 100% !important;
        }
        
        /* Skjul header fullstendig */
        header {
            display: none !important;
            height: 0 !important;
        }
        
        /* Skjul Streamlits innebygde padding-elementer */
        div[data-testid="stVerticalBlock"] > div:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Juster overskrifter for print */
        h1, h2, h3 {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- DATA MANAGER (Model) ---
class SleepDataManager:
    def __init__(self):
        if "data" not in st.session_state:
            st.session_state.data = None
        if "filepath" not in st.session_state:
            st.session_state.filepath = None
        
        # Init file explorer state
        if "current_browser_dir" not in st.session_state:
            st.session_state.current_browser_dir = os.getcwd()

    def create_new_log(self, name, directory, filename="min_sovndagbok.json"):
        full_path = os.path.join(directory, filename)
        new_data = {
            "meta": {
                "name": name,
                "created": str(date.today()),
                "version": "2.0",
                "settings": {
                    "target_wake": "07:00:00",
                    "window_hours": 6.0
                },
                "window_history": [
                    {
                        "start_date": str(date.today()),
                        "end_date": None,
                        "target_wake": "07:00:00",
                        "window_hours": 6.0
                    }
                ]
            },
            "entries": {}
        }
        if os.path.exists(full_path):
             st.warning(f"Filen {full_path} finnes allerede. Velg et annet navn eller mappe.")
             return False

        self._save_to_disk(full_path, new_data)
        self.load_log(full_path)
        return True

    def load_log(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    st.session_state.data = json.load(f)
                st.session_state.filepath = filepath
                return True
            except json.JSONDecodeError:
                st.error("Filen er ikke gyldig JSON.")
                return False
        return False

    def save_window_history(self, new_history):
        if st.session_state.data is None:
             return
        st.session_state.data["meta"]["window_history"] = new_history
        self._save_to_disk(st.session_state.filepath, st.session_state.data)

    def get_window_history(self):
        if st.session_state.data is None:
             return []
        
        meta = st.session_state.data["meta"]
        # Handle legacy files (init history if missing)
        if "window_history" not in meta:
            current_settings = meta.get("settings", {"target_wake": "07:00:00", "window_hours": 6.0})
            st.session_state.data["meta"]["window_history"] = [{
                "start_date": str(date.today()),
                "end_date": None,
                "target_wake": current_settings.get("target_wake", "07:00:00"),
                "window_hours": current_settings.get("window_hours", 6.0)
            }]
            # Save immediately to fix structure
            self._save_to_disk(st.session_state.filepath, st.session_state.data)

        return st.session_state.data["meta"]["window_history"]

    def save_settings(self, target_wake, window_hours):
        if st.session_state.data is None:
            return
        
        # 1. Update current settings
        new_wake_str = target_wake.strftime("%H:%M:%S")
        new_window = float(window_hours)

        st.session_state.data["meta"]["settings"] = {
            "target_wake": new_wake_str,
            "window_hours": new_window
        }

        # 2. Update Window History
        history = self.get_window_history()
        today_str = str(date.today())

        # Find active period
        active_period = next((p for p in history if p["end_date"] is None), None)

        if active_period:
            # Avoid duplicate entries if values haven't changed
            if (active_period["target_wake"] == new_wake_str and 
                active_period["window_hours"] == new_window):
                self._save_to_disk(st.session_state.filepath, st.session_state.data)
                st.success("Innstillinger lagret!")
                return

            # Special case: If active period STARTED today, update it instead of closing (prevent end < start)
            if active_period["start_date"] == today_str:
                active_period["target_wake"] = new_wake_str
                active_period["window_hours"] = new_window
            else:
                # Close old period
                yesterday = date.today() - timedelta(days=1)
                active_period["end_date"] = str(yesterday)
                
                # Start new period
                new_period = {
                    "start_date": today_str,
                    "end_date": None,
                    "target_wake": new_wake_str,
                    "window_hours": new_window
                }
                history.append(new_period)
        else:
            # Should technically not happen due to get_window_history init, but safety fallback
            new_period = {
                "start_date": today_str,
                "end_date": None,
                "target_wake": new_wake_str,
                "window_hours": new_window
            }
            history.append(new_period)

        self._save_to_disk(st.session_state.filepath, st.session_state.data)
        st.success("Innstillinger og historikk lagret!")

    def get_settings(self):
        if st.session_state.data:
            return st.session_state.data["meta"].get("settings", {
                "target_wake": "07:00:00",
                "window_hours": 6.0
            })
        return None

    def save_entry(self, entry_date, entry_data):
        if st.session_state.data is None:
            return
        
        date_key = str(entry_date)
        st.session_state.data["entries"][date_key] = entry_data
        self._save_to_disk(st.session_state.filepath, st.session_state.data)
        st.success(f"Logg for {date_key} lagret!")

    def _save_to_disk(self, filepath, data):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_entry(self, entry_date):
        if st.session_state.data:
            return st.session_state.data["entries"].get(str(entry_date))
        return None

    def get_window_for_date(self, target_date):
        """Finds the active settings for a specific date from history."""
        target_str = str(target_date)
        history = self.get_window_history()
        
        # Default fallback
        fallback = self.get_settings()
        
        if not history:
             return fallback

        for period in history:
            start = period["start_date"]
            end = period["end_date"]
            
            # Check if target is after start
            if target_str >= start:
                # Check if target is before or on end (if end exists)
                if end is None or target_str <= end:
                    return {
                        "target_wake": period["target_wake"],
                        "window_hours": period["window_hours"]
                    }
        
        # If no matching period found (e.g. date before first history), return fallback
        return fallback

# --- SHARED HELPERS (Data Processing) ---
def format_hours_as_hm(hours: float) -> str:
    total_min = int(round(hours * 60))
    h = total_min // 60
    m = total_min % 60
    if m == 0:
        return f"{h} t"
    return f"{h} t {m} min"

# Slider options: 5 hours (300 min) to 12 hours (720 min) step 15
WINDOW_OPTIONS = range(300, 720, 15)
def format_window_label(m):
    return f"{m//60}:{m%60:02d}"

def process_log_data(data_entries: Dict[str, Any]) -> pd.DataFrame:
    """
    Processes raw log entries into a structured DataFrame for analysis and visualization.
    
    Args:
        data_entries: Dictionary of log entries, keyed by date string (YYYY-MM-DD).
        
    Returns:
        pd.DataFrame: DataFrame containing processed sleep metrics (SE, TST, TIB, etc.)
                      and datetime objects for sleep events. Returns empty DataFrame if input is empty.
    """
    if not data_entries:
        return pd.DataFrame()

    processed_records = []
    
    for date_str, entry in data_entries.items():
        log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Parse times
        bed_time = time.fromisoformat(entry["bed_time"])
        out_of_bed = time.fromisoformat(entry["out_of_bed"])
        lights_out = time.fromisoformat(entry["lights_out"])
        sleep_onset = time.fromisoformat(entry["sleep_onset"])
        wake_up = time.fromisoformat(entry["wake_up"])
        
        # --- RIGID DATE LOGIC (18:00 PIVOT) ---
        def get_dt(t, base_date):
            if t.hour >= 18: # Pivot at 18:00 to be safe
                return datetime.combine(base_date, t)
            else:
                return datetime.combine(base_date + timedelta(days=1), t)

        bed_dt = get_dt(bed_time, log_date)
        out_dt = get_dt(out_of_bed, log_date)
        onset_dt = get_dt(sleep_onset, log_date)
        wake_dt = get_dt(wake_up, log_date)
        lights_dt = get_dt(lights_out, log_date)
        
        # Metrics
        waso = entry.get("waso_minutes", 0)
        
        # Duration Calculations
        tib_seconds = (out_dt - bed_dt).total_seconds()
        tib_min = tib_seconds / 60
        
        # TST: Sleep Onset to Wake Up - WASO
        tst_seconds = (wake_dt - onset_dt).total_seconds() - (waso * 60)
        tst_min = tst_seconds / 60
        
        se = (tst_min / tib_min * 100) if tib_min > 0 else 0
        se = max(0.0, min(100.0, float(se)))
        
        # Awakenings
        processed_awakenings = []
        for awak in entry.get("awakenings", []):
            try:
                t_awak = time.fromisoformat(awak["time"])
                start_awak = get_dt(t_awak, log_date)
                processed_awakenings.append({
                    "start": start_awak,
                    "duration_min": awak["duration_min"],
                    "end": start_awak + timedelta(minutes=awak["duration_min"])
                })
            except:
                pass

        processed_records.append({
            "Date": log_date,
            "DateLabel": log_date.strftime("%d. %b"), 
            "SE": se,
            "TIB_min": tib_min,
            "TST_min": tst_min,
            "bed_dt": bed_dt,
            "out_dt": out_dt,
            "onset_dt": onset_dt,
            "wake_dt": wake_dt,
            "lights_dt": lights_dt,
            "awakenings": processed_awakenings,
            "nap_minutes": entry.get("nap_minutes", 0)
        })

    df = pd.DataFrame(processed_records).sort_values("Date")
    df = df.drop_duplicates(subset=["Date"], keep="last")
    return df

# --- UI COMPONENTS ---


def build_sleep_gantt_figure(df, for_print=False):
    """
    Bygger Gantt/døgnrytmefigur for søvnmønster. Forventer kolonner:
    DateLabel, bed_dt, out_dt, onset_dt, wake_dt, awakenings (liste), m.m.
    Returnerer en ferdig konfigurert go.Figure.
    """
    # Helper to normalize time for visualization (18:00 - 18:00)
    def normalize(dt_obj):
        base_d1 = date(2000, 1, 1)
        base_d2 = date(2000, 1, 2)
        t = dt_obj.time()
        if t.hour >= 18:
            return datetime.combine(base_d1, t)
        else:
            return datetime.combine(base_d2, t)

    fig_gantt = go.Figure()

    if df.empty:
        return fig_gantt

    # LEGEND HACK
    first_y = df["DateLabel"].iloc[0]
    fig_gantt.add_trace(go.Bar(y=[first_y], x=[0], name="Tid i seng", marker_color='#E0E0E0', showlegend=True))
    fig_gantt.add_trace(go.Bar(y=[first_y], x=[0], name="Søvn", marker_color='#0067C5', showlegend=True))
    fig_gantt.add_trace(go.Bar(y=[first_y], x=[0], name="Våken", marker_color='#C30000', showlegend=True))

    df_rev = df.sort_values("Date", ascending=False)

    MS_PER_HOUR = 3600 * 1000
    TOTAL_MS = 24 * MS_PER_HOUR
    base_start = datetime(2000, 1, 1, 18, 0)

    def get_offset(dt_full):
        norm_dt = normalize(dt_full)
        diff = (norm_dt - base_start).total_seconds() * 1000
        return diff

    for _, row in df_rev.iterrows():
        d_label = row["DateLabel"]

        # Helper to draw bars
        def draw_bar(start, end, color, legend_group):
            start_off = get_offset(start)
            end_off = get_offset(end)
            dur = end_off - start_off
            if dur > 0:
                fig_gantt.add_trace(go.Bar(
                    y=[d_label], x=[dur], base=[start_off],
                    orientation='h', marker_color=color,
                    showlegend=False, hoverinfo="x+y"
                ))

        # 1. Base Bed Time
        draw_bar(row["bed_dt"], row["out_dt"], '#E0E0E0', 'bed')
        # 2. Sleep Time (approximated as Bed + Latency to Wake)
        draw_bar(row["onset_dt"], row["wake_dt"], '#0067C5', 'sleep')
        
        # 3. Awakenings
        for awak in row["awakenings"]:
            start_off = get_offset(awak["start"])
            dur_ms = awak["duration_min"] * 60 * 1000
            fig_gantt.add_trace(go.Bar(
                y=[d_label], x=[dur_ms], base=[start_off],
                orientation='h', marker_color='#C30000',
                showlegend=False, width=0.6
            ))

    # TICKS
    tick_vals = [h * MS_PER_HOUR for h in range(25)]
    tick_text = [f"{(18 + h) % 24:02d}:00" for h in range(25)]

    # Layout config
    # Using dictionary literal to avoid Pyre errors with mixed value types
    layout_args: Dict[str, Any] = {
        "font_color": "#262626",
        "barmode": "overlay",
        "legend_orientation": "h",
        "legend_y": 1.1,
        "legend_font_color": "#262626",
        "yaxis_title": "Dato",
        "yaxis_type": "category",
        "yaxis_categoryorder": "array",
        "yaxis_categoryarray": df_rev["DateLabel"].tolist(),
        "xaxis_type": "linear",
        "xaxis_range": [0, TOTAL_MS],  # FIXED RANGE 18:00 - 18:00
        "xaxis_tickmode": "array",
        "xaxis_tickvals": tick_vals,
        "xaxis_ticktext": tick_text,
        "xaxis_showgrid": True,
        "xaxis_gridcolor": "#D1D1D1",
    }

    if for_print:
        # Compact sizing for print
        # Approx 300px or minimal height per row + buffer
        layout_args["height"] = max(300, len(df_rev) * 25 + 100)
        layout_args["margin"] = {"l": 20, "r": 20, "t": 30, "b": 20}
        # Maybe smaller font?
        layout_args["font"] = {"size": 10}
    else:
        # Standard sizing
        layout_args["height"] = max(400, len(df_rev) * 60)
    
    fig_gantt.update_layout(**layout_args)
    return fig_gantt

def render_file_explorer(manager, mode="open"):
    """
    Renders a file explorer using st.dataframe for a professional 'Details' view.
    mode: 'open' (click file to load) or 'new' (click folder to navigate)
    """
    current_path = st.session_state.current_browser_dir
    
    # 1. Navigation Header
    c1, c2 = st.columns([0.1, 0.9])
    with c1:
        if st.button("⬆️", help="Gå til mappen over"):
            st.session_state.current_browser_dir = os.path.dirname(current_path)
            st.rerun()
    with c2:
        st.code(current_path, language=None)

    # 2. Prepare Data
    try:
        items = os.listdir(current_path)
    except PermissionError:
        st.error(f"Ingen tilgang til mappen: {current_path}")
        return

    data = []
    
    # Process Directories
    dirs = sorted([d for d in items if os.path.isdir(os.path.join(current_path, d)) and not d.startswith('.')])
    for d in dirs:
        full_path = os.path.join(current_path, d)
        stats = os.stat(full_path)
        mtime = datetime.fromtimestamp(stats.st_mtime).strftime("%d.%m.%Y %H:%M")
        data.append({
            "Type": "📁", 
            "Navn": d, 
            "Sist endret": mtime, 
            "Størrelse": "-",
            "path": full_path,
            "is_dir": True
        })

    # Process Files
    files = sorted([f for f in items if f.endswith('.json')])
    for f in files:
        full_path = os.path.join(current_path, f)
        stats = os.stat(full_path)
        mtime = datetime.fromtimestamp(stats.st_mtime).strftime("%d.%m.%Y %H:%M")
        size_kb = f"{max(1, int(stats.st_size / 1024))} KB"
        data.append({
            "Type": "🌙", 
            "Navn": f, 
            "Sist endret": mtime, 
            "Størrelse": size_kb,
            "path": full_path,
            "is_dir": False
        })
        
    # 3. Render Dataframe
    if not data:
        st.caption("Tom mappe.")
        return

    df_explorer = pd.DataFrame(data)
    
    # Configure columns
    column_config = {
        "Type": st.column_config.TextColumn("Type", width="small"),
        "Navn": st.column_config.TextColumn("Navn", width="large"),
        "Sist endret": st.column_config.TextColumn("Sist endret", width="medium"),
        "Størrelse": st.column_config.TextColumn("Størrelse", width="small"),
        "path": None,   # Hide hidden columns
        "is_dir": None
    }
    
    event = st.dataframe(
        df_explorer,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # 4. Handle Selection
    if event.selection.rows:
        selected_index = event.selection.rows[0]
        selected_item = data[selected_index]
        
        if selected_item["is_dir"]:
            st.session_state.current_browser_dir = selected_item["path"]
            st.rerun()
            
        else:
            # File selection
            if mode == "open":
                if manager.load_log(selected_item["path"]):
                    st.session_state.main_menu_nav = "🏠 Loggføring"
                    st.rerun()
            elif mode == "new":
                # In 'new' mode, selecting a file might not do much unless we want to Overwrite?
                # For now, just maybe show it's selected or do nothing.
                pass


def render_welcome_view(manager):
    render_custom_css()
    
    # --- HEADER & INTRO ---
    # Centered aesthetic
    c_spacer, c_content, c_spacer2 = st.columns([1, 6, 1])
    
    with c_content:
        st.title("🌙 Søvndagbok")
        st.caption("Kognitiv atferdsbehandling for insomni (CBT-i)")
        
        # Intro Box
        with st.container():
            st.markdown("""
            ### Velkommen til din søvndagbok
            Dette verktøyet er bygget på prinsippene for **Kognitiv atferdsterapi for insomni (CBT-i)**, som er den anbefalte behandlingen for langvarige søvnproblemer.
            
            Appen hjelper deg med å:
            *   **Kartlegge søvnmønsteret ditt** systematisk over tid.
            *   **Beregne søvneffektivitet** (hvor mye av tiden i sengen du faktisk sover).
            *   **Bygge opp søvntrykk** ved å begrense tiden i sengen til det du faktisk trenger (søvnrestriksjon).
            *   **Justere søvnvinduet** basert på dine egne data fra uke til uke.
            """)
        
        st.warning("⚠️ **Om verktøyet:** Denne appen er et selvstendig hjelpemiddel for egenmestring og struktur. Den erstatter ikke helsefaglig behandling, men fungerer som et supplement til terapibasert behandling.")
        
        st.divider()
        
        # --- MODE SELECTION ---
        # "Tabs" feel using radio/segmented
        
        # Check for segmented_control availability
        nav_mode = None
        if hasattr(st, "segmented_control"):
            nav_mode = st.segmented_control(
                "Jeg vil:", 
                ["📂 Åpne eksisterende dagbok", "✨ Starte ny dagbok"],
                default="📂 Åpne eksisterende dagbok"
            )
        else:
            nav_mode = st.radio(
                "Jeg vil:", 
                ["📂 Åpne eksisterende dagbok", "✨ Starte ny dagbok"],
                horizontal=True
            )
            
        st.write("") # Spacer

        if not nav_mode:
            nav_mode = "📂 Åpne eksisterende dagbok"

        if nav_mode == "📂 Åpne eksisterende dagbok":
            st.subheader("Velg fil")
            with st.container(border=True):
                 render_file_explorer(manager, mode="open")
                 
        else:
            st.subheader("Opprett ny dagbok")
            with st.container(border=True):
                c1, c2 = st.columns(2)
                name = c1.text_input("Ditt navn", placeholder="Navn")
                filename = c2.text_input("Filnavn", value="min_sovndagbok.json")
                
                st.write("**Velg lagringsmappe:**")
                st.info(f"Valgt mappe: `{st.session_state.current_browser_dir}`")
                
                # File explorer in 'new' mode logic
                render_file_explorer(manager, mode="new")
                
                st.divider()
                if st.button("🚀 Opprett og start", type="primary", use_container_width=True):
                    if manager.create_new_log(name, st.session_state.current_browser_dir, filename):
                        # SUCCESS HOOK: Set default menu to 'Plan'
                        st.session_state.main_menu_nav = "📅 Din søvnplan"
                        st.rerun()

def render_main_app(manager):
    render_custom_css()
    data = st.session_state.data
    meta = data["meta"]
    
    with st.sidebar:
        st.markdown(f"### 👤 {meta['name']}")
        
        # Check if we have a requested page from welcome view
        default_index = 1 # Default to "Loggføring" normally
        options = ["📅 Din søvnplan", "🏠 Loggføring", "📊 Visualisering", "📈 Analyse og råd", "📝 Rapporter og utskrifter", "📂 Rådata"]
        
        if "main_menu_nav" in st.session_state:
            try:
                default_index = options.index(st.session_state.main_menu_nav)
            except ValueError:
                default_index = 1
        
        # Use key to sync with state, but if generic state issue, just use separate logic
        # Ideally, we pass 'index' to radio. 
        # But if we use 'key', Streamlit handles it.
        # Let's initialize the key if not set.
        if "main_menu_key" not in st.session_state:
             st.session_state.main_menu_key = options[default_index]
             
        # Override if we just came from welcome view (flag)
        if "main_menu_nav" in st.session_state:
            st.session_state.main_menu_key = st.session_state.main_menu_nav
            del st.session_state.main_menu_nav # Consume the flag

        mode = st.radio("Meny", options, key="main_menu_key")
        
        st.divider()
        if st.button("Lukk dagbok"):
            st.session_state.data = None
            st.session_state.filepath = None
            if "main_menu_key" in st.session_state:
                del st.session_state.main_menu_key
            st.rerun()

    if mode == "📅 Din søvnplan":
         render_plan_view(manager)
    elif mode == "🏠 Loggføring":
        render_logging_view(manager)
    elif mode == "📊 Visualisering":
        render_viz_view(manager)
    elif mode == "📈 Analyse og råd":
         render_analysis_view(manager)
    elif mode == "📝 Rapporter og utskrifter":
         render_weekly_report_view(manager)
    elif mode == "📂 Rådata":
         render_rawdata_view(manager)

def render_plan_view(manager):
    st.header("📅 Din søvnplan")
    st.info("Sett dine mål her. Disse brukes som standardverdier i loggen.")
    
    current_settings = manager.get_settings()
    
    with st.form("settings_form"):
        try:
            curr_wake = time.fromisoformat(current_settings["target_wake"])
        except ValueError:
            curr_wake = time(7, 0)
            
        curr_window = current_settings.get("window_hours", 6.0)
        curr_window_min = int(round(float(curr_window) * 60))
        
        c1, c2 = st.columns(2)
        target_wake = c1.time_input("Mål for oppvåkning", value=curr_wake, help="Når du skal stå opp om morgenen.")
        
        # UI shows time format (H:MM)
        # Find closest option to current value
        current_val = min(WINDOW_OPTIONS, key=lambda x: abs(x - curr_window_min))
        
        window_minutes = c2.select_slider(
            "Søvnvindu (timer:minutter)",
            options=WINDOW_OPTIONS,
            value=current_val,
            format_func=format_window_label,
            help="Hvor lenge du skal ligge i sengen."
        )
        window_hours = window_minutes / 60.0
        
        wake_dt = datetime.combine(date.today(), target_wake)
        bed_dt = wake_dt - timedelta(hours=window_hours)
        st.markdown(
            f"**Anbefalt leggetid:** {bed_dt.strftime('%H:%M')}  "
            f"(søvnvindu: {format_hours_as_hm(window_hours)})"
        )
        
        # New: Valid from info
        st.info(f"ℹ️ Endringen i søvnvindu gjelder fra og med **{date.today()}**.")
        
        if st.form_submit_button("Lagre plan"):
            manager.save_settings(target_wake, window_hours)

    # New: History Table
    st.divider()
    
    # Editor in Expander
    with st.expander("🛠️ Juster søvnplan-historikk. **ER NORMALT SETT IKKE NØDVENDIG Å GJØRE NOE HER!**"):
        render_window_history_editor(manager)

    st.subheader("Historikk")
    
    history = manager.get_window_history()
    if history:
        table_rows = []
        # Reverse to show newest first
        for i, entry in enumerate(reversed(history)):
            row_num = len(history) - i
            
            start = entry["start_date"]
            end = entry["end_date"] if entry["end_date"] else "Pågår"
            t_wake = entry["target_wake"]
            win = entry["window_hours"]
            
            table_rows.append({
                "Periode": row_num,
                "Fra": start,
                "Til": end,
                "Mål oppvåkning": t_wake,
                "Vindu": format_hours_as_hm(win)
            })
            
        st.dataframe(
            table_rows, 
            hide_index=True,
            width="stretch",
            column_config={
                "Periode": st.column_config.NumberColumn("Periode", width="small"),
                "Fra": st.column_config.TextColumn("Fra", width="medium"),
                "Til": st.column_config.TextColumn("Til", width="medium"),
                "Mål oppvåkning": st.column_config.TextColumn("Mål oppvåkning", width="medium"),
                "Vindu (t)": st.column_config.NumberColumn("Vindu (t)", format="%.2f", width="medium")
            }
        )
    else:
        st.caption("Ingen historikk funnet.")


def render_window_history_editor(manager):
    """
    Renders an interactive editor for the sleep window history.
    Allows users to modify start/end dates, target wake times, and window durations for past periods.
    """
    st.info("Her kan du korrigere historikken. Endringer påvirker statistikk og anbefalinger.")
    
    history = manager.get_window_history()
    if not history:
        st.info("Ingen historikk å redigere.")
        return

    # Use a form? No, interactive edits needed.
    # We edit a local copy logic
    
    if "history_editor_data" not in st.session_state:
        # Initialize editor state with DEEP copy
        st.session_state.history_editor_data = [h.copy() for h in history]
        
    # Button to reset/reload 
    if st.button("🔄 Last inn på nytt"):
         st.session_state.history_editor_data = [h.copy() for h in history]
         st.rerun()

    edited_history = st.session_state.history_editor_data
    
    # Iterate and edit
    # Sort by start date to keep sane order
    # edited_history.sort(key=lambda x: x["start_date"]) # Should we force sort? Yes.
    
    # Iterate in reverse to show newest first, but keep index for editing
    # list(enumerate(history)) gives [(0, h0), (1, h1)...]
    # reversed(...) gives [(N, hN)... (0, h0)]
    for i, entry in reversed(list(enumerate(edited_history))):
        st.markdown(f"**Periode {i+1}**")
        
        # Grid Layout 2.0
        # Row 1: Active Checkbox (Right)
        
        c1, c2 = st.columns(2)
        # Left col empty
        c1.write("")
        
        # Checkbox logic
        is_active_in_data = entry["end_date"] is None
        # Use key to persist state if needed, but value drives initial render
        is_active = c2.checkbox("Pågående periode (aktiv)", value=is_active_in_data, key=f"hist_active_{i}")
        
        # Row 2: Dates
        c3, c4 = st.columns(2)
        
        # Start Date
        try:
            d_start = datetime.strptime(entry["start_date"], "%Y-%m-%d").date()
        except:
            d_start = date.today()
        new_start = c3.date_input(f"Start dato #{i+1}", value=d_start, key=f"hist_start_{i}")
        entry["start_date"] = str(new_start)
        
        # End Date
        # Logic controlled by checkbox above
        try:
            current_end_date = datetime.strptime(entry["end_date"], "%Y-%m-%d").date() if entry["end_date"] else date.today()
        except:
            current_end_date = date.today()
            
        end_date_input_val = date.today() if is_active else current_end_date
        
        new_end = c4.date_input(
            f"Slutt dato #{i+1}", 
            value=end_date_input_val, 
            disabled=is_active,
            key=f"hist_end_{i}"
        )
        
        # Update entry based on active state
        if is_active:
            entry["end_date"] = None
        else:
            entry["end_date"] = str(new_end)

        # Row 3: Time & Window
        c5, c6 = st.columns(2)
        
        # Target Wake
        try:
            t_wake = time.fromisoformat(entry["target_wake"])
        except:
            t_wake = time(7, 0)
        new_wake = c5.time_input(f"Mål oppvåkning #{i+1}", value=t_wake, key=f"hist_wake_{i}")
        entry["target_wake"] = new_wake.strftime("%H:%M:%S")
        
        # Window Slider
        win_min = int(round(float(entry["window_hours"]) * 60))
        # Find closest option
        current_val_hist = min(WINDOW_OPTIONS, key=lambda x: abs(x - win_min))
        
        new_win_min = c6.select_slider(
            f"Vindu (t:m) #{i+1}", 
            options=WINDOW_OPTIONS,
            value=current_val_hist,
            format_func=format_window_label,
            key=f"hist_win_{i}"
        )
        entry["window_hours"] = new_win_min / 60.0

        # Row 4: Delete Button (Only for inactive periods)
        if not is_active:
            if st.button(f"🗑️ Slett periode {i+1}", key=f"del_hist_{i}"):
                edited_history.pop(i)
                manager.save_window_history(edited_history)
                st.session_state.history_editor_data = edited_history
                st.rerun()

        st.divider()

    # Immediate Validation Display
    active_count = sum(1 for e in edited_history if e["end_date"] is None)
    if active_count > 1:
        st.error("⚠️ **Du har markert flere perioder som pågående. Vennligst fjern krysset fra de gamle periodene og sett en sluttdato for dem.**")
    elif active_count == 0:
        st.warning("⚠️ **Ingen periode er markert som pågående. Dette vil stoppe beregningen av anbefalinger.**")
        
    if st.button("💾 Lagre endringer i historikk"):
        # Validation
        # 1. Sort by Start Date
        edited_history.sort(key=lambda x: x["start_date"])
        
        # 2. Check overlap? (Basic check: End of one < Start of next)
        valid = True
        
        # Active Period Validation
        if active_count > 1:
            st.error(f"**Feil: {active_count} perioder er markert som pågående (aktive). Kun én periode kan være aktiv av gangen. Gå gjennom listen og sett sluttdato på de gamle periodene.**")
            valid = False
            
        # Overlap Check
        for i in range(len(edited_history)):
            if i < len(edited_history) - 1:
                curr_end = edited_history[i]["end_date"]
                next_start = edited_history[i+1]["start_date"]
                
                if curr_end is None:
                     # Active period must be last usually
                     # If active period is followed by another, it means active period starts BEFORE next one?
                     # Allowed if active period is *ongoing* and next one is *future plan*? 
                     # But current logic treats active as *current*.
                     # Let's not strictly block based on position, but warn if active is not last?
                     pass 
                elif curr_end >= next_start:
                     st.error(f"Periode {i+1} slutter ({curr_end}) etter eller samtidig som periode {i+2} starter ({next_start}).")
                     valid = False
        
        if valid:
            manager.save_window_history(edited_history)
            st.success("Historikk oppdatert!")
            # Update session state to force refresh of other views?
            # Rerun acts as a refresh
            del st.session_state.history_editor_data
            st.rerun()

def render_logging_view(manager):
    st.header("✍️ Daglig loggføring")
    
    def load_data_for_date():
        current_date = st.session_state.log_date
        entry = manager.get_entry(current_date)
        settings = manager.get_settings()
        
        if entry:
            st.session_state.bed_time = time.fromisoformat(entry["bed_time"])
            st.session_state.out_of_bed = time.fromisoformat(entry["out_of_bed"])
            st.session_state.lights_out = time.fromisoformat(entry["lights_out"])
            st.session_state.sleep_onset = time.fromisoformat(entry["sleep_onset"])
            st.session_state.wake_up = time.fromisoformat(entry["wake_up"])
            st.session_state.nap_minutes = entry.get("nap_minutes", 0)
            
            raw_awakenings = entry.get("awakenings", [])
            parsed = []
            for item in raw_awakenings:
                 t_obj = time.fromisoformat(item["time"])
                 parsed.append({"time": t_obj, "duration": item["duration_min"]})
            st.session_state.current_wakeups = parsed
            
            # SNAPSHOT FOR CHANGES
            st.session_state.original_values = {
                "bed_time": st.session_state.bed_time,
                "out_of_bed": st.session_state.out_of_bed,
                "lights_out": st.session_state.lights_out,
                "sleep_onset": st.session_state.sleep_onset,
                "wake_up": st.session_state.wake_up,
                "nap_minutes": st.session_state.nap_minutes,
                "current_wakeups": [w.copy() for w in parsed]
            }
        else:
            plan_wake = time.fromisoformat(settings["target_wake"])
            plan_window = settings["window_hours"]
            plan_wake_dt = datetime.combine(date.today(), plan_wake)
            plan_bed_dt = plan_wake_dt - timedelta(hours=plan_window)
            
            st.session_state.bed_time = plan_bed_dt.time()
            st.session_state.out_of_bed = plan_wake
            st.session_state.lights_out = (plan_bed_dt + timedelta(minutes=15)).time()
            st.session_state.sleep_onset = (plan_bed_dt + timedelta(minutes=30)).time()
            st.session_state.wake_up = plan_wake
            st.session_state.nap_minutes = 0
            st.session_state.current_wakeups = []
            
            # Clear snapshot since it's a new entry
            if "original_values" in st.session_state:
                del st.session_state.original_values

    # Initialize session state for date
    if "log_date" not in st.session_state:
        # Default to yesterday (since we log the night that just passed)
        st.session_state.log_date = date.today() - timedelta(days=1)
        load_data_for_date()
        
    # Load defaults if bed_time not set
    if "bed_time" not in st.session_state:
        load_data_for_date()
    
    st.date_input("Dato", key="log_date", on_change=load_data_for_date)
    
    cur_date = st.session_state.log_date
    if manager.get_entry(cur_date):
        st.warning(f"⚠️ Redigerer eksisterende logg for {cur_date}.")
        
        # --- CHECK FOR CHANGES ---
        if "original_values" in st.session_state:
            orig = st.session_state.original_values
            curr_wakeups = st.session_state.current_wakeups
            
            # Simple field check
            has_changes = (
                st.session_state.bed_time != orig["bed_time"] or
                st.session_state.out_of_bed != orig["out_of_bed"] or
                st.session_state.lights_out != orig["lights_out"] or
                st.session_state.sleep_onset != orig["sleep_onset"] or
                st.session_state.wake_up != orig["wake_up"] or
                st.session_state.nap_minutes != orig["nap_minutes"]
            )
            
            # Complex check for wakeups (list of dicts)
            if not has_changes:
                if len(curr_wakeups) != len(orig["current_wakeups"]):
                    has_changes = True
                else:
                    for i, w in enumerate(curr_wakeups):
                        o = orig["current_wakeups"][i]
                        # Note: 'time' in wakeups might be comparing objects, ensure type safety if needed
                        if w["time"] != o["time"] or w["duration"] != o["duration"]:
                            has_changes = True
                            break
            
            if has_changes:
                st.warning("📝 Du har gjort endringer i denne loggen. Husk å trykke ‘Lagre Dagbok’ for å ta vare på dem.")

    with st.container():
        st.subheader("Tider")
        c1, c2 = st.columns(2)
        c1.time_input("La meg", key="bed_time")
        c2.time_input("Sto opp", key="out_of_bed")
        
        c3, c4, c5 = st.columns(3)
        c3.time_input("Slukket lys", key="lights_out")
        c4.time_input("Sovnet (ca)", key="sleep_onset")
        c5.time_input("Våknet", key="wake_up")
        
        st.number_input("Søvn dagtid (min)", min_value=0, step=5, key="nap_minutes")

    st.divider()
    st.subheader("Oppvåkninger")
    
    if "current_wakeups" not in st.session_state:
        st.session_state.current_wakeups = []
    
    def add_wakeup():
        st.session_state.current_wakeups.append({"time": time(3, 0), "duration": 10})

    def remove_wakeup(idx):
        st.session_state.current_wakeups.pop(idx)

    for i, wakeup in enumerate(st.session_state.current_wakeups):
        c_time, c_dur, c_del = st.columns([1, 1, 0.2])
        
        new_time = c_time.time_input(
            f"Tidspunkt #{i+1}", 
            value=wakeup["time"], 
            key=f"wake_time_{i}_d{cur_date}",
            label_visibility="collapsed"
        )
        new_dur = c_dur.number_input(
            f"Varighet (min) #{i+1}", 
            min_value=1, 
            value=wakeup["duration"], 
            step=1, 
            key=f"wake_dur_{i}_d{cur_date}",
            label_visibility="collapsed"
        )
        st.session_state.current_wakeups[i]["time"] = new_time
        st.session_state.current_wakeups[i]["duration"] = new_dur

        if c_del.button("❌", key=f"del_{i}"):
            remove_wakeup(i)
            st.rerun()

    st.button("➕ Legg til oppvåkning", on_click=add_wakeup)
    
    total_waso = sum(w["duration"] for w in st.session_state.current_wakeups)
    st.info(f"Total våkentid: **{total_waso} minutter**")
    
    st.divider()

    if st.button("💾 Lagre dagbok", type="primary"):
        final_awakenings = []
        for w in st.session_state.current_wakeups:
            final_awakenings.append({
                "time": w["time"].strftime("%H:%M:%S"),
                "duration_min": w["duration"]
            })

        entry_data = {
            "bed_time": st.session_state.bed_time.strftime("%H:%M:%S"),
            "out_of_bed": st.session_state.out_of_bed.strftime("%H:%M:%S"),
            "lights_out": st.session_state.lights_out.strftime("%H:%M:%S"),
            "sleep_onset": st.session_state.sleep_onset.strftime("%H:%M:%S"),
            "wake_up": st.session_state.wake_up.strftime("%H:%M:%S"),
            "awakenings": final_awakenings,
            "waso_minutes": int(total_waso),
            "nap_minutes": st.session_state.nap_minutes
        }
        manager.save_entry(cur_date, entry_data)
        
        # Update snapshot to reflect saved state
        st.session_state.original_values = {
            "bed_time": st.session_state.bed_time,
            "out_of_bed": st.session_state.out_of_bed,
            "lights_out": st.session_state.lights_out,
            "sleep_onset": st.session_state.sleep_onset,
            "wake_up": st.session_state.wake_up,
            "nap_minutes": st.session_state.nap_minutes,
            "current_wakeups": [w.copy() for w in st.session_state.current_wakeups]
        }
        st.rerun()

def render_viz_view(manager):
    """
    Renders the Visualization view, displaying graphs for Sleep Efficiency (SE) and Sleep Pattern (Gantt).
    Includes date filtering options ("Last 7 days" or custom range).
    """
    st.header("📊 Visualisering")
    data = st.session_state.data["entries"]
    if not data:
        st.info("Ingen data å vise.")
        return

    # --- PROCESS DATA ---
    df = process_log_data(data)
    if df.empty:
        st.info("Ingen gyldige data.")
        return

    # --- DATE FILTER ---
    st.write("") # Spacer
    c_filter, c_info = st.columns([1, 2])
    
    with c_filter:
        filter_mode = st.radio("Periode", ["Siste 7 dager", "Velg periode"], horizontal=True, label_visibility="collapsed")
        
    start_date = date.today() - timedelta(days=7)
    end_date = date.today() - timedelta(days=1)
    
    with c_info:
        if filter_mode == "Siste 7 dager":
            st.caption(f"Viser datasett for siste uke ({start_date} til {end_date}).")
        else:
            c_start, c_end = st.columns(2)
            # Default custom range: last 14 days
            def_start = date.today() - timedelta(days=14)
            start_date = c_start.date_input("Fra dato", value=def_start)
            end_date = c_end.date_input("Til dato", value=date.today() - timedelta(days=1))
            
    # Apply Filter
    # Ensure dataframe Date column is comparable
    mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
    df = df.loc[mask]
    
    if df.empty:
        st.info(f"Ingen data funnet i perioden {start_date} til {end_date}.")
        return


    # --- GRAF 1: SE ---
    st.subheader("Søvneffektivitet (SE)")
    
    fig_se = px.line(df, x="DateLabel", y="SE", markers=True)
    fig_se.update_traces(line_color='#0067C5', marker={"size": 9, "line": {"width": 2, "color": "white"}})

    fig_se.update_layout(
        font_color="#262626", # Tving sort tekst
        yaxis_range=[0, 105],
        yaxis_title="SE (%)",
        yaxis_showgrid=True,
        yaxis_gridcolor="#D1D1D1",
        yaxis_zeroline=False,
        xaxis_type="category",
        xaxis_title="Dato",
        xaxis_showgrid=True,
        xaxis_gridwidth=1,
        xaxis_gridcolor="#D1D1D1",
        legend_font_color="#262626"
    )
    fig_se.add_hline(y=85, line_dash="dash", line_color="#06893A", annotation_text="Mål (85%)")
    st.plotly_chart(fig_se, width="stretch")

    # --- GRAF 2: GANTT ---
    st.divider()
    st.subheader("Døgnrytme (Søvnmønster)")
    st.caption("Viser hele døgnet fra 18:00 til 18:00.")

    fig_gantt = build_sleep_gantt_figure(df)
    st.plotly_chart(fig_gantt, width="stretch")

def render_rawdata_view(manager):
    st.header("📂 Rådata")
    
    # 1. Access Data
    if not st.session_state.data or "entries" not in st.session_state.data:
        st.info("Ingen data tilgjengelig.")
        return
        
    entries = st.session_state.data["entries"]
    if not entries:
        st.info("Ingen loggføringer funnet.")
        return

    # 2. Controls
    filter_option = st.radio("Visning", ["Siste 7 dager", "Alle data"], horizontal=True)
    
    # 3. Process Data into List
    rows = []
    for date_str, data in entries.items():
        # Helpers for safety
        def safe_get(key): return data.get(key, "")
        
        # Format awakenings
        awaks = data.get("awakenings", [])
        awak_str = "; ".join([f"{a['time']} ({a['duration_min']}m)" for a in awaks])
        
        rows.append({
            "Dato": date_str,
            "Leggetid": safe_get("bed_time"),
            "Slukket lys": safe_get("lights_out"),
            "Sovnet": safe_get("sleep_onset"),
            "Våknet": safe_get("wake_up"),
            "Sto opp": safe_get("out_of_bed"),
            "WASO (min)": safe_get("waso_minutes"),
            "Søvn dagtid (min)": safe_get("nap_minutes"),
            "Antall oppvåk.": len(awaks),
            "Oppvåkninger detaljer": awak_str
        })
    
    # 4. Create DataFrame and Sort
    df = pd.DataFrame(rows)
    df["Dato_dt"] = pd.to_datetime(df["Dato"])
    df = df.sort_values("Dato_dt", ascending=False)
    
    # 5. Filter
    if filter_option == "Siste 7 dager":
        df = df.head(7)
    
    # Drop temp sort column
    df = df.drop(columns=["Dato_dt"])
    
    # 6. Display
    st.dataframe(
        df, 
        width="stretch", 
        hide_index=True,
        column_config={
            "Dato": st.column_config.TextColumn("Dato", width="medium"),
            "Oppvåkninger detaljer": st.column_config.TextColumn("Oppvåkninger", width="large"),
        }
    )

def render_analysis_view(manager):
    """
    Renders the Analysis & Advice view (CBT-i).
    Calculates sleep metrics based on the active window history and provides
    recommendations for adjusting the sleep window based on Sleep Efficiency (SE).
    """
    st.header("📈 Analyse og råd (CBT-i)")
    data_entries = st.session_state.data["entries"]
    df = process_log_data(data_entries)
    
    if df.empty:
        st.info("Loggfør mer data for å få en analyse.")
        return
        
    # --- 1. FILTERING BASED ON ACTIVE WINDOW ---
    # Start with last 7 days (standard analysis window), excluding today
    history_df = df[df["Date"] < date.today()]
    recent = history_df.tail(7)

    # Retrieve history to find active start date
    history = manager.get_window_history()
    active_start_date = None
    
    # Standard: Find active period (end_date=None)
    for period in history:
        if period.get("end_date") is None:
            active_start_date = period.get("start_date")
            break
            
    # Fallback if no active period found (should logically not happen if initialized correctly)
    if not active_start_date or not isinstance(active_start_date, str):
        # If dataset has dates, pick a very old one or just use all
        active_start_date = "2000-01-01"

    # Convert to date object for comparison
    try:
        active_start_dt = datetime.strptime(active_start_date, "%Y-%m-%d").date()
    except:
        active_start_dt = date(2000, 1, 1)

    # Create RELEVANT dataframe (subset of recent 7 days that are within active window)
    relevant_df = recent[recent["Date"] >= active_start_dt].copy()
    
    # Use relevant_df for all calculations
    # If we have no data in active period (e.g. just started today and no log yet), handle gracefully
    if relevant_df.empty:
        st.info(f"Ingen data funnet for nåværende periode (startet {active_start_date}). Loggfør data for å se statistikk.")
        return

    avg_se = relevant_df["SE"].mean()
    avg_tst = relevant_df["TST_min"].mean()
    avg_tib = relevant_df["TIB_min"].mean()
    
    def fmt_min(m):
        return f"{int(m // 60)}t {int(m % 60)}m"

    c1, c2, c3 = st.columns(3)
    c1.metric("Søvneffektivitet", f"{avg_se:.1f}%")
    c2.metric("Total søvn (TST)", fmt_min(avg_tst))
    c3.metric("Tid i seng (TIB)", fmt_min(avg_tib))
    
    st.divider()
    
    # Advice Logic
    curr_settings = manager.get_settings()
    curr_win = curr_settings.get("window_hours", 8.0)
    
    days_count = len(relevant_df)
    
    if days_count < 3:
        st.info(f"ℹ️ Nytt søvnvindu aktivert. Vi trenger minst 3 dager med data i denne perioden før vi gir nye råd. (Har {days_count} dager).")
    else:
        # Valid amount of data to give advice
        if avg_se > 85:
            st.success(f"""
            ### 👍 Godt jobbet! SE er {avg_se:.1f}% (> 85%)
            **Anbefaling:** ØK søvnvinduet med 15 minutter (til {format_hours_as_hm(curr_win + 0.25)}).
            *Legg deg 15 min tidligere eller stå opp 15 min senere.*
            """)
        elif avg_se < 80:
            if curr_win <= 5:
                st.warning(f"SE er {avg_se:.1f}%. Du er allerede på minimumsvindu (5t). Hold ut!")
            else:
                st.warning(f"""
                ### ⚠️ SE er {avg_se:.1f}% (< 80%)
                **Anbefaling:** REDUSER søvnvinduet med 15 minutter (til {format_hours_as_hm(curr_win - 0.25)}).
                *Legg deg 15 min senere eller stå opp 15 min før.*
                """)
        else:
            st.info(f"### 👌 SE er {avg_se:.1f}% (80-85%). Behold nåværende vindu.")
            
        # Add context about data basis if between 3 and 7 days
        if 3 <= days_count < 7:
            st.caption(f"(Basert på de siste {days_count} dagene i nåværende periode)")

    # --- VURDERING AV SØVN PÅ DAGTID ---
    st.divider()
    st.subheader("Vurdering av søvn på dagtid")
    
    # 1. Beregn nøkkeltall fra relevant_df
    days_with_naps = relevant_df[relevant_df["nap_minutes"] > 0].shape[0]
    total_naps_min = relevant_df["nap_minutes"].sum()
    # Pass på å dele på antall loggførte dager, ikke nødvendigvis 7 hvis man har logget færre
    num_logged_days = len(relevant_df)
    avg_nap_min_per_day = (total_naps_min / num_logged_days) if num_logged_days > 0 else 0
    
    # 2. Lag kjerne-budskap basert på ANTALL DAGER med naps
    if days_with_naps == 0:
        msg_type = "success"
        main_msg = "Du har **ikke loggført søvn på dagtid** i denne perioden. Dette er veldig bra for å bygge opp solid søvntrykk til kvelden!"
    elif days_with_naps == 1:
        msg_type = "info"
        main_msg = "Du har loggført **én dag** med søvn på dagtid. Dette er normalt innimellom, men vær oppmerksom på at det kan redusere søvntrykket ditt noe."
    elif 2 <= days_with_naps <= 3:
        msg_type = "info" # Tydeligere info
        main_msg = f"Du har loggført **{days_with_naps} dager** med søvn på dagtid. Dette kan begynne å svekke effekten av søvnrestriksjonen. Prøv å begrense dagsoving."
    else: # >= 4
        msg_type = "warning"
        main_msg = f"Du har loggført **{days_with_naps} dager** med søvn på dagtid (nesten daglig). Dette vil sannsynligvis motvirke søvnrestriksjons-behandlingen. Anbefalingen er å **unngå søvn på dagtid** helt i denne perioden."

    # 3. Legg til nyansering basert på GJENNOMSNITTLIG VARIGHET
    if days_with_naps > 0:
        if avg_nap_min_per_day < 10:
            duration_msg = f"Gjennomsnittlig varighet er lav (**{avg_nap_min_per_day:.1f} min**). Dette har vanligvis liten betydning, men følg med."
        elif 10 <= avg_nap_min_per_day < 30:
            duration_msg = f"Gjennomsnittlig varighet er **{avg_nap_min_per_day:.1f} min**. Dette kan redusere søvntrykket. Hvis du må sove, hold det under 10-15 minutter."
        else: # >= 30
            duration_msg = f"Gjennomsnittlig varighet er **{avg_nap_min_per_day:.1f} min**. Dette gir en sannsynlig merkbar reduksjon i søvntrykk. Prøv å kutte ut disse lurene."
            # Hvis vi allerede har warning, behold warning. Hvis vi har info, kanskje oppgrader til warning? 
            # Oppgaveteksten sier ">= 30 min: sannsynlig merkbar reduksjon...".
            # La oss la 'days_with_naps >= 4' styre hoved-warningen, men hvis varigheten er lang, blir teksten strengere.
            if msg_type == "info":
                msg_type = "warning" # Oppgraderer til warning hvis lurene er lange, selv om det er få dager?
                # Oppgavetekst eksplisitt: "Plasser boksen... bruk st.info for milde nivåer og st.warning for de strengere".
                # La oss holde det enkelt: Vi legger duration_msg til main_msg.
        
        full_msg = f"{main_msg}\n\n*{duration_msg}*"
    else:
        full_msg = main_msg

    # 4. Vis boksen
    if msg_type == "success":
        st.success(full_msg)
    elif msg_type == "warning":
        st.warning(full_msg)
    else:
        st.info(full_msg)

    # --- ETTERLEVELSE AV SØVNVINDU ---
    st.divider()
    st.subheader("Etterlevelse av søvnvindu")
    
    adherent_days: int = 0
    total_days_checked: int = 0
    
    # Calculate adherence for relevant days
    def check_row_adherence(row) -> bool:
        try:
            log_date = row["Date"]
            plan = manager.get_window_for_date(log_date)
            
            target_wake = time.fromisoformat(plan["target_wake"])
            window_hours = plan["window_hours"]
            
            # Logic: Target Wake - Window
            dummy_date = date(2000, 1, 1)
            wake_dt = datetime.combine(dummy_date, target_wake)
            plan_bed_dt = wake_dt - timedelta(hours=window_hours)
            
            # Re-construct absolute planned wake for this log entry
            target_wake_dt = datetime.combine(log_date + timedelta(days=1), target_wake)
            planned_bed_dt = target_wake_dt - timedelta(hours=window_hours)
            
            actual_bed_dt = row["bed_dt"]
            actual_out_dt = row["out_dt"]
            
            bed_diff_seconds = abs((actual_bed_dt - planned_bed_dt).total_seconds())
            bed_diff_min = bed_diff_seconds / 60
            
            wake_diff_seconds = abs((actual_out_dt - target_wake_dt).total_seconds())
            wake_diff_min = wake_diff_seconds / 60
            
            return bed_diff_min <= 30 and wake_diff_min <= 30
        except Exception:
            return False

    results = [check_row_adherence(row) for _, row in relevant_df.iterrows()]
    adherent_days = sum(results)
    total_days_checked = len(results)
            
    if total_days_checked > 0:
        c1, c2 = st.columns(2)
        c1.metric("Netter innenfor vindu (±30 min)", f"{adherent_days} / {total_days_checked}")
        st.caption("Dette målet handler kun om du legger deg og står opp til planlagt tid (±30 min), ikke om hvor lenge du sover.")
        
        adherence_rate = adherent_days / total_days_checked
        
        if adherence_rate >= 0.7: # Approx 5/7 days
            if avg_se > 85:
                # High adherence, high SE -> Ready to expand?
                st.success("🌟 Du er veldig flink til å holde vinduet ditt! Kombinert med høy søvneffektivitet, er du i god posisjon til å utvide vinduet hvis du kjenner at du trenger mer søvn.")
            else:
                # High adherence, low SE -> Supportive, normalizing message
                st.info("👍 Du følger søvnvinduet ditt svært godt. Det er helt normalt at søvneffektiviteten kan være lav en periode selv om du gjør alt riktig. Fortsett å holde tider for legging og oppvåkning, så vil vi bruke analysen over tid til å vurdere små justeringer.")
        elif adherence_rate < 0.3: # Low adherence
             st.warning("⚠️ Mange kvelder og morgener ligger mer enn ±30 minutter fra planen for leggetid og oppvåkning. For å få effekt av søvnbegrensningen er det viktig at du fokuserer på tidspunktet for seng og oppvåkning, selv om søvnen ennå ikke kommer som ønsket.")
        else:
             st.info("Du treffer vinduet noen netter, men prøv å bli enda mer konsekvent på tider for å legge deg og stå opp.")
    else:
        st.caption("Ikke nok data til å beregne etterlevelse.")

    st.caption("Oppdater målene dine under 'Din søvnplan' i menyen.")

    # --- CONTROL TABLE ---
    st.divider()
    with st.expander("Se datagrunnlag (Active Window)"):
        st.caption(f"Viser data fra startdato for nåværende periode: {active_start_date}")
        
        # Prepare display dataframe
        display_df = relevant_df.copy()
        display_df["Dato"] = display_df["Date"].astype(str)
        display_df["SE (%)"] = display_df["SE"].round(1)
        display_df["TST (t:m)"] = display_df["TST_min"].apply(fmt_min)
        display_df["TIB (t:m)"] = display_df["TIB_min"].apply(fmt_min)
        
        st.dataframe(
            display_df[["Dato", "SE (%)", "TST (t:m)", "TIB (t:m)"]],
            hide_index=True,
            width="stretch"
        )

def render_report_content(filtered_df, start_date, end_date, print_mode=False):
    """
    Renders report content based on print_mode:
    - False: Normal view (metrics, table, chart)
    - "report": Text-only print (metrics, table - no chart)
    - "chart": Chart-only print (just the Gantt chart)
    """
    # --- METRICS CALCULATION ---
    avg_se = filtered_df["SE"].mean()
    avg_tst_min = filtered_df["TST_min"].mean()
    def fmt_hm(m): return f"{int(m // 60)}t {int(m % 60)}m"
    avg_tib_min = filtered_df["TIB_min"].mean()
    
    total_waso_list = []
    for _, row in filtered_df.iterrows():
        w_sum = sum(a["duration_min"] for a in row["awakenings"])
        total_waso_list.append(w_sum)
        
    avg_waso = sum(total_waso_list) / len(total_waso_list) if total_waso_list else 0
    num_nights = len(filtered_df)
    avg_nap_min = filtered_df["nap_minutes"].mean() if "nap_minutes" in filtered_df.columns else 0

    # --- TABLE GENERATION (Aligned for text view) ---
    def generate_aligned_table(df):
        headers = ["Dato", "SE", "TST", "TIB", "WASO", "Nap"]
        widths = [6, 7, 8, 8, 6, 6]
        
        # Build header
        head_line = "|"
        sep_line = "|"
        for h, w in zip(headers, widths):
             head_line += f" {h:<{w}} |"
             sep_line += f" {'-'*w} |"
        
        md = head_line + "\n" + sep_line + "\n"
        
        for _, row in df.sort_values("Date").iterrows():
            d_str = row["Date"].strftime("%d.%m")
            se_val = f"{row['SE']:.1f}%"
            tst_str = fmt_hm(row['TST_min'])
            tib_str = fmt_hm(row['TIB_min'])
            w_sum = sum(a["duration_min"] for a in row["awakenings"])
            nap_val = row.get("nap_minutes", 0)
            
            vals = [d_str, se_val, tst_str, tib_str, f"{w_sum}m", f"{nap_val}m"]
            row_line = "|"
            for v, w in zip(vals, widths):
                row_line += f" {v:<{w}} |"
            md += row_line + "\n"
        return md

    table_md = generate_aligned_table(filtered_df)

    # --- MODE: TEXT REPORT or NORMAL ---
    if print_mode == "report" or not print_mode:
        
        # Prepare metrics string
        metrics_md = f"""- SE: {avg_se:.1f}%
- TST: {fmt_hm(avg_tst_min)}
- TIB: {fmt_hm(avg_tib_min)}
- WASO: {int(avg_waso)} min
- Nap: {int(avg_nap_min)} min"""

        if print_mode == "report":
            # --- PRINT MODE ---
            st.markdown(f"""### Rapport (søvndagbok)
**Periode:** {start_date} – {end_date}
**Datagrunnlag:** {num_nights} netter logget.

#### Nøkkeltall (snitt):
{metrics_md}
""")
            st.divider()
            st.markdown("#### Dag-for-dag:")
            st.code(table_md, language="text")

        else:
            # --- NORMAL MODE ---
            # Visual metrics
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Netter", f"{num_nights}")
            m2.metric("Snitt SE", f"{avg_se:.1f}%")
            m3.metric("Snitt TST", fmt_hm(avg_tst_min))
            m4.metric("Snitt TIB", fmt_hm(avg_tib_min))
            m5.metric("Snitt WASO", f"{int(avg_waso)} min")
            m6.metric("Snitt Nap", f"{int(avg_nap_min)} min")

            st.divider()

            # Prepare text for copy/paste
            copy_text = f"""### Rapport (søvndagbok)
Periode: {start_date} – {end_date}
Datagrunnlag: {num_nights} netter logget.

Nøkkeltall (snitt):
{metrics_md}

Dag-for-dag:

{table_md}
"""
            # Display readable markdown in UI
            st.markdown(copy_text)
            
            with st.expander("Kopier rapporttekst"):
                 st.code(copy_text, language="markdown")

    # --- MODE: CHART or NORMAL ---
    if print_mode == "chart":
        user_name = st.session_state.data['meta']['name']
        st.markdown(f'<h3 style="margin-bottom: 0.2em;">Døgnrytme: {user_name} ({start_date} – {end_date})</h3>', unsafe_allow_html=True)
        # Tip for landscape printing (hidden in print CSS)
        st.caption("Tips: Velg 'Liggende' papirretning i utskriftsdialogen.")
        
        fig_gantt = build_sleep_gantt_figure(filtered_df, for_print=True)
        # Landscape size for print - compressed to fit A4
        fig_gantt.update_layout(
            width=880, 
            height=420,
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
            font={"size": 10}
        )
        st.plotly_chart(fig_gantt, width="content")
        
    elif not print_mode:
        # NORMAL MODE - show chart
        st.subheader("Døgnrytme for perioden")
        fig_gantt = build_sleep_gantt_figure(filtered_df, for_print=False)
        st.plotly_chart(fig_gantt, width="stretch")
        st.caption("Forklaring: SE = Søvneffektivitet, TST = Total Søvntid, TIB = Tid i Seng, WASO = Tid våken etter innsovning.")

# --- WEEKLY REPORT VIEW ---
def render_weekly_report_view(manager):
    """
    Renders the Reports & Print view.
    Handles 'print_mode' state to toggle between the interactive app view and properly formatted
    print layouts (Text Report or Gantt Chart).
    """
    # CHECK PRINT MODE (False, "report", or "chart")
    print_mode = st.session_state.get("print_mode", False)
    
    if print_mode:
        # Hide Sidebar & Header
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            @media print {
                .stButton, header, footer, .stCaption { display: none !important; }
                /* Tving hovedcontainer til A4-bredde og fjern padding */
                .main .block-container {
                    padding: 10mm !important;
                    margin: 0 auto !important;
                }
                /* Skaler ned innholdet litt for å få plass til mer vertikalt */
                body {
                    font-size: 12pt !important;
                    overflow: hidden; /* Skjul scrollbars på utskrift */
                }
                /* Tving Plotly til å respektere bredden */
                .stPlotlyChart {
                    width: 100% !important;
                }
                /* Sørg for at Plotly-grafen ikke blør utover */
                .js-plotly-plot, .plot-container {
                    width: 100% !important;
                }
            }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("🔙 Tilbake til appen"):
            st.session_state.print_mode = False
            st.rerun()

    if not print_mode:
        st.header("📝 Rapporter og utskrifter")
    else:
        if print_mode == "report":
            st.markdown("## Rapport (søvndagbok)")
            st.markdown(f"**Navn:** {st.session_state.data['meta']['name']}")
        # Chart mode gets its title in render_report_content
    
    data = st.session_state.data["entries"]
    if not data:
        st.info("Ingen data å vise.")
        return

    # --- PROCESS DATA ---
    df = process_log_data(data)
    if df.empty:
        st.info("Ingen gyldige data.")
        return
        
    start_date = date.today() - timedelta(days=7)
    end_date = date.today() - timedelta(days=1)

    if not print_mode:
        # --- DATE FILTER (Normal Mode) ---
        st.write("") 
        c_filter, c_info = st.columns([1, 2])
        
        with c_filter:
            filter_mode = st.radio("Periode", ["Siste 7 dager", "Velg periode"], horizontal=True, label_visibility="collapsed", key="report_period")
            
        with c_info:
            if filter_mode == "Siste 7 dager":
                st.caption(f"Viser rapport for siste uke ({start_date} til {end_date}).")
                st.session_state["report_start"] = start_date
                st.session_state["report_end"] = end_date
            else:
                c_start, c_end = st.columns(2)
                def_start = date.today() - timedelta(days=14)
                start_date = c_start.date_input("Fra dato", value=def_start, key="rep_start")
                end_date = c_end.date_input("Til dato", value=date.today() - timedelta(days=1), key="rep_end")
                st.session_state["report_start"] = start_date
                st.session_state["report_end"] = end_date

        # --- TWO PRINT BUTTONS ---
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("🖨️ Skriv ut Rapport (Tekst)"):
                st.session_state.print_mode = "report"
                st.rerun()
        with c_p2:
            if st.button("🖨️ Skriv ut Døgnrytme (Graf)"):
                st.session_state.print_mode = "chart"
                st.rerun()

    else:
        # --- PRINT MODE ---
        # Retrieve dates from session state if available, else default
        start_date = st.session_state.get("report_start", start_date)
        end_date = st.session_state.get("report_end", end_date)

    # Apply Filter
    mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
    filtered_df = df.loc[mask]
    
    if filtered_df.empty:
        st.info(f"Ingen data funnet i perioden {start_date} til {end_date}.")
        return

    st.divider()
    
    # Render Content
    render_report_content(filtered_df, start_date, end_date, print_mode=print_mode)

# --- RUN ---
if __name__ == "__main__":
    manager = SleepDataManager()
    if st.session_state.data is None:
        render_welcome_view(manager)
    else:
        render_main_app(manager)
