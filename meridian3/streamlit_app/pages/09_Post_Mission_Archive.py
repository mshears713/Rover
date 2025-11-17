"""
Chapter 9: Post-Mission Archive

TEACHING FOCUS:
    - Mission data archival and retrieval
    - SQLite database queries
    - Historical analysis and replay
    - Report generation

NARRATIVE:
    After a mission (or mission segment) completes, the data is archived for
    analysis. The archive browser allows you to review missions, compare runs,
    and generate reports - essential for learning from experience.

LEARNING OBJECTIVES:
    - Query mission database by time range
    - Replay historical telemetry
    - Compare multiple missions
    - Generate analysis reports

ARCHITECTURE:
    Telemetry → Storage → Archive → Analysis
    - SQLite for persistent storage
    - Indexed queries for fast retrieval
    - Export capabilities

TEACHING APPROACH:
    - Mission browser interface
    - Historical data visualization
    - Event timeline reconstruction
    - Statistical analysis tools

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 40.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(page_title="Post-Mission Archive", page_icon="📂", layout="wide")
st.title("📂 Chapter 9: Post-Mission Archive")

st.markdown("""
## Mission Data Archive and Analysis

Every mission generates thousands of telemetry frames. The archive system
stores, indexes, and retrieves this data for analysis and learning.
""")

with st.expander("💾 Archive Structure", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │                 MISSION ARCHIVE SYSTEM                       │
    └──────────────────────────────────────────────────────────────┘

    📦 SQLite Database (missions.sqlite)
       ├─ telemetry_frames table
       │  ├─ frame_id, mission_id, timestamp
       │  ├─ sensor values (voltage, temp, soc, etc.)
       │  └─ quality metadata
       │
       ├─ mission_metadata table
       │  ├─ mission_id, start_time, end_time
       │  ├─ duration, total_frames
       │  └─ anomaly_count, performance_metrics
       │
       └─ Indexes for fast queries
          ├─ idx_mission_time
          └─ idx_anomalies

    📊 Analysis Capabilities
       ├─ Time-range queries
       ├─ Multi-mission comparison
       ├─ Statistical summaries
       └─ Data export (CSV, JSON)
    ```
    """)

st.markdown("---")

# Generate sample archived missions
def generate_sample_missions():
    """Create synthetic mission archive for demonstration"""
    missions = []
    base_date = datetime(2025, 1, 1)

    for i in range(5):
        start_date = base_date + timedelta(days=i*7)
        duration_hours = np.random.randint(4, 24)
        num_frames = duration_hours * 3600  # 1 Hz
        num_anomalies = np.random.randint(2, 15)

        missions.append({
            'Mission ID': f"M-{2025010 + i}",
            'Start Time': start_date.strftime("%Y-%m-%d %H:%M"),
            'Duration': f"{duration_hours}h",
            'Frames': f"{num_frames:,}",
            'Anomalies': num_anomalies,
            'Status': np.random.choice(['Complete', 'Complete', 'Partial'])
        })

    return pd.DataFrame(missions)

st.markdown("## 📚 Mission Archive Browser")

# Mission list
missions_df = generate_sample_missions()
st.dataframe(missions_df, use_container_width=True, hide_index=True)

# Mission selector
col1, col2 = st.columns([2, 1])
with col1:
    selected_mission = st.selectbox("Select mission for analysis",
                                   missions_df['Mission ID'].tolist())
with col2:
    st.metric("Total Archived Missions", len(missions_df))

st.markdown("---")

# Simulated mission data for selected mission
st.markdown(f"## 📊 Mission Analysis: {selected_mission}")

mission_row = missions_df[missions_df['Mission ID'] == selected_mission].iloc[0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Start Time", mission_row['Start Time'])
with col2:
    st.metric("Duration", mission_row['Duration'])
with col3:
    st.metric("Total Frames", mission_row['Frames'])
with col4:
    st.metric("Anomalies", mission_row['Anomalies'])

# Generate synthetic historical data for visualization
duration_hours = int(mission_row['Duration'].replace('h', ''))
num_points = min(500, duration_hours * 60)  # Downsample for visualization
time_points = np.linspace(0, duration_hours * 3600, num_points)

# Synthetic telemetry
battery_soc = 100 - (time_points / 3600) * 2 + 10 * np.sin(2 * np.pi * time_points / 88775)
battery_soc = np.clip(battery_soc + np.random.normal(0, 2, num_points), 0, 100)

cpu_temp = 40 + 10 * np.sin(2 * np.pi * time_points / 88775) + np.random.normal(0, 3, num_points)

solar_power = np.maximum(0, 80 * np.sin(2 * np.pi * time_points / 88775)) + np.random.normal(0, 5, num_points)
solar_power = np.clip(solar_power, 0, 100)

# Inject some anomalies
num_anomalies = mission_row['Anomalies']
anomaly_indices = np.random.choice(num_points, num_anomalies, replace=False)
anomaly_times = time_points[anomaly_indices]

st.markdown("### 📈 Historical Telemetry Plots")

fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=("Battery State of Charge", "CPU Temperature", "Solar Power"),
    vertical_spacing=0.1,
    row_heights=[0.33, 0.33, 0.34]
)

# Battery plot
fig.add_trace(go.Scatter(x=time_points/3600, y=battery_soc,
                        mode='lines', name='Battery SoC',
                        line=dict(color='green', width=1.5)), row=1, col=1)
# Mark anomalies
for at in anomaly_times:
    fig.add_vline(x=at/3600, line_dash="dash", line_color="red",
                 opacity=0.3, row=1, col=1)

# Temperature plot
fig.add_trace(go.Scatter(x=time_points/3600, y=cpu_temp,
                        mode='lines', name='CPU Temp',
                        line=dict(color='orange', width=1.5)), row=2, col=1)
for at in anomaly_times:
    fig.add_vline(x=at/3600, line_dash="dash", line_color="red",
                 opacity=0.3, row=2, col=1)

# Solar plot
fig.add_trace(go.Scatter(x=time_points/3600, y=solar_power,
                        mode='lines', name='Solar Power',
                        line=dict(color='gold', width=1.5),
                        fill='tozeroy'), row=3, col=1)
for at in anomaly_times:
    fig.add_vline(x=at/3600, line_dash="dash", line_color="red",
                 opacity=0.3, row=3, col=1)

fig.update_xaxes(title_text="Mission Time (hours)", row=3, col=1)
fig.update_yaxes(title_text="SoC (%)", row=1, col=1)
fig.update_yaxes(title_text="Temp (°C)", row=2, col=1)
fig.update_yaxes(title_text="Power (W)", row=3, col=1)

fig.update_layout(height=700, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.info("""
📍 **Red dashed lines** indicate detected anomaly events in the historical data.
""")

st.markdown("---")

# Event Timeline
st.markdown("### 📅 Event Timeline")

events = []
for i, at in enumerate(anomaly_times[:10]):  # Show up to 10 events
    event_types = ['Low Battery', 'High CPU Temp', 'Power Spike', 'Sensor Glitch', 'Dust Storm']
    events.append({
        'Event Time': f"{at/3600:.2f}h",
        'Event Type': np.random.choice(event_types),
        'Severity': np.random.choice(['Low', 'Medium', 'High']),
        'Duration': f"{np.random.randint(10, 300)}s"
    })

if events:
    events_df = pd.DataFrame(events)
    st.dataframe(events_df, use_container_width=True, hide_index=True)

st.markdown("---")

# Performance Metrics
st.markdown("### 📊 Mission Performance Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_battery = np.mean(battery_soc)
    st.metric("Avg Battery SoC", f"{avg_battery:.1f}%")

with col2:
    max_temp = np.max(cpu_temp)
    st.metric("Peak CPU Temp", f"{max_temp:.1f}°C")

with col3:
    total_energy = np.trapz(solar_power, time_points) / 3600000  # kWh
    st.metric("Energy Collected", f"{total_energy:.2f} kWh")

with col4:
    data_quality = np.random.uniform(92, 99)
    st.metric("Data Quality", f"{data_quality:.1f}%")

st.markdown("---")

# Export Options
st.markdown("### 📤 Data Export")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Export CSV"):
        st.success("✅ CSV export would download telemetry data")

with col2:
    if st.button("📥 Export JSON"):
        st.success("✅ JSON export would download structured data")

with col3:
    if st.button("📄 Generate Report"):
        st.success("✅ PDF report would be generated with analysis")

st.markdown("---")

# Mission Comparison
st.markdown("### 🔄 Multi-Mission Comparison")

st.markdown("""
Compare key metrics across multiple archived missions to identify trends
and performance patterns.
""")

# Generate comparison data
comparison_missions = missions_df['Mission ID'].tolist()[:4]
comparison_data = {
    'Mission': comparison_missions,
    'Avg Battery': [np.random.uniform(60, 85) for _ in range(4)],
    'Peak Temp': [np.random.uniform(55, 75) for _ in range(4)],
    'Energy (kWh)': [np.random.uniform(1.5, 3.5) for _ in range(4)],
    'Anomaly Rate': [np.random.uniform(0.5, 3.0) for _ in range(4)]
}

fig_comp = go.Figure()

fig_comp.add_trace(go.Bar(x=comparison_data['Mission'],
                         y=comparison_data['Avg Battery'],
                         name='Avg Battery (%)',
                         marker_color='green'))

fig_comp.update_layout(
    title="Mission Comparison: Average Battery SoC",
    xaxis_title="Mission ID",
    yaxis_title="Average Battery SoC (%)",
    height=350
)

st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

st.success("""
**🎓 Chapter 9 Complete!**

You've learned:
- ✅ Mission archive structure and organization
- ✅ Historical data query and retrieval
- ✅ Event timeline reconstruction
- ✅ Performance metrics analysis
- ✅ Multi-mission comparison tools
- ✅ Data export capabilities

**Congratulations!** You've completed the Meridian-3 interactive tutorial.
Navigate to Chapter 10 for the Engineering Legacy and system reference.
""")

st.markdown("*Navigate to Chapter 10: Engineering Legacy in the sidebar →*")
