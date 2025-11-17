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

ARCHITECTURE:
    Raw Packets → Validator → Interpolator → Clean Frames
    - Validator: Range checks, sanity tests
    - Interpolator: Fill gaps using various strategies
    - Quality metadata: Track confidence

TEACHING APPROACH:
    - Interactive cleaning strategy toggles
    - Before/after visualization
    - Quality metrics display
    - Parameter tuning

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 37.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(page_title="Cleaning and Validation", page_icon="🧹", layout="wide")
st.title("🧹 Chapter 6: Cleaning and Validation")

st.markdown("""
## From Messy Packets to Clean Frames

The data we receive is imperfect. The cleaning layer's job is to validate,
repair, and reconstruct usable telemetry from corrupted transmissions.
""")

with st.expander("🔧 Data Cleaning Pipeline", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │              DATA CLEANING WORKFLOW                          │
    └──────────────────────────────────────────────────────────────┘

    Corrupted Packet
         │
         ▼
    [1. Range Check] → Out of bounds? → REJECT
         │ Pass
         ▼
    [2. Sanity Check] → Physically impossible? → REJECT
         │ Pass
         ▼
    [3. Gap Detection] → Missing predecessor? → INTERPOLATE
         │ Complete
         ▼
    [4. Quality Scoring] → Assign confidence (0.0-1.0)
         │
         ▼
    Clean Frame + Metadata
    ```
    """)

st.markdown("---")
st.markdown("## 🔬 Experiment 1: Range Validation")

col1, col2 = st.columns(2)
with col1:
    num_samples = st.slider("Test samples", 50, 200, 100, step=10)
with col2:
    corruption_rate = st.slider("Corruption rate (%)", 0, 50, 15, step=5)

if st.button("🧪 Generate Corrupted Data", type="primary", key="range_exp1"):
    # Generate mostly valid data
    battery_voltage = np.random.normal(28.0, 0.5, num_samples)
    cpu_temp = np.random.normal(45.0, 3.0, num_samples)
    battery_soc = np.random.normal(75.0, 5.0, num_samples)

    # Inject corruptions
    num_corrupt = int(num_samples * corruption_rate / 100)
    corrupt_indices = np.random.choice(num_samples, num_corrupt, replace=False)

    battery_voltage[corrupt_indices] = np.random.uniform(-10, 60, num_corrupt)
    cpu_temp[corrupt_indices] = np.random.uniform(-100, 150, num_corrupt)
    battery_soc[corrupt_indices] = np.random.uniform(-50, 150, num_corrupt)

    # Apply range checks
    valid_voltage = (battery_voltage >= 20) & (battery_voltage <= 32)
    valid_temp = (cpu_temp >= -40) & (cpu_temp <= 85)
    valid_soc = (battery_soc >= 0) & (battery_soc <= 100)

    all_valid = valid_voltage & valid_temp & valid_soc

    # Stats
    num_rejected = num_samples - np.sum(all_valid)
    detection_rate = (num_rejected / num_corrupt * 100) if num_corrupt > 0 else 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Samples", f"{num_samples}")
    with col2:
        st.metric("Corrupted", f"{num_corrupt}")
    with col3:
        st.metric("Rejected", f"{num_rejected}")
    with col4:
        st.metric("Detection Rate", f"{detection_rate:.0f}%")

    # Visualization
    fig = make_subplots(rows=1, cols=3, subplot_titles=("Battery Voltage", "CPU Temp", "Battery SoC"))

    fig.add_trace(go.Scatter(x=np.arange(num_samples)[all_valid], y=battery_voltage[all_valid],
                            mode='markers', name='Valid', marker=dict(color='green', size=4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=np.arange(num_samples)[~all_valid], y=battery_voltage[~all_valid],
                            mode='markers', name='Rejected', marker=dict(color='red', size=6, symbol='x')), row=1, col=1)

    fig.add_trace(go.Scatter(x=np.arange(num_samples)[all_valid], y=cpu_temp[all_valid],
                            mode='markers', marker=dict(color='green', size=4), showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(x=np.arange(num_samples)[~all_valid], y=cpu_temp[~all_valid],
                            mode='markers', marker=dict(color='red', size=6, symbol='x'), showlegend=False), row=1, col=2)

    fig.add_trace(go.Scatter(x=np.arange(num_samples)[all_valid], y=battery_soc[all_valid],
                            mode='markers', marker=dict(color='green', size=4), showlegend=False), row=1, col=3)
    fig.add_trace(go.Scatter(x=np.arange(num_samples)[~all_valid], y=battery_soc[~all_valid],
                            mode='markers', marker=dict(color='red', size=6, symbol='x'), showlegend=False), row=1, col=3)

    fig.update_xaxes(title_text="Sample", row=1, col=1)
    fig.update_yaxes(title_text="Voltage (V)", row=1, col=1)
    fig.update_yaxes(title_text="Temp (°C)", row=1, col=2)
    fig.update_yaxes(title_text="SoC (%)", row=1, col=3)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"""
    **📚 Range Validation Results:**
    - Detected **{num_rejected}** out-of-range values ({detection_rate:.0f}% detection)
    - Valid ranges: Voltage [20-32V], Temp [-40-85°C], SoC [0-100%]
    - Simple but effective: catches most hardware glitches
    - False positives rare if ranges are properly defined
    """)

st.markdown("---")
st.markdown("## 🔬 Experiment 2: Gap Interpolation")

st.markdown("""
When packets are lost, we have gaps in the telemetry timeline. Interpolation
estimates missing values based on surrounding data.
""")

col1, col2, col3 = st.columns(3)
with col1:
    gap_length = st.slider("Gap length", 1, 20, 5, step=1, help="Consecutive missing samples")
with col2:
    interp_method = st.selectbox("Interpolation method", ["Linear", "Forward Fill", "Mean Fill"])
with col3:
    signal_type = st.selectbox("Signal type", ["Slowly varying", "Rapidly changing"])

if st.button("🔬 Demonstrate Interpolation", type="primary", key="interp_exp2"):
    # Generate clean signal
    time = np.arange(100)
    if signal_type == "Slowly varying":
        clean_signal = 25 + 3 * np.sin(2 * np.pi * time / 50)
    else:
        clean_signal = 25 + 3 * np.sin(2 * np.pi * time / 10) + 2 * np.cos(2 * np.pi * time / 7)

    # Create gap
    gap_start = 40
    gap_end = gap_start + gap_length
    corrupted_signal = clean_signal.copy()
    corrupted_signal[gap_start:gap_end] = np.nan

    # Interpolate
    if interp_method == "Linear":
        interpolated = pd.Series(corrupted_signal).interpolate(method='linear').values
    elif interp_method == "Forward Fill":
        interpolated = pd.Series(corrupted_signal).fillna(method='ffill').values
    else:  # Mean Fill
        mean_val = np.nanmean(corrupted_signal)
        interpolated = np.where(np.isnan(corrupted_signal), mean_val, corrupted_signal)

    # Calculate error
    gap_error = np.abs(interpolated[gap_start:gap_end] - clean_signal[gap_start:gap_end])
    rms_error = np.sqrt(np.mean(gap_error**2))

    # Visualization
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=clean_signal, mode='lines', name='True Signal',
                            line=dict(color='green', width=2)))
    fig.add_trace(go.Scatter(x=time, y=interpolated, mode='lines', name='Interpolated',
                            line=dict(color='blue', width=2, dash='dash')))
    fig.add_vrect(x0=gap_start, x1=gap_end-1, fillcolor="red", opacity=0.1,
                 annotation_text="Missing Data", annotation_position="top left")

    fig.update_layout(title=f"{interp_method} Interpolation ({signal_type} signal)",
                     xaxis_title="Time", yaxis_title="Value", height=350)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gap Length", f"{gap_length} samples")
    with col2:
        st.metric("RMS Error", f"{rms_error:.3f}")
    with col3:
        st.metric("Max Error", f"{np.max(gap_error):.3f}")

    st.info(f"""
    **📚 Interpolation Analysis:**
    - **Linear**: Best for slowly varying signals, smooth transitions
    - **Forward Fill**: Conservative, holds last value (may create steps)
    - **Mean Fill**: Simple but ignores local trends
    - Error increases with gap length and signal complexity
    - RMS error: **{rms_error:.3f}** - {"Good" if rms_error < 0.5 else "Poor"} reconstruction
    """)

st.markdown("---")
st.markdown("## 🔬 Experiment 3: Complete Cleaning Pipeline")

st.markdown("""
Apply all cleaning strategies together to transform corrupted data into
clean, validated telemetry.
""")

col1, col2 = st.columns(2)
with col1:
    enable_range_check = st.checkbox("Enable range checking", value=True)
    enable_interpolation = st.checkbox("Enable gap interpolation", value=True)
with col2:
    enable_smoothing = st.checkbox("Enable noise smoothing", value=False)
    show_quality = st.checkbox("Show quality scores", value=True)

if st.button("🧹 Run Complete Cleaning", type="primary", key="clean_exp3"):
    # Generate realistic corrupted data
    time = np.arange(150)
    true_signal = 28 + 2 * np.sin(2 * np.pi * time / 60)
    raw_signal = true_signal + np.random.normal(0, 0.3, len(time))

    # Add corruptions (out of range)
    corrupt_mask = np.random.random(len(time)) < 0.1
    raw_signal[corrupt_mask] = np.random.uniform(-10, 60, np.sum(corrupt_mask))

    # Add missing data (packet loss)
    missing_mask = np.random.random(len(time)) < 0.08
    raw_signal[missing_mask] = np.nan

    # Start cleaning
    cleaned_signal = raw_signal.copy()
    quality = np.ones(len(time))

    # Step 1: Range check
    if enable_range_check:
        valid_range = (cleaned_signal >= 20) & (cleaned_signal <= 35)
        cleaned_signal[~valid_range] = np.nan
        quality[~valid_range] = 0.0

    # Step 2: Interpolate gaps
    if enable_interpolation:
        was_nan = np.isnan(cleaned_signal)
        cleaned_signal = pd.Series(cleaned_signal).interpolate(method='linear').values
        quality[was_nan] = 0.7  # Lower quality for interpolated

    # Step 3: Smoothing
    if enable_smoothing:
        window = 5
        cleaned_signal = pd.Series(cleaned_signal).rolling(window, center=True).mean().values

    # Visualization
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Before vs After Cleaning", "Data Quality Score"),
                       vertical_spacing=0.15, row_heights=[0.65, 0.35])

    fig.add_trace(go.Scatter(x=time, y=raw_signal, mode='markers', name='Raw (corrupted)',
                            marker=dict(color='red', size=3, opacity=0.6)), row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=cleaned_signal, mode='lines', name='Cleaned',
                            line=dict(color='blue', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=true_signal, mode='lines', name='True',
                            line=dict(color='green', width=1, dash='dash')), row=1, col=1)

    if show_quality:
        fig.add_trace(go.Scatter(x=time, y=quality, mode='lines', name='Quality',
                                line=dict(color='purple', width=2), fill='tozeroy'), row=2, col=1)

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Quality", range=[0, 1.1], row=2, col=1)
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Metrics
    valid_cleaned = ~np.isnan(cleaned_signal)
    reconstruction_error = np.abs(cleaned_signal[valid_cleaned] - true_signal[valid_cleaned])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Raw Quality", f"{np.sum(~np.isnan(raw_signal))/len(time)*100:.0f}%")
    with col2:
        st.metric("Cleaned Quality", f"{np.sum(valid_cleaned)/len(time)*100:.0f}%")
    with col3:
        st.metric("Avg Quality Score", f"{np.mean(quality):.2f}")
    with col4:
        st.metric("RMS Error", f"{np.sqrt(np.mean(reconstruction_error**2)):.3f}")

    st.success("""
    **✅ Cleaning Pipeline Results:**
    - Invalid data detected and removed
    - Gaps filled with interpolation (quality score: 0.7)
    - Optional smoothing reduces noise
    - Quality metadata tracks confidence in each sample
    - Downstream systems can use quality to make informed decisions
    """)

st.markdown("---")
st.success("""
**🎓 Chapter 6 Complete!**

You've learned:
- ✅ Range validation to detect corrupted values
- ✅ Interpolation methods for gap filling
- ✅ Complete cleaning pipeline integration
- ✅ Quality scoring and metadata
- ✅ Tradeoffs between repair and rejection
- ✅ Why validation is critical for mission data

**Next Steps**: Proceed to Chapter 7 to learn about anomaly detection -
identifying unusual patterns in clean telemetry.
""")

st.markdown("*Navigate to Chapter 7: Anomaly Detection in the sidebar →*")
