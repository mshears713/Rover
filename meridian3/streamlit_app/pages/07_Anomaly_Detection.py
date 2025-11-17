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

ARCHITECTURE:
    Clean Frames → Anomaly Detector → Labeled Frames + Alerts
    - Threshold detection: Simple limits
    - Statistical detection: Z-score, derivatives
    - Alert classification: P0-P3 priorities

TEACHING APPROACH:
    - Interactive detection method selector
    - Labeled anomaly visualization
    - Parameter tuning for sensitivity
    - False positive/negative analysis

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 38.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(page_title="Anomaly Detection", page_icon="🎯", layout="wide")
st.title("🎯 Chapter 7: Anomaly Detection")

st.markdown("""
## Finding Needles in Telemetry Haystacks

Anomaly detection is about pattern recognition: what's normal, and what's not?
A good detector alerts on real issues while avoiding false alarms.
""")

with st.expander("🔍 Anomaly Detection Methods", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │           ANOMALY DETECTION TAXONOMY                         │
    └──────────────────────────────────────────────────────────────┘

    1. THRESHOLD DETECTION
       Value > Upper_Limit → ANOMALY
       Value < Lower_Limit → ANOMALY
       ✓ Simple, fast  ✗ Requires manual tuning

    2. DERIVATIVE DETECTION
       |dValue/dt| > Rate_Limit → ANOMALY
       ✓ Catches sudden changes  ✗ Sensitive to noise

    3. Z-SCORE (Statistical)
       |Value - Mean| / StdDev > 3.0 → ANOMALY
       ✓ Adaptive  ✗ Needs baseline period

    4. MOVING AVERAGE
       Value < (80% of recent average) → ANOMALY
       ✓ Trend-aware  ✗ Lag in detection
    ```
    """)

st.markdown("---")
st.markdown("## 🔬 Experiment 1: Threshold Detection")

st.markdown("""
The simplest method: flag values that exceed predefined limits.
""")

col1, col2, col3 = st.columns(3)
with col1:
    upper_threshold = st.slider("Upper threshold (°C)", 40, 80, 60, step=5)
with col2:
    lower_threshold = st.slider("Lower threshold (°C)", 0, 40, 20, step=5)
with col3:
    num_anomalies = st.slider("Inject anomalies", 0, 20, 5, step=1)

if st.button("🔬 Run Threshold Detection", type="primary", key="threshold_exp1"):
    # Generate data with anomalies
    time = np.arange(200)
    normal_temp = 40 + 5 * np.sin(2 * np.pi * time / 100) + np.random.normal(0, 2, len(time))

    # Inject anomalies
    anomaly_indices = np.random.choice(len(time), num_anomalies, replace=False)
    temp = normal_temp.copy()
    for idx in anomaly_indices:
        if np.random.random() < 0.5:
            temp[idx] = np.random.uniform(upper_threshold + 5, 90)
        else:
            temp[idx] = np.random.uniform(0, lower_threshold - 5)

    # Detect anomalies
    detected = (temp > upper_threshold) | (temp < lower_threshold)
    true_anomalies = np.zeros(len(time), dtype=bool)
    true_anomalies[anomaly_indices] = True

    # Classification
    true_positives = np.sum(detected & true_anomalies)
    false_positives = np.sum(detected & ~true_anomalies)
    false_negatives = np.sum(~detected & true_anomalies)
    true_negatives = np.sum(~detected & ~true_anomalies)

    # Visualization
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time[~detected], y=temp[~detected],
                            mode='markers', name='Normal',
                            marker=dict(color='green', size=4)))
    fig.add_trace(go.Scatter(x=time[detected], y=temp[detected],
                            mode='markers', name='Anomaly Detected',
                            marker=dict(color='red', size=8, symbol='x')))
    fig.add_hline(y=upper_threshold, line_dash="dash", line_color="red",
                 annotation_text=f"Upper: {upper_threshold}°C")
    fig.add_hline(y=lower_threshold, line_dash="dash", line_color="blue",
                 annotation_text=f"Lower: {lower_threshold}°C")
    fig.update_layout(title="Threshold-Based Anomaly Detection",
                     xaxis_title="Time", yaxis_title="CPU Temp (°C)", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("True Positives", f"{true_positives}", help="Correctly detected anomalies")
    with col2:
        st.metric("False Positives", f"{false_positives}", help="False alarms")
    with col3:
        st.metric("Precision", f"{precision:.2f}", help="TP / (TP + FP)")
    with col4:
        st.metric("Recall", f"{recall:.2f}", help="TP / (TP + FN)")

    st.info(f"""
    **📚 Threshold Detection Results:**
    - Detected **{np.sum(detected)}** anomalies ({true_positives} true, {false_positives} false)
    - Precision: **{precision:.2f}** (low = many false alarms)
    - Recall: **{recall:.2f}** (low = missing real anomalies)
    - Threshold tuning is critical for performance
    """)

st.markdown("---")
st.markdown("## 🔬 Experiment 2: Z-Score Detection")

st.markdown("""
Statistical method: flag values that deviate significantly from the mean.
Z = (value - mean) / std_dev. Typical threshold: |Z| > 3.0
""")

col1, col2 = st.columns(2)
with col1:
    z_threshold = st.slider("Z-score threshold", 1.5, 5.0, 3.0, step=0.5)
with col2:
    window_size = st.slider("Baseline window", 20, 100, 50, step=10)

if st.button("🔬 Run Z-Score Detection", type="primary", key="zscore_exp2"):
    # Generate data with anomalies
    time = np.arange(300)
    baseline = 45 + 3 * np.sin(2 * np.pi * time / 150)
    normal_data = baseline + np.random.normal(0, 1.5, len(time))

    # Inject sharp anomalies
    anomaly_times = [80, 150, 220]
    data = normal_data.copy()
    for t in anomaly_times:
        data[t:t+5] += np.random.uniform(8, 15)

    # Calculate rolling Z-score
    rolling_mean = pd.Series(data).rolling(window_size, min_periods=1).mean()
    rolling_std = pd.Series(data).rolling(window_size, min_periods=1).std()
    z_score = np.abs((data - rolling_mean) / rolling_std)

    # Detect anomalies
    anomalies = z_score > z_threshold

    # Visualization
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Data with Anomalies", "Z-Score"),
                       vertical_spacing=0.15, row_heights=[0.6, 0.4])

    fig.add_trace(go.Scatter(x=time, y=data, mode='lines', name='Data',
                            line=dict(color='blue', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=time[anomalies], y=data[anomalies],
                            mode='markers', name='Anomaly',
                            marker=dict(color='red', size=10, symbol='x')), row=1, col=1)

    fig.add_trace(go.Scatter(x=time, y=z_score, mode='lines', name='Z-score',
                            line=dict(color='purple', width=2)), row=2, col=1)
    fig.add_hline(y=z_threshold, line_dash="dash", line_color="red",
                 annotation_text=f"Threshold: {z_threshold}", row=2, col=1)

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Anomalies Detected", f"{np.sum(anomalies)}")
    with col2:
        st.metric("Max Z-Score", f"{np.max(z_score):.2f}")
    with col3:
        st.metric("Baseline Window", f"{window_size} samples")

    st.success("""
    **✅ Z-Score Detection:**
    - Adapts to signal trends (uses rolling statistics)
    - Less sensitive to slow drifts
    - Z > 3.0 means value is >99.7% from mean (very unusual)
    - Requires sufficient baseline data for accurate statistics
    """)

st.markdown("---")
st.markdown("## 🔬 Experiment 3: Alert Prioritization")

st.markdown("""
Not all anomalies are equally important. Classify them by severity and impact.
""")

if st.button("🚨 Generate Mission Alerts", type="primary", key="alert_exp3"):
    # Simulate various anomaly types
    alerts = []

    # Critical (P0): Battery failure
    if np.random.random() < 0.3:
        alerts.append({
            "Time": "14:23:45",
            "Type": "Battery Voltage Low",
            "Value": "18.5V",
            "Priority": "P0 - CRITICAL",
            "Action": "Switch to safe mode immediately",
            "Color": "darkred"
        })

    # High (P1): Temperature trending high
    if np.random.random() < 0.5:
        alerts.append({
            "Time": "14:25:12",
            "Type": "CPU Temp Rising",
            "Value": "78°C",
            "Priority": "P1 - HIGH",
            "Action": "Reduce computational load",
            "Color": "red"
        })

    # Medium (P2): Unusual power draw
    if np.random.random() < 0.7:
        alerts.append({
            "Time": "14:27:03",
            "Type": "Power Anomaly",
            "Value": "35W (expect 20W)",
            "Priority": "P2 - MEDIUM",
            "Action": "Investigate cause",
            "Color": "orange"
        })

    # Low (P3): Interesting science data
    if np.random.random() < 0.9:
        alerts.append({
            "Time": "14:28:30",
            "Type": "Thermal Signature",
            "Value": "Unusual pattern detected",
            "Priority": "P3 - LOW",
            "Action": "Log for science team review",
            "Color": "yellow"
        })

    if alerts:
        st.markdown("### 🚨 Active Mission Alerts")
        for alert in alerts:
            color_map = {"darkred": "🔴", "red": "🟠", "orange": "🟡", "yellow": "🟢"}
            icon = color_map.get(alert["Color"], "⚪")
            with st.expander(f"{icon} {alert['Priority']}: {alert['Type']} at {alert['Time']}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Value**: {alert['Value']}")
                    st.markdown(f"**Priority**: {alert['Priority']}")
                with col2:
                    st.markdown(f"**Recommended Action**:")
                    st.markdown(f"*{alert['Action']}*")

        st.info("""
        **📋 Alert Priority Levels:**
        - **P0 (Critical)**: Immediate threat to mission - wake up flight team
        - **P1 (High)**: Significant issue - attention within hours
        - **P2 (Medium)**: Notable but not urgent - review next shift
        - **P3 (Low)**: Informational or science opportunity - log for later
        """)
    else:
        st.success("✅ No active alerts - all systems nominal")

st.markdown("---")
st.success("""
**🎓 Chapter 7 Complete!**

You've learned:
- ✅ Threshold-based detection (simple but effective)
- ✅ Z-score statistical detection (adaptive)
- ✅ Derivative detection for rapid changes
- ✅ Alert prioritization (P0-P3)
- ✅ Precision vs. recall tradeoffs
- ✅ Balancing sensitivity and false alarms

**Next Steps**: Proceed to Chapter 8 for the Mission Console where
all these systems come together in real-time operations.
""")

st.markdown("*Navigate to Chapter 8: Mission Console in the sidebar →*")
