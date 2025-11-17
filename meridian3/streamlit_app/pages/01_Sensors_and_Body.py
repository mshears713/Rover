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

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 32.
"""

import streamlit as st

st.set_page_config(page_title="Sensors and Body", page_icon="📡", layout="wide")

st.title("📡 Chapter 1: Sensors and Body")

st.markdown("""
## Understanding the Rover as a Sensor Platform

A rover doesn't "know" where it is or what's happening to it. It only knows
what its sensors tell it. This chapter explores the sensor suite that gives
Meridian-3 awareness of its state.

---

### The Sensor Suite

**Inertial Measurement Unit (IMU)**
- Measures: Roll, pitch, heading (orientation)
- Accuracy: ±0.1° (noise), 0.01°/hour drift
- Update rate: 10 Hz

**Power Monitor**
- Measures: Battery voltage, current, state of charge, solar input
- Accuracy: ±0.05V (voltage), ±10mA (current)
- Update rate: 1 Hz

**Thermal Array**
- Measures: CPU, battery, motor, chassis temperatures
- Accuracy: ±0.5°C
- Resolution: 0.1°C
- Update rate: 1 Hz

**Position System (GPS/Odometry)**
- Measures: X, Y, Z position, velocity
- Accuracy: ±1m (position), ±0.01 m/s (velocity)
- Update rate: 1 Hz

---

### State vs. Measurement

**True State** (unknowable in real systems):
- The actual physical configuration of the rover
- Perfect, noiseless values
- Used in simulation only

**Measured State** (what we actually get):
- Sensor readings with noise, bias, drift
- May be corrupted or missing
- What the telemetry pipeline receives

---

## Interactive Demonstration (Phase 2)

**Try It: Sensor Noise Visualization**

Run a short simulation to see how sensor noise affects measurements.
""")

# Phase 2: Add simple simulator demonstration
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'meridian3', 'src'))

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite
    import pandas as pd

    # Simulation controls
    col1, col2 = st.columns(2)
    with col1:
        num_samples = st.slider("Number of samples", 10, 100, 50)
    with col2:
        if st.button("Run Sensor Test", type="primary"):
            # Create rover and sensors
            rover = RoverState()
            sensors = SensorSuite()

            # Collect samples
            data = []
            for i in range(num_samples):
                frame = sensors.read_all(rover, mission_time=float(i))
                data.append({
                    'Sample': i,
                    'True Roll': rover.roll,
                    'Measured Roll': frame['roll'],
                    'True Battery SoC': rover.battery_soc,
                    'Measured Battery SoC': frame['battery_soc'],
                    'True CPU Temp': rover.cpu_temp,
                    'Measured CPU Temp': frame['cpu_temp']
                })

            df = pd.DataFrame(data)

            # Display statistics
            st.subheader("Sensor Accuracy Analysis")

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                roll_error = (df['Measured Roll'] - df['True Roll']).abs().mean()
                st.metric("Roll Error (avg)", f"{roll_error:.3f}°")

            with col_b:
                soc_error = (df['Measured Battery SoC'] - df['True Battery SoC']).abs().mean()
                st.metric("Battery SoC Error (avg)", f"{soc_error:.2f}%")

            with col_c:
                temp_error = (df['Measured CPU Temp'] - df['True CPU Temp']).abs().mean()
                st.metric("CPU Temp Error (avg)", f"{temp_error:.2f}°C")

            # Show sample data
            st.subheader("Sample Sensor Readings")
            st.dataframe(df.head(10), use_container_width=True)

            st.info("""
            📊 **Observations:**
            - Notice how measured values differ slightly from true values
            - Errors are random (Gaussian noise)
            - Multiple readings allow statistical estimation
            - Real rovers use filtering to reduce noise impact
            """)

except ImportError as e:
    st.warning(f"""
    ⚠️ Simulator not yet fully configured.
    This interactive demo will be available once Phase 2 is complete.

    Error: {str(e)}
    """)

st.markdown("""
---

*Proceed to Chapter 2: Time and Orbits →*
""")
