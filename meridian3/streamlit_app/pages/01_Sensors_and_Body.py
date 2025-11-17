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

## Interactive Features

*Full interactive sensor visualization will be implemented in Phase 4*

This chapter will include:
- Real-time sensor readouts
- Noise visualization
- Sensor calibration exercises
- State vs. measurement comparison

---

*Proceed to Chapter 2: Time and Orbits →*
""")
