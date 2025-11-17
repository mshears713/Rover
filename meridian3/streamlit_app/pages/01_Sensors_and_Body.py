"""
Chapter 1: Sensors and Body

TEACHING FOCUS:
    - Rover physical state representation
    - Sensor suite overview (IMU, power monitors, thermal sensors)
    - Reading sensor data
    - Understanding sensor specifications

NARRATIVE:
    A rover is a collection of sensors wrapped around a mobility system.
    Understanding what the rover can measure - and what it cannot - is
    the foundation of telemetry engineering.

LEARNING OBJECTIVES:
    - Identify the sensors in the Meridian-3 suite
    - Understand sensor accuracy and precision
    - Read and interpret raw sensor frames
    - Recognize the difference between state and measurement

ARCHITECTURE:
    Sensors are the interface between physical reality and digital telemetry.
    They transform continuous physical quantities (temperature, voltage, angle)
    into discrete digital values that can be transmitted and processed.

    Physical World → Sensors → Digital Telemetry → Processing

TEACHING APPROACH:
    - Interactive exploration of each sensor type
    - Statistical analysis of sensor noise
    - Comparison of true state vs. measured state
    - Hands-on experimentation with sensor parameters

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 32.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Sensors and Body", page_icon="📡", layout="wide")

st.title("📡 Chapter 1: Sensors and Body")

st.markdown("""
## Understanding the Rover as a Sensor Platform

A rover doesn't "know" where it is or what's happening to it. It only knows
what its sensors tell it. This chapter explores the sensor suite that gives
Meridian-3 awareness of its state.
""")

# ═══════════════════════════════════════════════════════════════════════════
# SENSOR SUITE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Sensor Suite Specifications", expanded=True):
    st.markdown("""
    ```
    ┌────────────────────────────────────────────────────────────────┐
    │                   MERIDIAN-3 SENSOR SUITE                      │
    └────────────────────────────────────────────────────────────────┘

         ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
         │     IMU     │        │    Power    │        │   Thermal   │
         │             │        │   Monitor   │        │    Array    │
         │  📐 Gyro    │        │  🔋 Battery │        │  🌡️  Temps  │
         │  📐 Accel   │        │  ☀️  Solar  │        │             │
         └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
                │                      │                      │
                └──────────────────────┴──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  Telemetry Frame     │
                            │  (All sensor data)   │
                            └──────────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Inertial Measurement Unit (IMU)**
        - **Measures**: Roll, pitch, heading
        - **Noise**: ±0.1° (1-sigma)
        - **Drift**: 0.01°/hour
        - **Rate**: 10 Hz
        - **Use**: Orientation tracking
        """)

    with col2:
        st.markdown("""
        **Power Monitor**
        - **Measures**: Voltage, current, SoC
        - **Accuracy**: ±0.05V, ±10mA
        - **Rate**: 1 Hz
        - **Channels**: Battery + solar
        - **Use**: Energy management
        """)

    with col3:
        st.markdown("""
        **Thermal Array**
        - **Measures**: Subsystem temps
        - **Accuracy**: ±0.5°C
        - **Resolution**: 0.1°C
        - **Rate**: 1 Hz
        - **Use**: Thermal monitoring
        """)

# ═══════════════════════════════════════════════════════════════════════════
# KEY CONCEPT: STATE VS MEASUREMENT
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🎯 Key Concept: State vs. Measurement")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### True State (Unknowable)

    The **actual** physical configuration of the rover:
    - Exact position, orientation, temperature
    - Perfect, noiseless values
    - Only exists in simulation
    - Used as ground truth for comparison

    *In real missions, we never know the true state perfectly!*
    """)

with col2:
    st.markdown("""
    ### Measured State (Observable)

    What our **sensors** tell us:
    - Noisy readings with uncertainty
    - Subject to bias and drift
    - May be corrupted or missing
    - What the telemetry pipeline receives

    *This is our only window into the rover's condition.*
    """)

# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE SENSOR EXPLORATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🔬 Interactive Sensor Exploration")

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite

    # ═══════════════════════════════════════════════════════════════════════
    # EXPERIMENT 1: SENSOR NOISE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════

    st.markdown("### Experiment 1: Sensor Noise Characteristics")

    st.markdown("""
    Real sensors add **random noise** to their measurements. Let's collect
    multiple readings from a stationary rover to characterize this noise.
    """)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        num_samples = st.slider("Number of samples to collect",
                                min_value=50, max_value=500, value=200, step=50,
                                help="More samples give better statistical estimates")

    with col2:
        show_histograms = st.checkbox("Show histograms", value=True)

    with col3:
        run_exp1 = st.button("🔬 Run Experiment", type="primary", key="exp1")

    if run_exp1 or 'exp1_data' in st.session_state:
        if run_exp1:
            # Create stationary rover and sensor suite
            rover = RoverState()
            sensors = SensorSuite()

            # Collect sensor readings
            data = []
            for i in range(num_samples):
                frame = sensors.read_all(rover, mission_time=float(i))
                data.append({
                    'sample': i,
                    'true_roll': rover.roll,
                    'meas_roll': frame['roll'],
                    'true_battery_soc': rover.battery_soc,
                    'meas_battery_soc': frame['battery_soc'],
                    'true_cpu_temp': rover.cpu_temp,
                    'meas_cpu_temp': frame['cpu_temp'],
                    'meas_battery_voltage': frame['battery_voltage'],
                    'true_battery_voltage': rover.battery_voltage,
                })

            st.session_state['exp1_data'] = pd.DataFrame(data)

        df = st.session_state['exp1_data']

        # Calculate errors
        df['roll_error'] = df['meas_roll'] - df['true_roll']
        df['soc_error'] = df['meas_battery_soc'] - df['true_battery_soc']
        df['temp_error'] = df['meas_cpu_temp'] - df['true_cpu_temp']
        df['voltage_error'] = df['meas_battery_voltage'] - df['true_battery_voltage']

        # Display statistics
        st.markdown("#### 📊 Statistical Analysis")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "IMU Roll Error",
                f"{df['roll_error'].abs().mean():.3f}°",
                delta=f"σ = {df['roll_error'].std():.3f}°"
            )

        with col2:
            st.metric(
                "Battery SoC Error",
                f"{df['soc_error'].abs().mean():.2f}%",
                delta=f"σ = {df['soc_error'].std():.2f}%"
            )

        with col3:
            st.metric(
                "CPU Temp Error",
                f"{df['temp_error'].abs().mean():.2f}°C",
                delta=f"σ = {df['temp_error'].std():.2f}°C"
            )

        with col4:
            st.metric(
                "Battery V Error",
                f"{df['voltage_error'].abs().mean():.3f}V",
                delta=f"σ = {df['voltage_error'].std():.3f}V"
            )

        # Time series plots
        st.markdown("#### 📈 Measurement vs. True State Over Time")

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("IMU Roll Angle", "Battery State of Charge",
                          "CPU Temperature", "Battery Voltage"),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        # Roll plot
        fig.add_trace(go.Scatter(x=df['sample'], y=df['true_roll'],
                                name='True Roll', line=dict(color='blue', width=2),
                                legendgroup='roll'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['sample'], y=df['meas_roll'],
                                name='Measured Roll', mode='markers',
                                marker=dict(color='red', size=3, opacity=0.5),
                                legendgroup='roll'), row=1, col=1)

        # SoC plot
        fig.add_trace(go.Scatter(x=df['sample'], y=df['true_battery_soc'],
                                name='True SoC', line=dict(color='blue', width=2),
                                showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=df['sample'], y=df['meas_battery_soc'],
                                name='Measured SoC', mode='markers',
                                marker=dict(color='red', size=3, opacity=0.5),
                                showlegend=False), row=1, col=2)

        # Temperature plot
        fig.add_trace(go.Scatter(x=df['sample'], y=df['true_cpu_temp'],
                                name='True Temp', line=dict(color='blue', width=2),
                                showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['sample'], y=df['meas_cpu_temp'],
                                name='Measured Temp', mode='markers',
                                marker=dict(color='red', size=3, opacity=0.5),
                                showlegend=False), row=2, col=1)

        # Voltage plot
        fig.add_trace(go.Scatter(x=df['sample'], y=df['true_battery_voltage'],
                                name='True Voltage', line=dict(color='blue', width=2),
                                showlegend=False), row=2, col=2)
        fig.add_trace(go.Scatter(x=df['sample'], y=df['meas_battery_voltage'],
                                name='Measured Voltage', mode='markers',
                                marker=dict(color='red', size=3, opacity=0.5),
                                showlegend=False), row=2, col=2)

        fig.update_xaxes(title_text="Sample Number", row=2, col=1)
        fig.update_xaxes(title_text="Sample Number", row=2, col=2)
        fig.update_yaxes(title_text="Angle (°)", row=1, col=1)
        fig.update_yaxes(title_text="SoC (%)", row=1, col=2)
        fig.update_yaxes(title_text="Temp (°C)", row=2, col=1)
        fig.update_yaxes(title_text="Voltage (V)", row=2, col=2)

        fig.update_layout(height=600, showlegend=True,
                         legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                   xanchor="center", x=0.5))

        st.plotly_chart(fig, use_container_width=True)

        # Histograms if requested
        if show_histograms:
            st.markdown("#### 📊 Error Distribution Histograms")

            fig_hist = make_subplots(
                rows=1, cols=4,
                subplot_titles=("Roll Error", "SoC Error", "Temp Error", "Voltage Error"),
                horizontal_spacing=0.08
            )

            fig_hist.add_trace(go.Histogram(x=df['roll_error'], name='Roll',
                                           marker_color='steelblue', nbinsx=30), row=1, col=1)
            fig_hist.add_trace(go.Histogram(x=df['soc_error'], name='SoC',
                                           marker_color='green', nbinsx=30), row=1, col=2)
            fig_hist.add_trace(go.Histogram(x=df['temp_error'], name='Temp',
                                           marker_color='orange', nbinsx=30), row=1, col=3)
            fig_hist.add_trace(go.Histogram(x=df['voltage_error'], name='Voltage',
                                           marker_color='purple', nbinsx=30), row=1, col=4)

            fig_hist.update_xaxes(title_text="Error (°)", row=1, col=1)
            fig_hist.update_xaxes(title_text="Error (%)", row=1, col=2)
            fig_hist.update_xaxes(title_text="Error (°C)", row=1, col=3)
            fig_hist.update_xaxes(title_text="Error (V)", row=1, col=4)
            fig_hist.update_yaxes(title_text="Count", row=1, col=1)

            fig_hist.update_layout(height=350, showlegend=False)

            st.plotly_chart(fig_hist, use_container_width=True)

            st.info("""
            **📚 What to Notice:**
            - Error distributions are approximately **Gaussian** (bell-shaped)
            - Most errors are small, with rare large excursions
            - This is characteristic of electronic noise in real sensors
            - Statistical filtering can reduce the impact of this noise
            """)

    # ═══════════════════════════════════════════════════════════════════════
    # EXPERIMENT 2: COMPLETE SENSOR FRAME INSPECTION
    # ═══════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.markdown("### Experiment 2: Complete Sensor Frame Inspection")

    st.markdown("""
    A **telemetry frame** contains all sensor readings at a single point in time.
    Let's examine a complete frame to see all the data the rover generates.
    """)

    if st.button("📦 Generate Sensor Frame", type="primary", key="exp2"):
        rover = RoverState()
        sensors = SensorSuite()
        frame = sensors.read_all(rover, mission_time=0.0)

        st.markdown("#### Complete Telemetry Frame")

        # Organize frame data by subsystem
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🧭 IMU (Orientation)**")
            st.code(f"""
Roll:    {frame['roll']:.3f}°
Pitch:   {frame['pitch']:.3f}°
Heading: {frame['heading']:.3f}°
            """)

        with col2:
            st.markdown("**🔋 Power System**")
            st.code(f"""
Battery V:   {frame['battery_voltage']:.2f}V
Battery I:   {frame['battery_current']:.3f}A
Battery SoC: {frame['battery_soc']:.1f}%
Solar V:     {frame['solar_voltage']:.2f}V
Solar I:     {frame['solar_current']:.3f}A
            """)

        with col3:
            st.markdown("**🌡️ Thermal**")
            st.code(f"""
CPU Temp:     {frame['cpu_temp']:.1f}°C
Battery Temp: {frame['battery_temp']:.1f}°C
Motor Temp:   {frame['motor_temp']:.1f}°C
Chassis Temp: {frame['chassis_temp']:.1f}°C
            """)

        # Show raw frame as JSON
        with st.expander("🔍 View Raw Frame Data (JSON format)"):
            st.json(frame)

        st.success("""
        ✅ **This is what gets transmitted!**

        This telemetry frame will flow through the pipeline:
        1. **Packetizer** encodes it for transmission
        2. **Corruptor** simulates transmission errors
        3. **Cleaner** validates and reconstructs data
        4. **Anomaly Detector** flags unusual patterns
        5. **Storage** archives for mission analysis
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # EXPERIMENT 3: SENSOR COMPARISON TABLE
    # ═══════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.markdown("### Experiment 3: Multi-Sensor Comparison")

    st.markdown("""
    Compare multiple sensor readings side-by-side to understand the variation
    across the sensor suite.
    """)

    num_frames = st.slider("Number of frames to compare", 5, 20, 10, key="exp3")

    if st.button("📊 Collect Frames", type="primary", key="exp3_run"):
        rover = RoverState()
        sensors = SensorSuite()

        frames_data = []
        for i in range(num_frames):
            frame = sensors.read_all(rover, mission_time=float(i))
            frames_data.append({
                'Frame': i,
                'Roll (°)': f"{frame['roll']:.3f}",
                'Pitch (°)': f"{frame['pitch']:.3f}",
                'Battery V': f"{frame['battery_voltage']:.2f}",
                'Battery %': f"{frame['battery_soc']:.1f}",
                'CPU °C': f"{frame['cpu_temp']:.1f}",
                'Battery °C': f"{frame['battery_temp']:.1f}",
            })

        df_frames = pd.DataFrame(frames_data)
        st.dataframe(df_frames, use_container_width=True, hide_index=True)

        st.info("""
        💡 **Teaching Point**: Notice how readings vary slightly between frames
        even though the rover is stationary. This sensor noise is inherent to
        real hardware and must be accounted for in mission operations.
        """)

except ImportError as e:
    st.error(f"""
    ⚠️ **Simulator modules not found**

    Make sure the simulator has been implemented (Phase 2) and the path is correct.

    Error details: {str(e)}
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Chapter 1 Complete!**

You've learned:
- ✅ The Meridian-3 sensor suite composition
- ✅ Difference between true state and measurements
- ✅ Statistical characteristics of sensor noise
- ✅ Structure of telemetry frames

**Next Steps**: Proceed to Chapter 2 to learn about time, orbital mechanics,
and how the Martian environment affects sensor readings.
""")

st.markdown("*Navigate to Chapter 2: Time and Orbits in the sidebar →*")
