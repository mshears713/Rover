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

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 35.
"""

import streamlit as st

st.set_page_config(page_title="Terrain and Hazards", page_icon="🏔️", layout="wide")

st.title("🏔️ Chapter 4: Terrain and Hazards")

st.markdown("""
## Surviving the Martian Environment

Mars is not a benign environment. The rover must contend with challenging
terrain, dust storms, radiation, and thermal extremes.

---

### Terrain Properties

**Slope Angle**:
- Affects power consumption (steeper = more power)
- Affects stability (>20° is risky)
- Detected by IMU tilt measurements

**Surface Type**:
- Firm: Nominal traction, standard power
- Loose regolith: Slippage, 30% more power
- Dusty: Coating of solar panels, degraded efficiency
- Rocky: High vibration, increased wear
- Icy: Low friction, reduced power but slip risk

**Roughness**:
- Affects vibration and sensor noise
- Increases mechanical wear
- May obscure small features

---

### Hazardous Events

**Dust Devils** (Local dust storms):
- Frequency: ~1 per sol in dusty season
- Effects: Reduced solar power, sensor noise, coating
- Duration: 1-5 minutes
- Severity: Variable (light to heavy)

**Radiation Spikes** (Solar particle events):
- Frequency: ~1 per 3 sols
- Effects: Sensor glitches, bit flips, CPU errors
- Duration: 10-60 seconds
- Severity: Moderate to severe

**Slip Events**:
- Frequency: Depends on terrain and motion
- Effects: Sudden position/orientation change
- Duration: Instantaneous
- Severity: Minor to major

**Thermal Shocks**:
- Rapid temperature changes
- Stress on mechanical joints
- Can cause temporary sensor anomalies

---

### Event Detection

Hazards leave telemetry signatures:
- Dust devil: Power drop + sensor noise increase
- Radiation spike: Multiple sensor anomalies simultaneously
- Slip: Sudden IMU change + position mismatch
- Thermal shock: Rapid temperature derivative

---

## Interactive Features

*Full interactive environment simulator will be implemented in Phase 4*

This chapter will include:
- Terrain type selector
- Hazard event generator
- Real-time telemetry response viewer
- Mission timeline with hazard markers

---

*Proceed to Chapter 5: Packets and Loss →*
""")
