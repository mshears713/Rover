"""
Chapter 8: Mission Console

TEACHING FOCUS:
    - Real-time mission monitoring
    - Telemetry visualization and dashboards
    - Alert handling and response
    - Mission timeline and playback

NARRATIVE:
    This is the mission operations center - where engineers monitor the rover's
    health, respond to alerts, and plan activities. It integrates all previous
    chapters into a unified console for mission management.

LEARNING OBJECTIVES:
    - Monitor real-time telemetry streams
    - Interpret dashboard visualizations
    - Respond to alerts and anomalies
    - Review mission timeline and events

ARCHITECTURE:
    Complete Pipeline → Live Display
    - All modules integrated
    - Real-time data flow
    - Interactive controls

TEACHING APPROACH:
    - Simulated live telemetry
    - Interactive dashboard
    - Alert monitoring
    - Playback controls

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 39.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import time as pytime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(page_title="Mission Console", page_icon="🎛️", layout="wide")
st.title("🎛️ Chapter 8: Mission Console")

st.markdown("""
## Mission Operations Center

Welcome to the nerve center of Meridian-3 operations. This is where all
the simulation, telemetry, cleaning, and anomaly detection come together
in a unified interface.
""")

with st.expander("🖥️ Console Architecture", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │              MISSION CONSOLE ARCHITECTURE                    │
    └──────────────────────────────────────────────────────────────┘

    Simulation → Sensors → Packets → Cleaner → Anomaly Detector
                                                        │
                                                        ▼
                              ┌─────────────────────────────────┐
                              │    MISSION CONSOLE DISPLAY      │
                              ├─────────────────────────────────┤
                              │  📊 Telemetry Dashboard         │
                              │  🚨 Alert Monitor               │
                              │  📈 Real-time Plots             │
                              │  ⏯️  Playback Controls          │
                              │  📋 Event Timeline              │
                              └─────────────────────────────────┘
    ```
    """)

st.markdown("---")
st.markdown("## 🎛️ Mission Status Dashboard")

# Initialize session state for simulation
if 'sim_running' not in st.session_state:
    st.session_state.sim_running = False
if 'mission_time' not in st.session_state:
    st.session_state.mission_time = 0
if 'telemetry_history' not in st.session_state:
    st.session_state.telemetry_history = []

# Mission controls
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("▶️ Start Mission" if not st.session_state.sim_running else "⏸️ Pause Mission",
                type="primary", key="sim_control"):
        st.session_state.sim_running = not st.session_state.sim_running

with col2:
    if st.button("🔄 Reset Mission"):
        st.session_state.mission_time = 0
        st.session_state.telemetry_history = []
        st.session_state.sim_running = False

with col3:
    speed = st.selectbox("Playback Speed", ["1x", "2x", "5x", "10x"], index=0)
    speed_mult = int(speed.replace("x", ""))

with col4:
    history_len = st.slider("History (samples)", 20, 200, 100, step=20)

# Generate telemetry snapshot
def generate_telemetry_snapshot(mission_time):
    """Generate realistic telemetry at given mission time"""
    # Simulated values with realistic variations
    solar_angle = max(0, 90 * np.sin(2 * np.pi * mission_time / 88775))  # Sol cycle
    battery_soc = 85 - 0.001 * mission_time + 5 * np.sin(2 * np.pi * mission_time / 88775)
    battery_voltage = 26 + 2 * (battery_soc / 100) + np.random.normal(0, 0.1)
    cpu_temp = 35 + 15 * (solar_angle / 90) + np.random.normal(0, 2)
    solar_power = max(0, 80 * np.sin(np.radians(solar_angle))) + np.random.normal(0, 3)

    # Check for anomalies
    anomalies = []
    if battery_soc < 30:
        anomalies.append("Low battery")
    if cpu_temp > 65:
        anomalies.append("High CPU temp")
    if solar_power < 10 and solar_angle > 20:
        anomalies.append("Solar degradation")

    return {
        'time': mission_time,
        'battery_soc': max(0, min(100, battery_soc)),
        'battery_voltage': battery_voltage,
        'cpu_temp': cpu_temp,
        'solar_power': max(0, solar_power),
        'solar_angle': solar_angle,
        'anomalies': anomalies
    }

# Current telemetry snapshot
current = generate_telemetry_snapshot(st.session_state.mission_time)

# Display current status
st.markdown("### 📊 Current Telemetry")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    sol_num = int(st.session_state.mission_time / 88775)
    st.metric("Mission Time", f"Sol {sol_num}",
             delta=f"{st.session_state.mission_time % 88775:.0f}s")

with col2:
    delta_color = "normal" if current['battery_soc'] > 50 else "inverse"
    st.metric("Battery SoC", f"{current['battery_soc']:.1f}%",
             delta=f"{current['battery_voltage']:.1f}V")

with col3:
    temp_status = "🟢" if current['cpu_temp'] < 60 else "🟡" if current['cpu_temp'] < 70 else "🔴"
    st.metric("CPU Temp", f"{temp_status} {current['cpu_temp']:.1f}°C")

with col4:
    st.metric("Solar Power", f"{current['solar_power']:.0f}W",
             delta=f"Angle: {current['solar_angle']:.0f}°")

with col5:
    alert_count = len(current['anomalies'])
    st.metric("Active Alerts", f"{'🚨' if alert_count > 0 else '✅'} {alert_count}")

# Show alerts if any
if current['anomalies']:
    st.warning(f"⚠️ **Alerts**: {', '.join(current['anomalies'])}")

st.markdown("---")

# Telemetry plots
st.markdown("### 📈 Live Telemetry Plots")

# Update telemetry history
if st.session_state.sim_running:
    st.session_state.mission_time += speed_mult
    st.session_state.telemetry_history.append(current)
    # Keep only recent history
    if len(st.session_state.telemetry_history) > history_len:
        st.session_state.telemetry_history = st.session_state.telemetry_history[-history_len:]

    # Auto-refresh
    pytime.sleep(0.1)
    st.rerun()

# Create plots from history
if st.session_state.telemetry_history:
    history = st.session_state.telemetry_history
    times = [h['time'] for h in history]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Battery State of Charge", "CPU Temperature",
                       "Solar Power Generation", "Battery Voltage"),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    # Battery SoC
    socs = [h['battery_soc'] for h in history]
    fig.add_trace(go.Scatter(x=times, y=socs, mode='lines+markers',
                            name='Battery SoC', line=dict(color='green', width=2),
                            marker=dict(size=4)), row=1, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="red", row=1, col=1)

    # CPU Temp
    temps = [h['cpu_temp'] for h in history]
    fig.add_trace(go.Scatter(x=times, y=temps, mode='lines+markers',
                            name='CPU Temp', line=dict(color='orange', width=2),
                            marker=dict(size=4)), row=1, col=2)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=2)

    # Solar Power
    powers = [h['solar_power'] for h in history]
    fig.add_trace(go.Scatter(x=times, y=powers, mode='lines+markers',
                            name='Solar Power', line=dict(color='gold', width=2),
                            marker=dict(size=4), fill='tozeroy'), row=2, col=1)

    # Battery Voltage
    voltages = [h['battery_voltage'] for h in history]
    fig.add_trace(go.Scatter(x=times, y=voltages, mode='lines+markers',
                            name='Battery V', line=dict(color='blue', width=2),
                            marker=dict(size=4)), row=2, col=2)

    fig.update_xaxes(title_text="Mission Time (s)", row=2, col=1)
    fig.update_xaxes(title_text="Mission Time (s)", row=2, col=2)
    fig.update_yaxes(title_text="SoC (%)", row=1, col=1)
    fig.update_yaxes(title_text="Temp (°C)", row=1, col=2)
    fig.update_yaxes(title_text="Power (W)", row=2, col=1)
    fig.update_yaxes(title_text="Voltage (V)", row=2, col=2)

    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key="live_plots")
else:
    st.info("👆 Click **Start Mission** to begin telemetry generation")

st.markdown("---")

# Mission Event Log
st.markdown("### 📋 Mission Event Log")

if st.session_state.telemetry_history:
    # Extract anomaly events
    events = []
    for snapshot in st.session_state.telemetry_history[-20:]:  # Last 20 snapshots
        if snapshot['anomalies']:
            for anomaly in snapshot['anomalies']:
                events.append({
                    'Time': f"{int(snapshot['time'])}s",
                    'Event': anomaly,
                    'SoC': f"{snapshot['battery_soc']:.1f}%",
                    'Temp': f"{snapshot['cpu_temp']:.1f}°C"
                })

    if events:
        df_events = pd.DataFrame(events)
        st.dataframe(df_events, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No anomalies detected - all systems nominal")
else:
    st.info("Event log will appear during mission operations")

st.markdown("---")

# Mission Statistics
if st.session_state.telemetry_history and len(st.session_state.telemetry_history) > 10:
    st.markdown("### 📊 Mission Statistics")

    history = st.session_state.telemetry_history
    total_energy = sum([h['solar_power'] for h in history]) * 0.1 / 3600  # kWh (assuming 0.1s per sample)
    avg_temp = np.mean([h['cpu_temp'] for h in history])
    min_soc = min([h['battery_soc'] for h in history])
    anomaly_count = sum([len(h['anomalies']) for h in history])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Energy Collected", f"{total_energy:.3f} kWh")
    with col2:
        st.metric("Avg CPU Temp", f"{avg_temp:.1f}°C")
    with col3:
        st.metric("Min Battery SoC", f"{min_soc:.1f}%")
    with col4:
        st.metric("Total Anomalies", f"{anomaly_count}")

st.markdown("---")

st.success("""
**🎓 Chapter 8 Complete!**

You've learned:
- ✅ Mission console dashboard design
- ✅ Real-time telemetry visualization
- ✅ Alert monitoring and event logging
- ✅ Mission controls (start/stop/playback)
- ✅ Integration of all pipeline components
- ✅ Operational mission management

**Next Steps**: Proceed to Chapter 9 to learn about post-mission analysis
and the mission archive system.
""")

st.markdown("*Navigate to Chapter 9: Post-Mission Archive in the sidebar →*")
