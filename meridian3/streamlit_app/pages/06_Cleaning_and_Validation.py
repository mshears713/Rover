"""
Chapter 6: Cleaning and Validation

TEACHING FOCUS:
    - Data validation strategies
    - Gap filling and interpolation
    - Range checking and sanity tests
    - Repair vs. discard decisions

NARRATIVE:
    Corrupted and missing data is inevitable. The cleaning layer transforms
    messy, incomplete packets into usable telemetry frames through validation,
    interpolation, and repair. This is defensive data engineering.

LEARNING OBJECTIVES:
    - Implement range and sanity checks
    - Choose appropriate interpolation methods
    - Handle missing data gracefully
    - Balance repair vs. rejection

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 37.
"""

import streamlit as st

st.set_page_config(page_title="Cleaning and Validation", page_icon="🧹", layout="wide")

st.title("🧹 Chapter 6: Cleaning and Validation")

st.markdown("""
## From Messy Packets to Clean Frames

The data we receive is imperfect. The cleaning layer's job is to validate,
repair, and reconstruct usable telemetry from corrupted transmissions.

---

### Validation Strategies

**Range Checking**:
- Is the value physically possible?
- Example: Battery SoC must be 0-100%
- Example: CPU temp must be -40°C to +85°C

**Sanity Checks**:
- Is the value reasonable given context?
- Example: Temperature shouldn't jump 50°C in 1 second
- Example: Position shouldn't move 100m in 1 second (max speed ~0.05 m/s)

**Cross-Field Validation**:
- Are related fields consistent?
- Example: If battery current is negative, SoC should increase
- Example: If solar angle is 0°, solar current should be ~0

**Temporal Consistency**:
- Does value make sense compared to history?
- Example: Velocity shouldn't reverse instantly
- Example: Drift should be gradual, not sudden

**Checksum Verification**:
- Does packet checksum match contents?
- If not, entire packet may be suspect

---

### Repair Techniques

**Linear Interpolation**:
- Fill gaps using before/after values
- Works well for slowly-changing fields
- Example: Temperature, battery SoC

**Extrapolation**:
- Extend trend to fill recent gap
- Risky if trend changes
- Use with caution

**Last Valid Value**:
- Repeat previous good reading
- Conservative approach
- Mark as "stale" after timeout

**Model-Based Reconstruction**:
- Use physics model to predict value
- Example: Power consumption based on activity
- Example: Thermal state based on environment

**Discard and Mark Missing**:
- When repair is too uncertain, don't guess
- Mark field as missing/invalid
- Better to admit ignorance than introduce errors

---

### Cleaning Pipeline

```
Corrupted Packet
    ↓
[1. Checksum Verify] → Failed? → Discard entire packet
    ↓ Passed
[2. Range Check] → Out of range? → Mark field invalid
    ↓ In range
[3. Sanity Check] → Inconsistent? → Try repair or mark invalid
    ↓ Sane
[4. Gap Fill] → Missing predecessor? → Interpolate if possible
    ↓ Complete
Clean Frame (with quality metadata)
```

---

### Quality Metadata

Each cleaned frame includes quality indicators:
- Which fields were repaired
- Interpolation vs. measured
- Age of last valid reading
- Confidence score (0.0 to 1.0)

Downstream systems use this to make informed decisions.

---

## Interactive Features

*Full interactive cleaning demonstration will be implemented in Phase 4*

This chapter will include:
- Corruption injector
- Cleaning strategy selector
- Before/after comparison viewer
- Quality score calculator

---

*Proceed to Chapter 7: Anomaly Detection →*
""")
