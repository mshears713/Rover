"""
Chapter 2: Time and Orbits

TEACHING FOCUS:
    - Martian sol length and time systems
    - Solar angle calculation
    - Day/night cycles and their effects
    - Orbital mechanics basics

NARRATIVE:
    Time on Mars is different from Earth. A sol is 24 hours and 39 minutes.
    The rover must track both mission elapsed time and local solar time to
    manage power and thermal systems effectively.

LEARNING OBJECTIVES:
    - Convert between mission time and sol/local time
    - Calculate solar elevation angle
    - Predict day/night transitions
    - Understand how orbital position affects rover operations

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 33.
"""

import streamlit as st

st.set_page_config(page_title="Time and Orbits", page_icon="🌅", layout="wide")

st.title("🌅 Chapter 2: Time and Orbits")

st.markdown("""
## Understanding Martian Time

The rover operates on Mars time, not Earth time. Understanding the local
solar environment is critical for power management and mission planning.

---

### Mars vs. Earth

**Sol Length**: 24 hours, 39 minutes, 35 seconds (88,775 seconds)

**Why it matters**:
- Solar panels only work during daylight
- Batteries must last through the night
- CPU temperature drops dramatically after sunset
- Communication windows depend on orbital positions

---

### Time Systems

**Mission Elapsed Time (MET)**:
- Seconds since landing
- Continuous, monotonic counter
- Used for logging and correlation

**Sol Number**:
- Martian days since landing
- Sol 0 = landing day
- Discrete counter

**Local Solar Time (LST)**:
- Time of day on Mars (0-88775 seconds)
- 0 = local midnight
- ~44000s = local noon (peak solar)

---

### Solar Angle and Power

Solar elevation angle determines available power:
- 0° (sunrise/sunset): Minimal power
- 45°: ~70% of maximum power
- 90° (overhead): Maximum power (~100W)

Dust and atmospheric conditions reduce efficiency further.

---

## Interactive Features

*Full interactive orbital visualization will be implemented in Phase 4*

This chapter will include:
- Sol clock and time converter
- Solar angle calculator
- Day/night cycle simulator
- Power availability predictor

---

*Proceed to Chapter 3: Noise and Wear →*
""")
