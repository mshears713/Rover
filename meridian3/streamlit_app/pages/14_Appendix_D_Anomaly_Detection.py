"""
Appendix D: How Anomalies are Detected

TEACHING FOCUS:
    - Threshold-based detection algorithms
    - Rate-of-change and derivative monitoring
    - Statistical anomaly scoring (z-scores)
    - Alert prioritization and classification

NARRATIVE:
    This appendix explains how the system identifies anomalous behavior
    in telemetry data. It covers multiple detection strategies, from
    simple thresholds to statistical methods, and how alerts are
    prioritized.

LEARNING OBJECTIVES:
    - Understand anomaly detection strategies
    - Learn threshold and statistical methods
    - See alert classification in practice
    - Master the anomaly detection pipeline
    - Distinguish false positives from real anomalies

ARCHITECTURE:
    The anomaly detection pipeline uses multiple detectors:
    1. Threshold Detector: Simple min/max violations
    2. Rate-of-Change Detector: Sudden changes
    3. Statistical Detector: Z-score outliers
    4. Alert Aggregator: Combine and prioritize

TEACHING APPROACH:
    - Interactive detector configuration
    - Real-time anomaly injection
    - ROC curve analysis
    - Multi-detector fusion demos

IMPLEMENTATION:
    Full interactive implementation following patterns from Chapters 1-3.
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

st.set_page_config(
    page_title="Appendix D: Anomaly Detection",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Appendix D: How Anomalies are Detected")

st.markdown("""
## From Clean Data to Actionable Alerts

Anomaly detection identifies unusual patterns in telemetry that may indicate
problems, failures, or interesting science. Multiple detection strategies work
together to catch different types of anomalies.

Understanding anomaly detection is critical for mission operations and rapid
response to potential issues.
""")

# ═══════════════════════════════════════════════════════════════════════════
# ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Anomaly Detection Architecture", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │            ANOMALY DETECTION PIPELINE                        │
    └──────────────────────────────────────────────────────────────┘

         ┌─────────────────┐
         │  Clean Data     │  Input: Validated telemetry
         │  ─────────────  │
         │  Time series   │  - Continuous values
         │  All sensors   │  - Complete records
         └────────┬────────┘
                  │
                  ├──────────────────┬──────────────────┐
                  ▼                  ▼                  ▼
         ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐
         │   Threshold     │  │ Rate-of-    │  │ Statistical │
         │   Detector      │  │ Change      │  │  Detector   │
         │  ─────────────  │  │  Detector   │  │ ─────────── │
         │  Min/Max check │  │ ─────────── │  │  Z-scores   │
         │  Hard limits   │  │  Derivative │  │  Outliers   │
         └────────┬────────┘  └──────┬──────┘  └──────┬──────┘
                  │                  │                  │
                  └──────────────────┴──────────────────┘
                                     │
                                     ▼
                           ┌──────────────────┐
                           │ Alert Aggregator │
                           │  ──────────────  │
                           │  Priority score  │
                           │  Classification  │
                           │  Deduplication   │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │     Alerts       │
                           │  ──────────────  │
                           │  Critical: 3     │
                           │  Warning: 12     │
                           │  Info: 45        │
                           └──────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Threshold Detection**
        - Simple min/max bounds
        - Fast evaluation
        - Low false positives
        - Catches hard violations
        - Easy to configure
        """)

    with col2:
        st.markdown("""
        **Rate-of-Change**
        - Monitors derivatives
        - Catches sudden jumps
        - Time-aware detection
        - Adjustable sensitivity
        - Good for transients
        """)

    with col3:
        st.markdown("""
        **Statistical Detection**
        - Z-score analysis
        - Adaptive thresholds
        - Rolling statistics
        - Outlier detection
        - Context-aware
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: THRESHOLD DETECTION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Threshold-Based Detection")

st.markdown("""
The simplest anomaly detector checks if values exceed **thresholds**. Let's
configure thresholds and see how well they catch anomalies.
""")

col1, col2, col3 = st.columns(3)

with col1:
    num_samples_exp1 = st.slider("Number of samples", 50, 200, 100, 25, key="exp1_samples")

with col2:
    threshold_min = st.number_input("Min threshold", -50.0, 50.0, 10.0, 1.0, key="exp1_min")
    threshold_max = st.number_input("Max threshold", -50.0, 50.0, 40.0, 1.0, key="exp1_max")

with col3:
    anomaly_count = st.slider("Anomalies to inject", 0, 20, 8, 1, key="exp1_anomalies")

if st.button("🔬 Run Threshold Detection", type="primary", key="exp1_run"):
    # Generate normal data
    t = np.linspace(0, 10, num_samples_exp1)
    baseline = 25.0
    normal_data = baseline + np.random.normal(0, 3, num_samples_exp1)

    # Inject anomalies
    anomaly_indices = np.random.choice(num_samples_exp1, anomaly_count, replace=False)
    data_with_anomalies = normal_data.copy()

    for idx in anomaly_indices:
        # Random choice: too high or too low
        if np.random.rand() > 0.5:
            data_with_anomalies[idx] = threshold_max + np.random.uniform(5, 20)
        else:
            data_with_anomalies[idx] = threshold_min - np.random.uniform(5, 20)

    # Detect anomalies
    detected_high = data_with_anomalies > threshold_max
    detected_low = data_with_anomalies < threshold_min
    detected = detected_high | detected_low

    # Calculate detection metrics
    true_positives = np.sum(detected[anomaly_indices])
    false_positives = np.sum(detected) - true_positives
    false_negatives = anomaly_count - true_positives
    true_negatives = num_samples_exp1 - anomaly_count - false_positives

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("True Positives", true_positives, help="Correctly detected anomalies")

    with col2:
        st.metric("False Positives", false_positives, help="False alarms")

    with col3:
        st.metric("Precision", f"{precision*100:.1f}%", help="Accuracy of detections")

    with col4:
        st.metric("Recall", f"{recall*100:.1f}%", help="% of anomalies caught")

    # Visualization
    fig = go.Figure()

    # Normal data
    normal_mask = ~detected
    fig.add_trace(go.Scatter(
        x=t[normal_mask],
        y=data_with_anomalies[normal_mask],
        mode='markers',
        name='Normal',
        marker=dict(color='green', size=6)
    ))

    # Detected anomalies
    detected_mask = detected
    fig.add_trace(go.Scatter(
        x=t[detected_mask],
        y=data_with_anomalies[detected_mask],
        mode='markers',
        name='Detected Anomalies',
        marker=dict(color='red', size=10, symbol='x')
    ))

    # Threshold lines
    fig.add_hline(y=threshold_max, line_dash="dash", line_color="orange",
                 annotation_text="Max Threshold")
    fig.add_hline(y=threshold_min, line_dash="dash", line_color="orange",
                 annotation_text="Min Threshold")

    # Acceptable range shading
    fig.add_hrect(y0=threshold_min, y1=threshold_max, fillcolor="green", opacity=0.1,
                 annotation_text="Normal Range", annotation_position="top left")

    fig.update_layout(
        title="Threshold-Based Anomaly Detection",
        xaxis_title="Time",
        yaxis_title="Value",
        height=450,
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Confusion matrix
    st.markdown("### 📊 Detection Performance")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Confusion Matrix:**")
        confusion_df = pd.DataFrame({
            'Actual Normal': [true_negatives, false_positives],
            'Actual Anomaly': [false_negatives, true_positives]
        }, index=['Predicted Normal', 'Predicted Anomaly'])

        st.dataframe(confusion_df, use_container_width=True)

    with col2:
        st.markdown("**Performance Metrics:**")
        st.code(f"""
Precision: {precision*100:.1f}%
  (Of detected, % truly anomalous)

Recall: {recall*100:.1f}%
  (Of actual anomalies, % detected)

F1 Score: {f1_score:.3f}
  (Harmonic mean of precision/recall)

Accuracy: {((true_positives + true_negatives) / num_samples_exp1)*100:.1f}%
  (Overall correctness)
        """, language="text")

    st.info("""
    **📚 Threshold Detection Insights:**
    - **Simple and fast**: Minimal computation required
    - **Low false positives**: When thresholds are well-chosen
    - **May miss subtle anomalies**: Only catches extreme values
    - **Requires domain knowledge**: Setting appropriate thresholds
    - **Best for**: Hard limit violations (temp, voltage, pressure)
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: RATE-OF-CHANGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Rate-of-Change Detection")

st.markdown("""
Some anomalies manifest as **sudden changes** rather than absolute value violations.
Rate-of-change detection monitors the derivative to catch rapid transitions.
""")

col1, col2 = st.columns(2)

with col1:
    num_samples_exp2 = st.slider("Number of samples", 60, 150, 100, 10, key="exp2_samples")

with col2:
    rate_threshold = st.slider("Rate threshold (change/step)", 1.0, 20.0, 8.0, 0.5, key="exp2_threshold")

if st.button("🔬 Detect Rapid Changes", type="primary", key="exp2_run"):
    # Generate slowly varying signal
    t = np.linspace(0, 10, num_samples_exp2)
    signal = 25 + 5 * np.sin(2 * np.pi * 0.2 * t) + np.random.normal(0, 0.5, num_samples_exp2)

    # Inject sudden spikes (rapid changes)
    num_spikes = 5
    spike_indices = np.random.choice(range(10, num_samples_exp2-10), num_spikes, replace=False)

    for idx in spike_indices:
        # Create a sudden jump
        signal[idx] += np.random.choice([-1, 1]) * np.random.uniform(15, 25)

    # Calculate rate of change (derivative)
    rate_of_change = np.diff(signal)
    rate_of_change = np.concatenate([[0], rate_of_change])  # Pad to same length

    # Detect anomalies
    anomalies_detected = np.abs(rate_of_change) > rate_threshold

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Spikes Injected", num_spikes)

    with col2:
        st.metric("Detections", np.sum(anomalies_detected))

    with col3:
        max_rate = np.max(np.abs(rate_of_change))
        st.metric("Max Rate Observed", f"{max_rate:.2f}")

    with col4:
        avg_normal_rate = np.mean(np.abs(rate_of_change[~anomalies_detected]))
        st.metric("Avg Normal Rate", f"{avg_normal_rate:.2f}")

    # Visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Signal with Rapid Changes", "Rate of Change (Derivative)"),
        vertical_spacing=0.15,
        row_heights=[0.55, 0.45]
    )

    # Signal plot
    fig.add_trace(go.Scatter(
        x=t,
        y=signal,
        mode='lines+markers',
        name='Signal',
        line=dict(color='steelblue', width=2),
        marker=dict(size=4)
    ), row=1, col=1)

    # Mark anomalies on signal
    fig.add_trace(go.Scatter(
        x=t[anomalies_detected],
        y=signal[anomalies_detected],
        mode='markers',
        name='Detected Anomalies',
        marker=dict(color='red', size=10, symbol='x')
    ), row=1, col=1)

    # Rate of change plot
    fig.add_trace(go.Scatter(
        x=t,
        y=rate_of_change,
        mode='lines',
        name='Rate of Change',
        line=dict(color='orange', width=2)
    ), row=2, col=1)

    # Threshold lines
    fig.add_hline(y=rate_threshold, line_dash="dash", line_color="red",
                 annotation_text="Threshold", row=2, col=1)
    fig.add_hline(y=-rate_threshold, line_dash="dash", line_color="red", row=2, col=1)

    # Shading for normal range
    fig.add_hrect(y0=-rate_threshold, y1=rate_threshold, fillcolor="green", opacity=0.1,
                 row=2, col=1)

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Rate", row=2, col=1)

    fig.update_layout(height=700, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    st.info("""
    **📚 Rate-of-Change Detection Insights:**
    - **Catches transients**: Detects sudden jumps, spikes, and drops
    - **Time-aware**: Considers temporal context
    - **Complementary**: Works alongside threshold detection
    - **Sensitive to noise**: May need filtering or smoothing
    - **Best for**: Equipment failures, state transitions, glitches
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: STATISTICAL Z-SCORE DETECTION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Statistical Z-Score Detection")

st.markdown("""
Statistical detectors use **z-scores** to identify outliers based on how many
standard deviations a value deviates from the mean. This adapts to signal characteristics.
""")

col1, col2, col3 = st.columns(3)

with col1:
    num_samples_exp3 = st.slider("Number of samples", 80, 200, 120, 20, key="exp3_samples")

with col2:
    z_threshold = st.slider("Z-score threshold", 1.5, 5.0, 3.0, 0.5, key="exp3_z",
                           help="Typical: 3 = 99.7% confidence")

with col3:
    window_size = st.slider("Rolling window size", 10, 50, 30, 5, key="exp3_window",
                           help="For rolling statistics")

if st.button("🔬 Run Z-Score Detection", type="primary", key="exp3_run"):
    # Generate data with varying characteristics
    t = np.linspace(0, 10, num_samples_exp3)
    baseline = 30 + 10 * np.sin(2 * np.pi * 0.15 * t)  # Slow trend
    noise = np.random.normal(0, 2, num_samples_exp3)
    signal = baseline + noise

    # Inject outliers
    num_outliers = 8
    outlier_indices = np.random.choice(num_samples_exp3, num_outliers, replace=False)

    for idx in outlier_indices:
        signal[idx] += np.random.choice([-1, 1]) * np.random.uniform(15, 25)

    # Calculate rolling statistics
    df = pd.DataFrame({'value': signal})
    rolling_mean = df['value'].rolling(window=window_size, center=True).mean()
    rolling_std = df['value'].rolling(window=window_size, center=True).std()

    # Calculate z-scores
    z_scores = np.abs((signal - rolling_mean) / rolling_std)

    # Detect anomalies
    anomalies = z_scores > z_threshold

    # Handle NaN values from rolling window
    anomalies = anomalies.fillna(False).values
    z_scores = z_scores.fillna(0).values

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Outliers Injected", num_outliers)

    with col2:
        st.metric("Detections", np.sum(anomalies))

    with col3:
        max_z = np.max(z_scores)
        st.metric("Max Z-Score", f"{max_z:.2f}")

    with col4:
        detected_true = np.sum(anomalies[outlier_indices])
        st.metric("True Positives", detected_true)

    # Visualization
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Signal with Outliers", "Rolling Statistics", "Z-Scores"),
        vertical_spacing=0.1,
        row_heights=[0.35, 0.3, 0.35]
    )

    # Signal
    fig.add_trace(go.Scatter(
        x=t,
        y=signal,
        mode='lines+markers',
        name='Signal',
        line=dict(color='steelblue', width=1),
        marker=dict(size=4)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=t[anomalies],
        y=signal[anomalies],
        mode='markers',
        name='Detected Outliers',
        marker=dict(color='red', size=10, symbol='x')
    ), row=1, col=1)

    # Rolling statistics
    fig.add_trace(go.Scatter(
        x=t,
        y=rolling_mean,
        mode='lines',
        name='Rolling Mean',
        line=dict(color='green', width=2)
    ), row=2, col=1)

    # Confidence band
    upper_bound = rolling_mean + z_threshold * rolling_std
    lower_bound = rolling_mean - z_threshold * rolling_std

    fig.add_trace(go.Scatter(
        x=t,
        y=upper_bound,
        mode='lines',
        name=f'+{z_threshold}σ',
        line=dict(color='orange', width=1, dash='dash'),
        showlegend=False
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=t,
        y=lower_bound,
        mode='lines',
        name=f'-{z_threshold}σ',
        line=dict(color='orange', width=1, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(255, 165, 0, 0.1)'
    ), row=2, col=1)

    # Z-scores
    fig.add_trace(go.Scatter(
        x=t,
        y=z_scores,
        mode='lines',
        name='Z-Score',
        line=dict(color='purple', width=2)
    ), row=3, col=1)

    fig.add_hline(y=z_threshold, line_dash="dash", line_color="red",
                 annotation_text="Threshold", row=3, col=1)

    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Value", row=2, col=1)
    fig.update_yaxes(title_text="Z-Score", row=3, col=1)

    fig.update_layout(height=900, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    st.info("""
    **📚 Z-Score Detection Insights:**
    - **Adaptive**: Adjusts to signal mean and variance
    - **Statistically grounded**: Based on normal distribution theory
    - **Configurable**: Z-threshold controls sensitivity
    - **Rolling window**: Handles non-stationary signals
    - **Z=3**: Detects values beyond 99.7% of normal distribution
    - **Best for**: General outlier detection, varying baselines
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: MULTI-DETECTOR FUSION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Multi-Detector Fusion")

st.markdown("""
Real systems use **multiple detectors** simultaneously. Let's run all three
detectors and see how they complement each other.
""")

col1, col2 = st.columns(2)

with col1:
    num_samples_exp4 = st.slider("Number of samples", 80, 150, 100, 10, key="exp4_samples")

with col2:
    fusion_strategy = st.selectbox(
        "Fusion strategy",
        ["Any detector (OR)", "Majority vote", "All detectors (AND)"],
        key="exp4_fusion"
    )

if st.button("🔬 Run Multi-Detector System", type="primary", key="exp4_run"):
    # Generate complex signal with multiple anomaly types
    t = np.linspace(0, 10, num_samples_exp4)
    signal = 25 + 8 * np.sin(2 * np.pi * 0.2 * t) + np.random.normal(0, 1.5, num_samples_exp4)

    # Inject different anomaly types
    # Type 1: Threshold violation
    threshold_anomaly_idx = [20, 50, 80]
    for idx in threshold_anomaly_idx:
        if idx < len(signal):
            signal[idx] = 55  # Way above threshold

    # Type 2: Sudden spike (rate-of-change)
    spike_idx = [35, 65]
    for idx in spike_idx:
        if idx < len(signal):
            signal[idx] += 20

    # Type 3: Statistical outlier
    outlier_idx = [15, 45, 75, 95]
    for idx in outlier_idx:
        if idx < len(signal):
            signal[idx] += np.random.choice([-1, 1]) * 12

    # Run all detectors
    # 1. Threshold detector
    threshold_min_exp4 = 5
    threshold_max_exp4 = 45
    detected_threshold = (signal > threshold_max_exp4) | (signal < threshold_min_exp4)

    # 2. Rate-of-change detector
    rate_of_change = np.diff(signal)
    rate_of_change = np.concatenate([[0], rate_of_change])
    rate_threshold_exp4 = 8
    detected_rate = np.abs(rate_of_change) > rate_threshold_exp4

    # 3. Z-score detector
    rolling_mean = pd.Series(signal).rolling(window=20, center=True).mean()
    rolling_std = pd.Series(signal).rolling(window=20, center=True).std()
    z_scores = np.abs((signal - rolling_mean) / rolling_std)
    detected_z = (z_scores > 2.5).fillna(False).values

    # Fusion
    if fusion_strategy == "Any detector (OR)":
        final_detection = detected_threshold | detected_rate | detected_z
    elif fusion_strategy == "Majority vote":
        votes = detected_threshold.astype(int) + detected_rate.astype(int) + detected_z.astype(int)
        final_detection = votes >= 2
    else:  # AND
        final_detection = detected_threshold & detected_rate & detected_z

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Threshold Detections", np.sum(detected_threshold))

    with col2:
        st.metric("Rate Detections", np.sum(detected_rate))

    with col3:
        st.metric("Z-Score Detections", np.sum(detected_z))

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Final (Fused) Detections", np.sum(final_detection))

    with col2:
        coverage = (np.sum(detected_threshold) + np.sum(detected_rate) + np.sum(detected_z)) / 3
        st.metric("Avg Detector Coverage", f"{coverage:.1f} detections")

    # Visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Multi-Detector Results", "Detection Comparison"),
        vertical_spacing=0.15,
        row_heights=[0.65, 0.35]
    )

    # Signal with detections
    fig.add_trace(go.Scatter(
        x=t,
        y=signal,
        mode='lines',
        name='Signal',
        line=dict(color='lightgray', width=1)
    ), row=1, col=1)

    # Show each detector's findings
    if np.sum(detected_threshold) > 0:
        fig.add_trace(go.Scatter(
            x=t[detected_threshold],
            y=signal[detected_threshold],
            mode='markers',
            name='Threshold',
            marker=dict(color='blue', size=8, symbol='square')
        ), row=1, col=1)

    if np.sum(detected_rate) > 0:
        fig.add_trace(go.Scatter(
            x=t[detected_rate],
            y=signal[detected_rate],
            mode='markers',
            name='Rate-of-Change',
            marker=dict(color='orange', size=8, symbol='diamond')
        ), row=1, col=1)

    if np.sum(detected_z) > 0:
        fig.add_trace(go.Scatter(
            x=t[detected_z],
            y=signal[detected_z],
            mode='markers',
            name='Z-Score',
            marker=dict(color='purple', size=8, symbol='triangle-up')
        ), row=1, col=1)

    # Final fused detections
    if np.sum(final_detection) > 0:
        fig.add_trace(go.Scatter(
            x=t[final_detection],
            y=signal[final_detection],
            mode='markers',
            name='Fused Detection',
            marker=dict(color='red', size=12, symbol='x', line=dict(width=2))
        ), row=1, col=1)

    # Detector agreement heatmap
    detector_data = np.vstack([
        detected_threshold.astype(int),
        detected_rate.astype(int),
        detected_z.astype(int)
    ])

    fig.add_trace(go.Heatmap(
        z=detector_data,
        x=t,
        y=['Threshold', 'Rate', 'Z-Score'],
        colorscale=[[0, 'white'], [1, 'red']],
        showscale=False,
        name='Detector Activity'
    ), row=2, col=1)

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Detector", row=2, col=1)

    fig.update_layout(height=750, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Detector comparison
    st.markdown("### 📊 Detector Performance Comparison")

    comparison_df = pd.DataFrame({
        'Detector': ['Threshold', 'Rate-of-Change', 'Z-Score', f'Fused ({fusion_strategy})'],
        'Detections': [
            np.sum(detected_threshold),
            np.sum(detected_rate),
            np.sum(detected_z),
            np.sum(final_detection)
        ],
        'Sensitivity': ['Low', 'Medium', 'High', 'Varies'],
        'Best For': [
            'Hard limits',
            'Transients',
            'Outliers',
            'Combined coverage'
        ]
    })

    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    st.success("""
    **✅ Multi-Detector Fusion Benefits:**
    - **Complementary coverage**: Different detectors catch different anomaly types
    - **Reduced false negatives**: Multiple chances to detect each anomaly
    - **Configurable fusion**: Tune strategy based on mission needs
    - **OR fusion**: Maximum sensitivity, may increase false positives
    - **AND fusion**: Maximum precision, may miss some anomalies
    - **Majority vote**: Balanced approach, good compromise
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Appendix D Complete!**

You've learned:
- ✅ Threshold-based detection for hard limit violations
- ✅ Rate-of-change detection for transients and spikes
- ✅ Statistical z-score detection for outliers
- ✅ Multi-detector fusion strategies
- ✅ Performance metrics (precision, recall, F1)
- ✅ How different detectors complement each other

**Connection to Mission**: Anomaly detection is mission-critical for rover operations.
Early detection of failures, sensor drift, or unexpected conditions enables rapid
response and may prevent catastrophic failures. Understanding detector characteristics
helps operators tune systems for optimal performance.

**Next**: Proceed to Appendix E to learn visualization techniques for telemetry and anomalies.
""")

st.markdown("*Navigate to Appendix E: Data Visualization in the sidebar →*")
