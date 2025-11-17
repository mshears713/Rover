"""
Chapter 4: Terrain and Hazards

TEACHING FOCUS:
    - Terrain effects on rover operations
    - Hazardous event modeling (dust devils, radiation, slips)
    - Environmental state tracking
    - Stochastic event generation

NARRATIVE:
    The Martian environment is harsh and unpredictable. Dust devils appear
    with no warning. Radiation from solar events causes sensor glitches.
    The rover must adapt to terrain and survive hazards to complete its mission.

LEARNING OBJECTIVES:
    - Understand terrain property impacts (slope, surface type)
    - Model random hazard events using Poisson processes
    - Track environmental state over time
    - Recognize hazard signatures in telemetry

ARCHITECTURE:
    The Environment module maintains Mars state:
    - Terrain properties (slope, surface, roughness)
    - Time-based phenomena (day/night, solar angle)
    - Stochastic hazards (dust devils, radiation spikes)
    - Impact on rover sensors and power

TEACHING APPROACH:
    - Interactive terrain type selector
    - Hazard event demonstrations
    - Telemetry response visualization
    - Environmental effects on sensors

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 35.
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

st.set_page_config(page_title="Terrain and Hazards", page_icon="🏔️", layout="wide")

st.title("🏔️ Chapter 4: Terrain and Hazards")

st.markdown("""
## Surviving the Martian Environment

Mars is not a benign environment. The rover must contend with challenging
terrain, dust storms, radiation, and thermal extremes. This chapter explores
how environmental factors impact telemetry and operations.
""")

# ═══════════════════════════════════════════════════════════════════════════
# TERRAIN AND HAZARDS OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("🌍 Environmental Challenges Overview", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │            MARTIAN ENVIRONMENTAL HAZARDS                     │
    └──────────────────────────────────────────────────────────────┘

        ☀️ RADIATION SPIKES          🌪️ DUST DEVILS
        ├─ Solar particle events     ├─ Local dust storms
        ├─ Sensor bit flips          ├─ Solar panel coating
        ├─ CPU errors                ├─ Power reduction
        └─ 1 per 3 sols average      └─ 1 per sol in season

        🗻 TERRAIN SLOPE             🪨 SURFACE TYPE
        ├─ 0-5°: Easy                ├─ Firm: Nominal
        ├─ 5-15°: Moderate           ├─ Loose: +30% power
        ├─ 15-25°: Difficult         ├─ Rocky: High vibration
        └─ >25°: Dangerous           └─ Icy: Slip risk

        ⛷️ SLIP EVENTS                🌡️ THERMAL EXTREMES
        ├─ Sudden position change    ├─ -90°C night
        ├─ IMU spike                 ├─ +20°C day
        ├─ Depends on surface        ├─ Sensor noise increase
        └─ Recovery needed           └─ Component stress
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Terrain Properties**
        - Slope angle (affects power)
        - Surface type (affects traction)
        - Roughness (affects vibration)
        - Navigation difficulty
        """)

    with col2:
        st.markdown("""
        **Atmospheric Hazards**
        - Dust devils (power impact)
        - Dust storms (visibility)
        - Wind events (thermal)
        - Seasonal variations
        """)

    with col3:
        st.markdown("""
        **Space Weather**
        - Solar radiation (bit flips)
        - Particle events (glitches)
        - Cosmic rays (SEU/SEL)
        - Magnetic field variations
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: TERRAIN TYPE EFFECTS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Terrain Type Impact on Operations")

st.markdown("""
Different terrain types affect rover power consumption, sensor noise, and
navigation difficulty. Let's explore these effects.
""")

col1, col2 = st.columns([2, 1])

with col1:
    terrain_type = st.selectbox(
        "Select Terrain Type",
        ["Firm (Nominal)", "Loose Regolith", "Rocky", "Icy", "Dusty"],
        help="Each terrain has different operational characteristics"
    )

with col2:
    slope_angle = st.slider("Slope Angle (degrees)", 0, 30, 5, step=1,
                           help="Steeper slopes require more power")

# Define terrain properties
terrain_properties = {
    "Firm (Nominal)": {
        "power_factor": 1.0,
        "noise_factor": 1.0,
        "slip_prob": 0.01,
        "vibration": "Low",
        "description": "Ideal conditions - firm, flat surface"
    },
    "Loose Regolith": {
        "power_factor": 1.3,
        "noise_factor": 1.2,
        "slip_prob": 0.08,
        "vibration": "Medium",
        "description": "Sandy/dusty surface with reduced traction"
    },
    "Rocky": {
        "power_factor": 1.1,
        "noise_factor": 1.5,
        "slip_prob": 0.03,
        "vibration": "High",
        "description": "Rough surface with high vibration"
    },
    "Icy": {
        "power_factor": 0.9,
        "noise_factor": 1.1,
        "slip_prob": 0.15,
        "vibration": "Low",
        "description": "Slippery surface with low friction"
    },
    "Dusty": {
        "power_factor": 1.2,
        "noise_factor": 1.3,
        "slip_prob": 0.05,
        "vibration": "Medium",
        "description": "Dust-covered surface reducing solar efficiency"
    }
}

props = terrain_properties[terrain_type]

# Calculate slope impact
slope_power_factor = 1.0 + (slope_angle / 30) * 0.5  # Up to 50% more power for 30° slope
total_power_factor = props["power_factor"] * slope_power_factor

# Display terrain characteristics
st.markdown(f"### {terrain_type} Characteristics")
st.markdown(f"*{props['description']}*")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Power Factor", f"{total_power_factor:.2f}x",
             help="Multiply nominal power by this factor")

with col2:
    st.metric("Noise Factor", f"{props['noise_factor']:.2f}x",
             help="Sensor noise increases by this factor")

with col3:
    st.metric("Slip Probability", f"{props['slip_prob']*100:.1f}%",
             help="Chance of slip event per drive segment")

with col4:
    st.metric("Vibration Level", props['vibration'],
             help="Mechanical stress on sensors")

if st.button("🔬 Simulate Drive Segment", type="primary", key="terrain_exp1"):
    # Simulate a 10-minute drive
    time_points = 100
    time_minutes = np.linspace(0, 10, time_points)

    # Nominal values
    nominal_power = 20.0  # Watts
    nominal_velocity = 0.05  # m/s
    nominal_imu_noise = 0.1  # degrees

    # Calculate actual values
    actual_power = nominal_power * total_power_factor
    actual_velocity = nominal_velocity / (total_power_factor ** 0.5)  # Slower if more power needed
    actual_imu_noise = nominal_imu_noise * props['noise_factor']

    # Generate telemetry
    power_draw = np.random.normal(actual_power, actual_power * 0.1, time_points)
    velocity = np.random.normal(actual_velocity, actual_velocity * 0.05, time_points)
    imu_noise = np.random.normal(0, actual_imu_noise, time_points)

    # Add slip event if probability met
    if np.random.random() < props['slip_prob']:
        slip_time = np.random.randint(20, 80)
        velocity[slip_time:slip_time+5] *= 0.3  # Sudden velocity drop
        imu_noise[slip_time:slip_time+5] += np.random.normal(0, 5, 5)  # IMU spike

    # Visualize
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Power Consumption", "Velocity", "IMU Noise (Roll)"),
        vertical_spacing=0.12,
        row_heights=[0.33, 0.33, 0.34]
    )

    # Power
    fig.add_trace(go.Scatter(x=time_minutes, y=power_draw,
                            mode='lines', name='Power',
                            line=dict(color='orange', width=2),
                            fill='tozeroy'),
                 row=1, col=1)
    fig.add_hline(y=nominal_power, line_dash="dash", line_color="red",
                 annotation_text="Nominal", row=1, col=1)

    # Velocity
    fig.add_trace(go.Scatter(x=time_minutes, y=velocity,
                            mode='lines', name='Velocity',
                            line=dict(color='blue', width=2)),
                 row=2, col=1)
    fig.add_hline(y=nominal_velocity, line_dash="dash", line_color="red",
                 annotation_text="Nominal", row=2, col=1)

    # IMU noise
    fig.add_trace(go.Scatter(x=time_minutes, y=imu_noise,
                            mode='lines', name='IMU Noise',
                            line=dict(color='green', width=1)),
                 row=3, col=1)

    fig.update_xaxes(title_text="Time (minutes)", row=3, col=1)
    fig.update_yaxes(title_text="Power (W)", row=1, col=1)
    fig.update_yaxes(title_text="Velocity (m/s)", row=2, col=1)
    fig.update_yaxes(title_text="Roll Error (°)", row=3, col=1)

    fig.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Summary statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Avg Power", f"{np.mean(power_draw):.1f} W",
                 delta=f"+{np.mean(power_draw) - nominal_power:.1f} W")

    with col2:
        st.metric("Avg Velocity", f"{np.mean(velocity):.3f} m/s",
                 delta=f"{np.mean(velocity) - nominal_velocity:.3f} m/s")

    with col3:
        st.metric("IMU RMS Noise", f"{np.sqrt(np.mean(imu_noise**2)):.2f}°",
                 delta=f"{np.sqrt(np.mean(imu_noise**2)) - nominal_imu_noise:.2f}°")

    st.info(f"""
    **📚 Key Observations for {terrain_type}:**
    - Power consumption is **{total_power_factor:.2f}x** nominal
    - Sensor noise increased by **{props['noise_factor']:.2f}x**
    - Slip probability: **{props['slip_prob']*100:.1f}%** per drive
    - Vibration level: **{props['vibration']}**
    - This terrain type {('reduces' if total_power_factor < 1 else 'increases')} mission energy budget
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: DUST DEVIL EVENT
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Dust Devil Encounter")

st.markdown("""
Dust devils are local whirlwinds that can reduce solar power and coat sensors
with dust. They last 1-5 minutes and occur randomly, especially during
Martian spring/summer.
""")

col1, col2 = st.columns(2)

with col1:
    dust_devil_severity = st.select_slider(
        "Dust Devil Severity",
        options=["Light", "Moderate", "Heavy", "Severe"],
        value="Moderate",
        help="Severity affects power reduction and duration"
    )

with col2:
    dust_devil_duration = st.slider("Duration (minutes)", 1, 10, 3, step=1,
                                   help="How long the dust devil lasts")

severity_impact = {
    "Light": {"power_reduction": 0.15, "noise_increase": 1.3},
    "Moderate": {"power_reduction": 0.35, "noise_increase": 1.6},
    "Heavy": {"power_reduction": 0.55, "noise_increase": 2.0},
    "Severe": {"power_reduction": 0.75, "noise_increase": 2.5}
}

impact = severity_impact[dust_devil_severity]

if st.button("🔬 Simulate Dust Devil", type="primary", key="dust_exp2"):
    # Simulate 30-minute period with dust devil in the middle
    time_points = 300
    time_minutes = np.linspace(0, 30, time_points)

    # Event timing (start at 10 minutes, last for specified duration)
    event_start = 10
    event_end = event_start + dust_devil_duration

    # Normal solar power generation
    nominal_solar = 80.0  # Watts
    solar_power = np.ones(time_points) * nominal_solar

    # Add normal fluctuations
    solar_power += np.random.normal(0, 2, time_points)

    # Dust devil impact
    event_mask = (time_minutes >= event_start) & (time_minutes < event_end)
    solar_power[event_mask] *= (1 - impact["power_reduction"])

    # Sensor noise (temperature sensor as example)
    temp_noise = np.random.normal(0, 0.3, time_points)
    temp_noise[event_mask] *= impact["noise_increase"]

    # CPU temperature (affected by reduced cooling during dust devil)
    cpu_temp = 45 + np.random.normal(0, 2, time_points)
    cpu_temp[event_mask] += 10  # Heating during dust devil

    # Visualization
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Solar Power Generation", "Sensor Noise Amplitude", "CPU Temperature"),
        vertical_spacing=0.12,
        row_heights=[0.33, 0.33, 0.34]
    )

    # Solar power
    fig.add_trace(go.Scatter(x=time_minutes, y=solar_power,
                            mode='lines', name='Solar Power',
                            line=dict(color='orange', width=2),
                            fill='tozeroy', fillcolor='rgba(255,165,0,0.2)'),
                 row=1, col=1)

    # Mark event region
    fig.add_vrect(x0=event_start, x1=event_end,
                 fillcolor="red", opacity=0.15,
                 layer="below", line_width=0,
                 annotation_text=f"Dust Devil ({dust_devil_severity})",
                 annotation_position="top left",
                 row=1, col=1)

    # Sensor noise
    fig.add_trace(go.Scatter(x=time_minutes, y=np.abs(temp_noise),
                            mode='lines', name='Noise',
                            line=dict(color='steelblue', width=1)),
                 row=2, col=1)
    fig.add_vrect(x0=event_start, x1=event_end,
                 fillcolor="red", opacity=0.15,
                 layer="below", line_width=0,
                 row=2, col=1)

    # CPU temp
    fig.add_trace(go.Scatter(x=time_minutes, y=cpu_temp,
                            mode='lines', name='CPU Temp',
                            line=dict(color='red', width=2)),
                 row=3, col=1)
    fig.add_vrect(x0=event_start, x1=event_end,
                 fillcolor="red", opacity=0.15,
                 layer="below", line_width=0,
                 row=3, col=1)

    fig.update_xaxes(title_text="Time (minutes)", row=3, col=1)
    fig.update_yaxes(title_text="Power (W)", row=1, col=1)
    fig.update_yaxes(title_text="Noise (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Temp (°C)", row=3, col=1)

    fig.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Calculate impact metrics
    normal_power = solar_power[~event_mask]
    event_power = solar_power[event_mask]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Power Reduction", f"{impact['power_reduction']*100:.0f}%",
                 help=f"{dust_devil_severity} dust devil impact")

    with col2:
        st.metric("Avg Power Loss", f"{np.mean(normal_power) - np.mean(event_power):.1f} W",
                 help="Power lost during event")

    with col3:
        st.metric("Noise Increase", f"{impact['noise_increase']:.1f}x",
                 help="Sensor noise multiplier")

    with col4:
        st.metric("CPU Temp Rise", f"+{np.mean(cpu_temp[event_mask]) - np.mean(cpu_temp[~event_mask]):.1f}°C",
                 help="Temperature increase during event")

    st.warning(f"""
    **⚠️ Dust Devil Impact:**
    - Solar power reduced by **{impact['power_reduction']*100:.0f}%** during event
    - Sensor noise increased **{impact['noise_increase']:.1f}x**
    - Possible dust coating on solar panels (persists after event)
    - Temperature increase from reduced airflow cooling
    - **Mission Response**: Switch to battery, pause non-critical operations
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: RADIATION SPIKE EVENT
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Solar Radiation Spike")

st.markdown("""
Solar particle events can cause sensor glitches, bit flips in memory, and
temporary CPU errors. These are brief (10-60 seconds) but can corrupt data.
""")

col1, col2 = st.columns(2)

with col1:
    radiation_intensity = st.select_slider(
        "Radiation Intensity",
        options=["Low", "Moderate", "High", "Extreme"],
        value="Moderate",
        help="Higher intensity = more sensor corruption"
    )

with col2:
    radiation_duration = st.slider("Event Duration (seconds)", 10, 120, 30, step=10,
                                  help="How long the radiation spike lasts")

rad_impact = {
    "Low": {"corruption_rate": 0.02, "glitch_count": 1},
    "Moderate": {"corruption_rate": 0.05, "glitch_count": 3},
    "High": {"corruption_rate": 0.12, "glitch_count": 7},
    "Extreme": {"corruption_rate": 0.25, "glitch_count": 15}
}

rad_effect = rad_impact[radiation_intensity]

if st.button("🔬 Simulate Radiation Event", type="primary", key="rad_exp3"):
    # Simulate 5-minute period
    sample_rate = 10  # Hz
    time_points = 5 * 60 * sample_rate
    time_seconds = np.linspace(0, 300, time_points)

    # Event timing
    event_start_sec = 120
    event_end_sec = event_start_sec + radiation_duration

    # Generate normal sensor readings
    battery_voltage = 28.0 + np.random.normal(0, 0.1, time_points)
    cpu_temp = 45.0 + np.random.normal(0, 0.5, time_points)
    roll_angle = 0.0 + np.random.normal(0, 0.1, time_points)

    # Inject radiation-induced glitches during event
    event_mask = (time_seconds >= event_start_sec) & (time_seconds < event_end_sec)
    event_indices = np.where(event_mask)[0]

    # Randomly corrupt some readings during event
    num_corruptions = int(len(event_indices) * rad_effect["corruption_rate"])
    corrupt_indices = np.random.choice(event_indices, num_corruptions, replace=False)

    # Add glitches (sudden jumps, invalid values)
    for idx in corrupt_indices:
        glitch_type = np.random.choice(['spike', 'zero', 'random'])
        if glitch_type == 'spike':
            battery_voltage[idx] += np.random.uniform(-5, 5)
            cpu_temp[idx] += np.random.uniform(-20, 20)
            roll_angle[idx] += np.random.uniform(-10, 10)
        elif glitch_type == 'zero':
            battery_voltage[idx] = 0
            cpu_temp[idx] = 0
        else:
            battery_voltage[idx] = np.random.uniform(0, 50)
            cpu_temp[idx] = np.random.uniform(-50, 100)
            roll_angle[idx] = np.random.uniform(-180, 180)

    # Visualization
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Battery Voltage", "CPU Temperature", "IMU Roll Angle"),
        vertical_spacing=0.12,
        row_heights=[0.33, 0.33, 0.34]
    )

    # Battery voltage
    fig.add_trace(go.Scatter(x=time_seconds, y=battery_voltage,
                            mode='lines', name='Voltage',
                            line=dict(color='green', width=1)),
                 row=1, col=1)
    fig.add_vrect(x0=event_start_sec, x1=event_end_sec,
                 fillcolor="purple", opacity=0.15,
                 layer="below", line_width=0,
                 annotation_text=f"Radiation Spike ({radiation_intensity})",
                 annotation_position="top left",
                 row=1, col=1)

    # CPU temp
    fig.add_trace(go.Scatter(x=time_seconds, y=cpu_temp,
                            mode='lines', name='CPU Temp',
                            line=dict(color='orange', width=1)),
                 row=2, col=1)
    fig.add_vrect(x0=event_start_sec, x1=event_end_sec,
                 fillcolor="purple", opacity=0.15,
                 layer="below", line_width=0,
                 row=2, col=1)

    # Roll angle
    fig.add_trace(go.Scatter(x=time_seconds, y=roll_angle,
                            mode='lines', name='Roll',
                            line=dict(color='blue', width=1)),
                 row=3, col=1)
    fig.add_vrect(x0=event_start_sec, x1=event_end_sec,
                 fillcolor="purple", opacity=0.15,
                 layer="below", line_width=0,
                 row=3, col=1)

    fig.update_xaxes(title_text="Time (seconds)", row=3, col=1)
    fig.update_yaxes(title_text="Voltage (V)", row=1, col=1)
    fig.update_yaxes(title_text="Temp (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Angle (°)", row=3, col=1)

    fig.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Corrupted Samples", f"{num_corruptions}",
                 help="Number of sensor readings affected")

    with col2:
        st.metric("Corruption Rate", f"{rad_effect['corruption_rate']*100:.1f}%",
                 help="Percentage of readings during event")

    with col3:
        st.metric("Expected Glitches", f"{rad_effect['glitch_count']}",
                 help="Typical number for this intensity")

    with col4:
        total_samples = len(event_indices)
        st.metric("Event Samples", f"{total_samples}",
                 help="Total samples during radiation event")

    st.error(f"""
    **☢️ Radiation Event Impact:**
    - **{num_corruptions}** sensor readings corrupted ({rad_effect['corruption_rate']*100:.1f}% of event period)
    - Glitches include: spikes, zeros, and random invalid values
    - Data cleaning layer must detect and discard these readings
    - Some bit flips may go undetected if within valid range
    - **Mission Response**: Flag data quality, increase validation checks
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: SLIP EVENT
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Wheel Slip Event")

st.markdown("""
On loose or icy terrain, wheels can slip, causing sudden changes in position
and orientation. The rover must detect and recover from these events.
""")

if st.button("🔬 Simulate Slip Event", type="primary", key="slip_exp4"):
    # Simulate 60-second drive with slip at 30 seconds
    time_points = 600
    time_seconds = np.linspace(0, 60, time_points)

    # Normal drive: constant velocity, stable orientation
    commanded_velocity = 0.05  # m/s
    actual_velocity = np.ones(time_points) * commanded_velocity
    actual_velocity += np.random.normal(0, 0.005, time_points)  # Small noise

    # Position (integral of velocity)
    position = np.cumsum(actual_velocity) * (time_seconds[1] - time_seconds[0])

    # IMU orientation (should be stable)
    roll = np.random.normal(0, 0.1, time_points)
    pitch = np.random.normal(2.0, 0.1, time_points)  # Slight pitch from slope

    # SLIP EVENT at 30 seconds
    slip_index = 300
    slip_duration = 50  # Half a second

    # During slip: velocity drops, IMU shows sudden change
    actual_velocity[slip_index:slip_index+slip_duration] *= 0.2  # Wheels spinning, low progress
    roll[slip_index:slip_index+slip_duration] += np.random.uniform(-3, 3, slip_duration)
    pitch[slip_index:slip_index+slip_duration] += np.random.uniform(-2, 2, slip_duration)

    # Recalculate position with slip
    position = np.cumsum(actual_velocity) * (time_seconds[1] - time_seconds[0])

    # Expected position (without slip)
    expected_position = commanded_velocity * time_seconds

    # Visualization
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Velocity (Commanded vs Actual)", "Position Error", "IMU Orientation"),
        vertical_spacing=0.12,
        row_heights=[0.33, 0.33, 0.34]
    )

    # Velocity
    fig.add_trace(go.Scatter(x=time_seconds, y=np.ones(time_points)*commanded_velocity,
                            mode='lines', name='Commanded',
                            line=dict(color='green', width=2, dash='dash')),
                 row=1, col=1)
    fig.add_trace(go.Scatter(x=time_seconds, y=actual_velocity,
                            mode='lines', name='Actual',
                            line=dict(color='blue', width=1)),
                 row=1, col=1)

    # Position error
    position_error = expected_position - position
    fig.add_trace(go.Scatter(x=time_seconds, y=position_error,
                            mode='lines', name='Position Error',
                            line=dict(color='red', width=2),
                            fill='tozeroy'),
                 row=2, col=1)

    # IMU
    fig.add_trace(go.Scatter(x=time_seconds, y=roll,
                            mode='lines', name='Roll',
                            line=dict(color='purple', width=1)),
                 row=3, col=1)
    fig.add_trace(go.Scatter(x=time_seconds, y=pitch,
                            mode='lines', name='Pitch',
                            line=dict(color='orange', width=1)),
                 row=3, col=1)

    # Mark slip event
    for row in [1, 2, 3]:
        fig.add_vrect(x0=time_seconds[slip_index], x1=time_seconds[slip_index+slip_duration],
                     fillcolor="red", opacity=0.2,
                     layer="below", line_width=0,
                     annotation_text="SLIP!" if row == 1 else "",
                     annotation_position="top left",
                     row=row, col=1)

    fig.update_xaxes(title_text="Time (seconds)", row=3, col=1)
    fig.update_yaxes(title_text="Velocity (m/s)", row=1, col=1)
    fig.update_yaxes(title_text="Error (m)", row=2, col=1)
    fig.update_yaxes(title_text="Angle (°)", row=3, col=1)

    fig.update_layout(height=700, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Slip Duration", f"{slip_duration/10:.1f} s",
                 help="How long wheels were slipping")

    with col2:
        final_position_error = position_error[-1]
        st.metric("Position Error", f"{final_position_error:.2f} m",
                 help="Distance lost due to slip",
                 delta=f"-{final_position_error:.2f} m")

    with col3:
        roll_spike = np.max(np.abs(roll[slip_index:slip_index+slip_duration]))
        st.metric("Max Roll Deviation", f"{roll_spike:.1f}°",
                 help="IMU detected orientation change")

    with col4:
        recovery_time = 5.0
        st.metric("Recovery Time", f"{recovery_time:.1f} s",
                 help="Time to stabilize after slip")

    st.warning("""
    **⛷️ Slip Event Detected:**
    - Wheels lost traction, velocity dropped to **20%** of commanded
    - Position error accumulated (rover didn't travel as far as expected)
    - IMU detected sudden orientation changes
    - **Detection**: Compare expected vs actual position/velocity
    - **Recovery**: Stop, reassess terrain, adjust path or reduce speed
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Chapter 4 Complete!**

You've learned:
- ✅ How different terrain types affect power and sensors
- ✅ Dust devil impacts on solar power and noise
- ✅ Solar radiation events causing sensor corruption
- ✅ Wheel slip detection and recovery
- ✅ Environmental hazard signatures in telemetry
- ✅ Mission response strategies for each hazard type

**Next Steps**: Proceed to Chapter 5 to learn about the telemetry transmission
layer, where packets can be lost, corrupted, or delayed.
""")

st.markdown("*Navigate to Chapter 5: Packets and Loss in the sidebar →*")
