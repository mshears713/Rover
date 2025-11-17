"""
Chapter 3: Noise and Wear

TEACHING FOCUS:
    - Sensor noise models (Gaussian, quantization)
    - Bias and drift over time
    - Sensor degradation and aging
    - Calibration and correction

NARRATIVE:
    Sensors are not perfect. They have noise, bias, drift, and they degrade
    over time. Understanding these imperfections is essential for interpreting
    telemetry and detecting real anomalies vs. sensor artifacts.

LEARNING OBJECTIVES:
    - Distinguish between noise types (random vs. systematic)
    - Model sensor drift accumulation
    - Recognize when recalibration is needed
    - Understand the impact of aging on sensor performance

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 34.
"""

import streamlit as st

st.set_page_config(page_title="Noise and Wear", page_icon="📊", layout="wide")

st.title("📊 Chapter 3: Noise and Wear")

st.markdown("""
## Imperfect Measurements in a Perfect Simulation

Real sensors lie. Not maliciously - they simply cannot be perfect.
Understanding sensor imperfections is the key to robust telemetry systems.

---

### Types of Sensor Errors

**Random Noise**:
- Gaussian fluctuations around true value
- Zero mean, constant standard deviation
- Example: ±0.5°C on thermistors
- Reduced by averaging multiple samples

**Systematic Bias**:
- Constant offset from true value
- Example: IMU reads +0.3° higher than actual
- Corrected by calibration

**Drift**:
- Bias that changes slowly over time
- Example: Gyro drifts 0.01°/hour
- Requires periodic recalibration

**Quantization**:
- Limited precision from ADC resolution
- Example: 12-bit ADC = 4096 discrete levels
- Causes "stair-step" artifacts in data

**Degradation**:
- Performance loss over mission lifetime
- Caused by radiation, thermal cycling, wear
- May require adjustment of operating parameters

---

### Sensor Specifications

Each sensor has a datasheet specification:

**IMU Gyroscope**:
- Noise: ±0.1°/s (1-sigma)
- Bias stability: 0.01°/hour
- Quantization: 16-bit (0.01° resolution)

**Thermistor**:
- Accuracy: ±0.5°C
- Resolution: 0.1°C
- Drift: <0.1°C/year

**Current Sensor**:
- Accuracy: ±1% of reading
- Resolution: 10mA
- Temperature coefficient: 50ppm/°C

---

## Interactive Features

*Full interactive noise visualization will be implemented in Phase 4*

This chapter will include:
- Live noise distribution plots
- Drift accumulation simulator
- Calibration correction tool
- Signal-to-noise ratio calculator

---

*Proceed to Chapter 4: Terrain and Hazards →*
""")
