"""
Appendix A: How Sensor Data is Generated

TEACHING FOCUS:
    - Understanding the rover state representation
    - How sensors add realistic noise to measurements
    - The simulation pipeline from state to sensor readings
    - Detailed code walkthrough with examples

NARRATIVE:
    This appendix provides a deep dive into how the Meridian-3 rover
    creates sensor data from scratch. It covers the RoverState class,
    sensor noise models, and the complete data generation pipeline.

LEARNING OBJECTIVES:
    - Understand the "source of truth" rover state
    - Learn how realistic sensor noise is modeled
    - See the relationship between true state and measurements
    - Master the sensor data generation architecture

ARCHITECTURE:
    The sensor data generation pipeline has three main components:
    1. RoverState: The ground truth physical state
    2. SensorSuite: Noise models that corrupt perfect measurements
    3. Telemetry Frames: The final output sent to the pipeline

TEACHING APPROACH:
    - Interactive exploration of RoverState
    - Hands-on noise model experimentation
    - Visual comparison of true vs measured values
    - Statistical analysis of sensor behavior

IMPLEMENTATION:
    Full interactive implementation following patterns from Chapters 1-3.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(
    page_title="Appendix A: Sensor Data Generation",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Appendix A: How Sensor Data is Generated")

st.markdown("""
## From Physical State to Digital Telemetry

Every piece of telemetry begins as a **physical state** - the rover's actual
configuration in the real (or simulated) world. This appendix explores how
that perfect state becomes noisy, realistic sensor measurements.

Understanding this process is critical for interpreting telemetry and
distinguishing real anomalies from sensor artifacts.
""")

# ═══════════════════════════════════════════════════════════════════════════
# ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Sensor Data Generation Architecture", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │           SENSOR DATA GENERATION PIPELINE                    │
    └──────────────────────────────────────────────────────────────┘

         ┌─────────────────┐
         │   RoverState    │  Ground Truth (Perfect)
         │  ─────────────  │
         │  • Position     │  - Exact physical configuration
         │  • Orientation  │  - No noise or uncertainty
         │  • Temperatures │  - Only exists in simulation
         │  • Voltages     │  - Used as reference
         │  • Currents     │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  SensorSuite    │  Noise Models
         │  ─────────────  │
         │  IMU Sensor     │  + Gaussian noise
         │  Power Monitor  │  + Bias and drift
         │  Thermal Array  │  + Quantization
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Telemetry Frame │  Noisy Measurements
         │  ─────────────  │
         │  {             │  - What gets transmitted
         │   "roll": 0.12 │  - Includes all errors
         │   "temp": 25.3 │  - Realistic sensor data
         │   ...          │
         │  }             │
         └─────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **RoverState (Ground Truth)**
        - All physical quantities
        - Perfect accuracy
        - Updated by simulation
        - Not observable in reality
        - Reference for validation
        """)

    with col2:
        st.markdown("""
        **SensorSuite (Noise Models)**
        - Gaussian random noise
        - Systematic bias
        - Time-dependent drift
        - Quantization effects
        - Temperature sensitivity
        """)

    with col3:
        st.markdown("""
        **Telemetry Frame (Output)**
        - Dictionary of measurements
        - Timestamp included
        - All sensors in one frame
        - Ready for packetization
        - What pipeline receives
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: ROVER STATE EXPLORER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: RoverState Explorer")

st.markdown("""
The **RoverState** class represents the rover's complete physical configuration.
Let's create a rover state and explore all its properties.
""")

try:
    from simulator.rover_state import RoverState

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Customize Initial State:**")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            custom_roll = st.slider("Roll (°)", -30.0, 30.0, 0.0, 0.5, key="exp1_roll")
            custom_pitch = st.slider("Pitch (°)", -30.0, 30.0, 0.0, 0.5, key="exp1_pitch")

        with col_b:
            custom_heading = st.slider("Heading (°)", 0.0, 360.0, 0.0, 5.0, key="exp1_heading")
            custom_battery_soc = st.slider("Battery SoC (%)", 0.0, 100.0, 85.0, 1.0, key="exp1_soc")

        with col_c:
            custom_cpu_temp = st.slider("CPU Temp (°C)", -40.0, 80.0, 25.0, 1.0, key="exp1_cpu")
            custom_battery_temp = st.slider("Battery Temp (°C)", -40.0, 60.0, 20.0, 1.0, key="exp1_batt")

    with col2:
        if st.button("🔬 Create RoverState", type="primary", key="exp1_create"):
            st.session_state['exp1_rover'] = True

    if st.session_state.get('exp1_rover', False):
        # Create rover with custom values
        rover = RoverState()
        rover.roll = custom_roll
        rover.pitch = custom_pitch
        rover.heading = custom_heading
        rover.battery_soc = custom_battery_soc
        rover.cpu_temp = custom_cpu_temp
        rover.battery_temp = custom_battery_temp

        st.markdown("### 📊 Complete RoverState Snapshot")

        # Display all state variables in organized groups
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**🧭 Orientation (IMU)**")
            st.metric("Roll", f"{rover.roll:.2f}°")
            st.metric("Pitch", f"{rover.pitch:.2f}°")
            st.metric("Heading", f"{rover.heading:.2f}°")

        with col2:
            st.markdown("**🔋 Power System**")
            st.metric("Battery Voltage", f"{rover.battery_voltage:.2f}V")
            st.metric("Battery Current", f"{rover.battery_current:.3f}A")
            st.metric("Battery SoC", f"{rover.battery_soc:.1f}%")
            st.metric("Solar Voltage", f"{rover.solar_voltage:.2f}V")
            st.metric("Solar Current", f"{rover.solar_current:.3f}A")

        with col3:
            st.markdown("**🌡️ Thermal System**")
            st.metric("CPU Temp", f"{rover.cpu_temp:.1f}°C")
            st.metric("Battery Temp", f"{rover.battery_temp:.1f}°C")
            st.metric("Motor Temp", f"{rover.motor_temp:.1f}°C")
            st.metric("Chassis Temp", f"{rover.chassis_temp:.1f}°C")

        with col4:
            st.markdown("**📍 Position**")
            st.metric("Latitude", f"{rover.latitude:.6f}°")
            st.metric("Longitude", f"{rover.longitude:.6f}°")
            st.metric("Altitude", f"{rover.altitude:.1f}m")

        # Visualize orientation
        st.markdown("### 🎯 Orientation Visualization")

        fig = go.Figure()

        # Create a simple 3D representation using roll, pitch, heading
        fig.add_trace(go.Scatterpolar(
            r=[90-abs(rover.roll), 90-abs(rover.pitch), rover.heading/4],
            theta=['Roll', 'Pitch', 'Heading'],
            fill='toself',
            name='Orientation'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 90])
            ),
            showlegend=False,
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **📚 Key Observations:**
        - The **RoverState** contains all physical quantities in perfect form
        - This is the "ground truth" used to validate sensor measurements
        - In a real mission, you never know the true state - only measurements
        - The simulation uses this to model sensor behavior realistically
        """)

except ImportError as e:
    st.error(f"⚠️ Simulator modules not found. Error: {str(e)}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: SENSOR NOISE APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Sensor Noise Models")

st.markdown("""
Real sensors corrupt perfect measurements with **noise**. Let's see how different
noise models transform the true state into realistic sensor readings.
""")

try:
    from simulator.sensors import SensorSuite

    col1, col2, col3 = st.columns(3)

    with col1:
        sensor_type = st.selectbox(
            "Select sensor to analyze",
            ["IMU (Roll)", "Power (Battery SoC)", "Thermal (CPU Temp)", "Power (Battery Voltage)"],
            key="exp2_sensor"
        )

    with col2:
        noise_sigma = st.slider(
            "Noise σ (standard deviation)",
            0.0, 2.0, 0.3, 0.05,
            help="Increase to see more noise",
            key="exp2_sigma"
        )

    with col3:
        num_samples = st.slider(
            "Number of samples",
            50, 500, 200, 50,
            help="More samples = better statistics",
            key="exp2_samples"
        )

    if st.button("🔬 Generate Noisy Measurements", type="primary", key="exp2_run"):
        rover = RoverState()
        sensors = SensorSuite()

        # Map sensor selection to state variable
        sensor_map = {
            "IMU (Roll)": ("roll", "°"),
            "Power (Battery SoC)": ("battery_soc", "%"),
            "Thermal (CPU Temp)": ("cpu_temp", "°C"),
            "Power (Battery Voltage)": ("battery_voltage", "V")
        }

        sensor_key, unit = sensor_map[sensor_type]

        # Collect measurements
        true_values = []
        measured_values = []

        for i in range(num_samples):
            frame = sensors.read_all(rover, mission_time=float(i))
            true_values.append(getattr(rover, sensor_key))
            measured_values.append(frame[sensor_key])

        true_values = np.array(true_values)
        measured_values = np.array(measured_values)
        errors = measured_values - true_values

        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("True Value", f"{true_values[0]:.3f}{unit}")

        with col2:
            st.metric(
                "Measured Mean",
                f"{measured_values.mean():.3f}{unit}",
                delta=f"Bias: {errors.mean():.3f}{unit}"
            )

        with col3:
            st.metric("Measured σ", f"{measured_values.std():.3f}{unit}")

        with col4:
            st.metric("Max Error", f"{np.abs(errors).max():.3f}{unit}")

        # Visualizations
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(f"{sensor_type} Time Series", "Error Distribution"),
            horizontal_spacing=0.12
        )

        # Time series
        fig.add_trace(
            go.Scatter(
                x=list(range(num_samples)),
                y=true_values,
                mode='lines',
                name='True Value',
                line=dict(color='red', width=2)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=list(range(num_samples)),
                y=measured_values,
                mode='markers',
                name='Measured',
                marker=dict(color='steelblue', size=4, opacity=0.6)
            ),
            row=1, col=1
        )

        # Histogram
        fig.add_trace(
            go.Histogram(
                x=errors,
                nbinsx=30,
                name='Error Distribution',
                marker_color='steelblue',
                opacity=0.7
            ),
            row=1, col=2
        )

        # Add Gaussian overlay
        x_range = np.linspace(errors.min(), errors.max(), 100)
        gaussian = (num_samples * (errors.max() - errors.min()) / 30) * \
                   (1 / (errors.std() * np.sqrt(2 * np.pi))) * \
                   np.exp(-0.5 * ((x_range - errors.mean()) / errors.std()) ** 2)

        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=gaussian,
                mode='lines',
                name='Gaussian Fit',
                line=dict(color='red', width=2)
            ),
            row=1, col=2
        )

        fig.update_xaxes(title_text="Sample Number", row=1, col=1)
        fig.update_xaxes(title_text=f"Error ({unit})", row=1, col=2)
        fig.update_yaxes(title_text=f"Value ({unit})", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=2)

        fig.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **📚 Key Observations:**
        - Sensor noise follows a **Gaussian (normal) distribution**
        - The measured mean approximates the true value (unbiased)
        - Individual measurements scatter around the truth
        - Error magnitude is characterized by standard deviation (σ)
        - This noise model matches real hardware behavior
        """)

except ImportError as e:
    st.error(f"⚠️ Sensor modules not found. Error: {str(e)}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: COMPLETE FRAME GENERATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Complete Telemetry Frame Generation")

st.markdown("""
A **telemetry frame** is the complete set of sensor readings at a single point in time.
Let's generate frames and see how the entire state → measurement transformation works.
""")

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite

    col1, col2 = st.columns([3, 1])

    with col1:
        num_frames = st.slider(
            "Number of frames to generate",
            1, 20, 5, 1,
            help="Generate multiple frames to see variation",
            key="exp3_frames"
        )

    with col2:
        if st.button("📦 Generate Frames", type="primary", key="exp3_run"):
            st.session_state['exp3_data'] = True

    if st.session_state.get('exp3_data', False):
        rover = RoverState()
        sensors = SensorSuite()

        frames_data = []

        for i in range(num_frames):
            frame = sensors.read_all(rover, mission_time=float(i))

            frames_data.append({
                'Frame': i,
                'Roll': f"{frame['roll']:.3f}",
                'Pitch': f"{frame['pitch']:.3f}",
                'Heading': f"{frame['heading']:.1f}",
                'Batt V': f"{frame['battery_voltage']:.2f}",
                'Batt %': f"{frame['battery_soc']:.1f}",
                'CPU °C': f"{frame['cpu_temp']:.1f}",
                'Batt °C': f"{frame['battery_temp']:.1f}",
                'Solar V': f"{frame['solar_voltage']:.2f}",
            })

        df = pd.DataFrame(frames_data)

        st.markdown("### 📊 Generated Telemetry Frames")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Show one frame in detail
        st.markdown("### 🔍 Frame 0 Detailed View")

        frame_0 = sensors.read_all(rover, mission_time=0.0)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Formatted Display:**")
            st.code(f"""
IMU Orientation:
  Roll:    {frame_0['roll']:.4f}°
  Pitch:   {frame_0['pitch']:.4f}°
  Heading: {frame_0['heading']:.4f}°

Power System:
  Battery Voltage: {frame_0['battery_voltage']:.3f}V
  Battery Current: {frame_0['battery_current']:.4f}A
  Battery SoC:     {frame_0['battery_soc']:.2f}%
  Solar Voltage:   {frame_0['solar_voltage']:.3f}V
  Solar Current:   {frame_0['solar_current']:.4f}A

Thermal System:
  CPU Temp:     {frame_0['cpu_temp']:.2f}°C
  Battery Temp: {frame_0['battery_temp']:.2f}°C
  Motor Temp:   {frame_0['motor_temp']:.2f}°C
  Chassis Temp: {frame_0['chassis_temp']:.2f}°C
            """, language="text")

        with col2:
            st.markdown("**Raw JSON Structure:**")
            st.json(frame_0)

        st.success("""
        **✅ This Frame is Ready for the Pipeline!**

        Next steps in the telemetry pipeline:
        1. **Packetizer** → Encode frame into binary packet
        2. **Corruptor** → Simulate transmission errors
        3. **Cleaner** → Validate and reconstruct data
        4. **Anomaly Detector** → Flag unusual patterns
        5. **Storage** → Archive for analysis
        """)

except ImportError as e:
    st.error(f"⚠️ Simulator modules not found. Error: {str(e)}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: NOISE MODEL DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Noise Model Deep Dive")

st.markdown("""
Let's explore how different noise parameters affect data quality.
We'll calculate **Signal-to-Noise Ratio (SNR)** and see when measurements become unreliable.
""")

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite

    col1, col2, col3 = st.columns(3)

    with col1:
        noise_level = st.slider(
            "Noise Level",
            0.1, 5.0, 0.5, 0.1,
            help="Higher = more noise",
            key="exp4_noise"
        )

    with col2:
        signal_value = st.slider(
            "Signal Amplitude",
            1.0, 100.0, 25.0, 1.0,
            help="The true value being measured",
            key="exp4_signal"
        )

    with col3:
        duration = st.slider(
            "Measurement Duration",
            10, 200, 100, 10,
            help="Number of samples to collect",
            key="exp4_duration"
        )

    # Calculate SNR
    snr_linear = signal_value / noise_level if noise_level > 0 else float('inf')
    snr_db = 20 * np.log10(snr_linear) if snr_linear > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("SNR (linear)", f"{snr_linear:.2f}")

    with col2:
        st.metric("SNR (dB)", f"{snr_db:.1f} dB")

    with col3:
        quality = "Excellent" if snr_db > 40 else "Good" if snr_db > 20 else "Fair" if snr_db > 10 else "Poor"
        st.metric("Signal Quality", quality)

    if st.button("🔬 Analyze Noise Impact", type="primary", key="exp4_run"):
        # Generate noisy measurements
        true_signal = np.ones(duration) * signal_value
        noise = np.random.normal(0, noise_level, duration)
        measured_signal = true_signal + noise

        # Calculate statistics
        rmse = np.sqrt(np.mean((measured_signal - true_signal) ** 2))
        max_error = np.max(np.abs(measured_signal - true_signal))

        # Visualization
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Measured Signal with Noise", "Measurement Error"),
            vertical_spacing=0.15,
            row_heights=[0.6, 0.4]
        )

        # Signal plot
        fig.add_trace(
            go.Scatter(
                x=list(range(duration)),
                y=true_signal,
                mode='lines',
                name='True Signal',
                line=dict(color='red', width=2, dash='dash')
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=list(range(duration)),
                y=measured_signal,
                mode='lines',
                name='Measured Signal',
                line=dict(color='steelblue', width=1)
            ),
            row=1, col=1
        )

        # Error plot
        fig.add_trace(
            go.Scatter(
                x=list(range(duration)),
                y=noise,
                mode='lines',
                name='Error',
                line=dict(color='orange', width=1),
                fill='tozeroy',
                fillcolor='rgba(255, 165, 0, 0.3)'
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text="Sample Number", row=2, col=1)
        fig.update_yaxes(title_text="Signal Value", row=1, col=1)
        fig.update_yaxes(title_text="Error", row=2, col=1)

        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

        # Error metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("RMSE", f"{rmse:.3f}")

        with col2:
            st.metric("Max Error", f"{max_error:.3f}")

        with col3:
            st.metric("Noise σ", f"{np.std(noise):.3f}")

        with col4:
            percent_error = (rmse / signal_value) * 100
            st.metric("% Error", f"{percent_error:.2f}%")

        st.info(f"""
        **📚 SNR Interpretation:**
        - **> 40 dB**: Excellent quality - noise barely visible
        - **20-40 dB**: Good quality - signal clearly distinguishable
        - **10-20 dB**: Fair quality - signal visible but noisy
        - **< 10 dB**: Poor quality - noise dominates, filtering required

        **Your SNR: {snr_db:.1f} dB** ({quality})
        """)

except ImportError as e:
    st.error(f"⚠️ Simulator modules not found. Error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Appendix A Complete!**

You've learned:
- ✅ RoverState structure and the concept of "ground truth"
- ✅ How SensorSuite applies realistic noise models
- ✅ The transformation from perfect state to noisy measurements
- ✅ Telemetry frame structure and generation
- ✅ Signal-to-noise ratio and data quality metrics
- ✅ Why sensor data is imperfect and how to characterize errors

**Connection to Mission**: Understanding sensor data generation is foundational
for interpreting telemetry, validating measurements, and distinguishing real
anomalies from sensor artifacts. Every analysis in the pipeline depends on
knowing what the sensors can and cannot tell us reliably.

**Next**: Proceed to Appendix B to see how these frames are encoded into packets for transmission.
""")

st.markdown("*Navigate to Appendix B: Data Packetization in the sidebar →*")
