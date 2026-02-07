# © 2026 Asbjørn Hval Bergestuen
# Licensed under the MIT License. See the LICENSE file for details.

import streamlit as st
import json
import os
from datetime import datetime, time, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
                    "window_hours": 8.0
                }
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

    def save_settings(self, target_wake, window_hours):
        if st.session_state.data is None:
            return
        
        st.session_state.data["meta"]["settings"] = {
            "target_wake": target_wake.strftime("%H:%M:%S"),
            "window_hours": float(window_hours)
        }
        self._save_to_disk(st.session_state.filepath, st.session_state.data)
        st.success("Innstillinger lagret!")

    def get_settings(self):
        if st.session_state.data:
            return st.session_state.data["meta"].get("settings", {
                "target_wake": "07:00:00",
                "window_hours": 8.0
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

# --- SHARED HELPERS (Data Processing) ---
def process_log_data(data_entries):
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
        se = max(0, min(100, se))
        
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

def render_landing_page(manager):
    render_custom_css()
    st.title("🌙 Søvndagbok")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ny Dagbok")
        with st.form("new_user_form"):
            new_name = st.text_input("Ditt navn")
            filename = st.text_input("Filnavn", value="min_sovndagbok.json")
            save_dir = st.session_state.current_browser_dir
            st.caption(f"Lagres i: {save_dir}")
            
            if st.form_submit_button("Opprett ny"):
                if manager.create_new_log(new_name, save_dir, filename):
                    st.rerun()

    with col2:
        st.subheader("Åpne Fil")
        current_path = st.session_state.current_browser_dir
        st.text(f"📍 {current_path}")
        
        if st.button("⬆️ Gå opp"):
            st.session_state.current_browser_dir = os.path.dirname(current_path)
            st.rerun()
        
        try:
            items = os.listdir(current_path)
            dirs = [d for d in items if os.path.isdir(os.path.join(current_path, d)) and not d.startswith('.')]
            files = [f for f in items if f.endswith('.json')]
            
            st.markdown("**Mapper:**")
            cols = st.columns(3)
            for i, d in enumerate(dirs):
                if cols[i % 3].button(f"📁 {d}", key=f"dir_{d}"):
                    st.session_state.current_browser_dir = os.path.join(current_path, d)
                    st.rerun()
            
            st.markdown("**Filer:**")
            for f in files:
                full_path = os.path.join(current_path, f)
                if st.button(f"📄 {f}", key=f"file_{f}"):
                    if manager.load_log(full_path):
                        st.rerun()
                        
        except PermissionError:
            st.error("Ingen tilgang til denne mappen.")

def render_main_app(manager):
    render_custom_css()
    data = st.session_state.data
    meta = data["meta"]
    
    with st.sidebar:
        st.markdown(f"### 👤 {meta['name']}")
        mode = st.radio("Meny", ["📅 Plan", "✍️ Loggføring", "📊 Visualisering", "📈 Analyse", "📂 Rådata"])
        st.divider()
        if st.button("Lukk Dagbok"):
            st.session_state.data = None
            st.session_state.filepath = None
            st.rerun()

    if mode == "📅 Plan":
        render_plan_view(manager)
    elif mode == "✍️ Loggføring":
        render_logging_view(manager)
    elif mode == "📊 Visualisering":
        render_viz_view(manager)
    elif mode == "📈 Analyse":
        render_analysis_view(manager)
    elif mode == "📂 Rådata":
        render_rawdata_view(manager)

def render_plan_view(manager):
    st.header("📅 Din Søvnplan")
    st.info("Sett dine mål her. Disse brukes som standardverdier i loggen.")
    
    current_settings = manager.get_settings()
    
    with st.form("settings_form"):
        try:
            curr_wake = time.fromisoformat(current_settings["target_wake"])
        except ValueError:
            curr_wake = time(7, 0)
            
        curr_window = current_settings.get("window_hours", 8.0)
        
        c1, c2 = st.columns(2)
        target_wake = c1.time_input("Mål for oppvåkning", value=curr_wake)
        window_hours = c2.number_input("Søvnvindu (timer)", value=float(curr_window), step=0.25)
        
        wake_dt = datetime.combine(date.today(), target_wake)
        bed_dt = wake_dt - timedelta(hours=window_hours)
        st.markdown(f"**Anbefalt leggetid:** {bed_dt.strftime('%H:%M')}")
        
        if st.form_submit_button("Lagre Plan"):
            manager.save_settings(target_wake, window_hours)

def render_logging_view(manager):
    st.header("✍️ Daglig Loggføring")
    
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
        st.session_state.log_date = date.today()
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

    if st.button("💾 Lagre Dagbok", type="primary"):
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

    # --- NORMALIZATION LOGIC (FOR GANTT) ---
    def normalize(dt_obj):
        base_d1 = date(2000, 1, 1)
        base_d2 = date(2000, 1, 2)
        t = dt_obj.time()
        if t.hour >= 16:
            return datetime.combine(base_d1, t)
        else:
            return datetime.combine(base_d2, t)

    # --- GRAF 1: SE ---
    st.subheader("Søvneffektivitet (SE)")
    
    fig_se = px.line(df, x="DateLabel", y="SE", markers=True)
    fig_se.update_traces(line_color='#0067C5', marker=dict(size=9, line=dict(width=2, color='white')))

    fig_se.update_layout(
        font=dict(color='#262626'), # Tving sort tekst
        yaxis=dict(
            range=[0, 105], 
            title="SE (%)", 
            showgrid=True, 
            gridcolor='#D1D1D1',
            zeroline=False
        ),
        xaxis=dict(
            type='category',
            title="Dato",
            showgrid=True,
            gridwidth=1,
            gridcolor='#D1D1D1' 
        ),
        legend=dict(font=dict(color='#262626'))
    )
    fig_se.add_hline(y=85, line_dash="dash", line_color="#06893A", annotation_text="Mål (85%)")
    st.plotly_chart(fig_se, use_container_width=True)

    # --- GRAF 2: GANTT ---
    st.divider()
    st.subheader("Døgnrytme (Søvnmønster)")
    st.caption("Viser hele døgnet fra 18:00 til 18:00.")

    fig_gantt = go.Figure()

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
        # 2. Sleep Time (approximated as Bed + Latency to Wake) - simplified visualization
        # Ideally: Bed->Lights->Onset->Wake->Out
        # Let's draw Onset to Wake as Blue
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

    fig_gantt.update_layout(
        font=dict(color='#262626'),
        barmode='overlay',
        height=max(400, len(df_rev)*60),
        legend=dict(orientation="h", y=1.1, font=dict(color='#262626')),
        yaxis=dict(
            title="Dato",
            type='category',
            categoryorder='array',
            categoryarray=df_rev["DateLabel"].tolist() # Tvinger rekkefølgen til å matche DataFramen
        ),
        xaxis=dict(
            type='linear',
            range=[0, TOTAL_MS], # FIXED RANGE 18:00 - 18:00
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_text,
            showgrid=True,
            gridcolor='#D1D1D1'
        )
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

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
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Dato": st.column_config.TextColumn("Dato", width="medium"),
            "Oppvåkninger detaljer": st.column_config.TextColumn("Oppvåkninger", width="large"),
        }
    )

def render_analysis_view(manager):
    st.header("📈 Analyse & Råd (CBT-i)")
    data_entries = st.session_state.data["entries"]
    df = process_log_data(data_entries)
    
    if df.empty:
        st.info("Loggfør mer data for å få en analyse.")
        return
        
    recent = df.tail(7)
    avg_se = recent["SE"].mean()
    avg_tst = recent["TST_min"].mean()
    avg_tib = recent["TIB_min"].mean()
    
    def fmt_min(m):
        return f"{int(m // 60)}t {int(m % 60)}m"

    c1, c2, c3 = st.columns(3)
    c1.metric("Søvneffektivitet", f"{avg_se:.1f}%")
    c2.metric("Total Søvn (TST)", fmt_min(avg_tst))
    c3.metric("Tid i Seng (TIB)", fmt_min(avg_tib))
    
    st.divider()
    
    # Advice Logic
    curr_settings = manager.get_settings()
    curr_win = curr_settings.get("window_hours", 8.0)
    
    if avg_se > 85:
        st.success(f"""
        ### 👍 Godt jobbet! SE er {avg_se:.1f}% (> 85%)
        **Anbefaling:** ØK søvnvinduet med 15 minutter (til {curr_win + 0.25}t).
        *Legg deg 15 min tidligere eller stå opp 15 min senere.*
        """)
    elif avg_se < 80:
        if curr_win <= 5:
            st.warning(f"SE er {avg_se:.1f}%. Du er allerede på minimumsvindu (5t). Hold ut!")
        else:
            st.warning(f"""
            ### ⚠️ SE er {avg_se:.1f}% (< 80%)
            **Anbefaling:** REDUSER søvnvinduet med 15 minutter (til {curr_win - 0.25}t).
            *Legg deg 15 min senere eller stå opp 15 min før.*
            """)
    else:
        st.info(f"### 👌 SE er {avg_se:.1f}% (80-85%). Behold nåværende vindu.")

    # --- VURDERING AV SØVN PÅ DAGTID ---
    st.divider()
    st.subheader("Vurdering av søvn på dagtid")
    
    # 1. Beregn nøkkeltall fra recent_df (siste 7 dager)
    days_with_naps = recent[recent["nap_minutes"] > 0].shape[0]
    total_naps_min = recent["nap_minutes"].sum()
    # Pass på å dele på antall loggførte dager, ikke nødvendigvis 7 hvis man har logget færre
    num_logged_days = len(recent)
    avg_nap_min_per_day = (total_naps_min / num_logged_days) if num_logged_days > 0 else 0
    
    # 2. Lag kjerne-budskap basert på ANTALL DAGER med naps
    if days_with_naps == 0:
        msg_type = "success"
        main_msg = "Du har **ikke loggført søvn på dagtid** den siste uken. Dette er veldig bra for å bygge opp solid søvntrykk til kvelden!"
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
    
    st.caption("Oppdater målene dine under 'Plan' i menyen.")

# --- RUN ---
if __name__ == "__main__":
    manager = SleepDataManager()
    if st.session_state.data is None:
        render_landing_page(manager)
    else:
        render_main_app(manager)
