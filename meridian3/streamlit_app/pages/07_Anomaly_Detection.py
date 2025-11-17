"""
Chapter 7: Anomaly Detection

TEACHING FOCUS:
    - Anomaly detection algorithms (threshold, statistical, ML)
    - Baseline establishment and adaptive thresholds
    - Alert generation and prioritization
    - False positive vs. false negative tradeoffs

NARRATIVE:
    Clean data is good. But what does it mean? The anomaly detector identifies
    unusual patterns that may indicate hardware issues, environmental hazards,
    or science opportunities. It's the "mission health monitor."

LEARNING OBJECTIVES:
    - Implement threshold-based anomaly detection
    - Use statistical methods (z-score, moving average)
    - Establish and update baselines
    - Tune sensitivity to balance false alarms vs. missed events

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 38.
"""

import streamlit as st

st.set_page_config(page_title="Anomaly Detection", page_icon="⚠️", layout="wide")

st.title("⚠️ Chapter 7: Anomaly Detection")

st.markdown("""
## Finding Needles in Telemetry Haystacks

Anomaly detection is about pattern recognition: what's normal, and what's not?
A good detector alerts on real issues while avoiding false alarms.

---

### What is an Anomaly?

An anomaly is a telemetry pattern that deviates significantly from expected
behavior. Anomalies may indicate:

**Hardware Issues**:
- Battery degradation (capacity loss)
- Sensor drift or failure
- Motor overheating
- CPU errors

**Environmental Hazards**:
- Dust devils (power drop)
- Radiation spikes (sensor glitches)
- Terrain hazards (slippage, tilt)

**Science Opportunities**:
- Interesting rock formations (camera anomalies)
- Temperature anomalies (subsurface ice?)
- Atmospheric events

**Operational Anomalies**:
- Unexpected command execution
- Timing violations
- Communication dropouts

---

### Detection Algorithms

**1. Threshold Detection**:
- Simplest method: value > threshold = anomaly
- Example: CPU temp > 80°C → Alert
- Pros: Fast, easy to understand
- Cons: Requires manual threshold tuning, no context

**2. Derivative Detection**:
- Detect rapid changes: |dValue/dt| > threshold
- Example: Temperature drops 10°C in 1 second → Anomaly
- Pros: Catches sudden events
- Cons: Sensitive to noise

**3. Statistical (Z-Score)**:
- Compare to running mean and std dev
- Z = (value - mean) / stddev
- Example: Z > 3.0 → Anomaly (99.7% confidence)
- Pros: Adaptive to typical behavior
- Cons: Requires stable baseline period

**4. Moving Window Average**:
- Compare current value to recent history
- Example: Current power < 80% of 10-minute average → Alert
- Pros: Adapts to slow trends
- Cons: Lag in detection

**5. Multi-Field Correlation**:
- Look for unusual combinations
- Example: High power draw + low velocity = anomaly
- Pros: Catches subtle issues
- Cons: Complex, requires domain knowledge

**6. Machine Learning**:
- Train model on normal behavior, flag deviations
- Example: Autoencoder, isolation forest
- Pros: Can learn complex patterns
- Cons: Requires training data, harder to interpret

---

### The Sensitivity Tradeoff

Increasing sensitivity:
- ✅ Catch more real anomalies (lower false negatives)
- ❌ More false alarms (higher false positives)

Decreasing sensitivity:
- ✅ Fewer false alarms
- ❌ Miss real issues

The right balance depends on mission criticality and human workload.

---

### Alert Prioritization

Not all anomalies are equal. Priority levels:

**Critical (P0)**:
- Immediate threat to mission (battery failure, hardware fault)
- Wake up flight team
- Example: Battery voltage < 20V

**High (P1)**:
- Significant issue, needs attention within hours
- Schedule investigation
- Example: CPU temp trending high

**Medium (P2)**:
- Notable but not urgent
- Review during next shift
- Example: Unusual power profile

**Low (P3)**:
- Informational, science opportunity
- Log for later analysis
- Example: Interesting thermal signature

---

## Interactive Features

*Full interactive anomaly detection will be implemented in Phase 4*

This chapter will include:
- Real-time anomaly detector
- Algorithm comparison tool
- Threshold tuning slider
- False positive/negative simulator
- Alert prioritization dashboard

---

*Proceed to Chapter 8: Mission Console →*
""")
