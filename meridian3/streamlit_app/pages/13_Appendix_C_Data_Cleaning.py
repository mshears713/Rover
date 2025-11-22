"""
Appendix C: How Data Gets Cleaned

TEACHING FOCUS:
    - Data validation and range checking
    - Interpolation strategies for missing data
    - Reconstruction techniques for corrupted values
    - Quality metrics and reporting

NARRATIVE:
    This appendix details how corrupted and incomplete telemetry is
    cleaned and validated. It covers range checking, interpolation,
    reconstruction algorithms, and quality assessment.

LEARNING OBJECTIVES:
    - Understand data cleaning strategies
    - Learn interpolation and reconstruction methods
    - See validation and quality metrics in action
    - Master the data cleaning pipeline
    - Distinguish cleanable vs unrecoverable errors

ARCHITECTURE:
    The data cleaning pipeline processes corrupted data:
    1. Validation: Check ranges and detect corruption
    2. Interpolation: Fill gaps with estimated values
    3. Reconstruction: Repair corrupted data
    4. Quality Metrics: Assess cleaning effectiveness

TEACHING APPROACH:
    - Interactive corruption and cleaning demos
    - Side-by-side before/after comparisons
    - Statistical quality assessment
    - Real-world scenario simulations

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
    page_title="Appendix C: Data Cleaning",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Appendix C: How Data Gets Cleaned")

st.markdown("""
## From Corrupted Packets to Validated Data

Transmission errors corrupt data. Missing packets create gaps. The **data cleaner**
repairs what it can, flags what it cannot, and assesses overall data quality.

Understanding data cleaning is essential for trusting telemetry and making
mission-critical decisions.
""")

# ═══════════════════════════════════════════════════════════════════════════
# ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Data Cleaning Architecture", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │                DATA CLEANING PIPELINE                        │
    └──────────────────────────────────────────────────────────────┘

         ┌─────────────────┐
         │ Corrupted Data  │  Input: Damaged packets
         │  ─────────────  │
         │  • Missing gaps │  - Packet loss
         │  • Bad values   │  - Bit flips
         │  • Out of range │  - Transmission errors
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   Validator     │  Check Ranges
         │  ─────────────  │
         │  • Min/max     │  - Detect invalid values
         │  • Type check  │  - Flag corruption
         │  • Flagging    │  - Mark suspicious data
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Interpolator   │  Fill Gaps
         │  ─────────────  │
         │  • Linear      │  - Simple average
         │  • Cubic       │  - Smooth curves
         │  • Forward     │  - Last valid value
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Clean Data      │  Output: Validated
         │  ─────────────  │
         │  • Complete    │  - No gaps
         │  • Validated   │  - Range checked
         │  • Flagged     │  - Quality scored
         └─────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Validation**
        - Range checking
        - Type verification
        - Corruption detection
        - Confidence scoring
        - Flag generation
        """)

    with col2:
        st.markdown("""
        **Interpolation**
        - Linear interpolation
        - Cubic spline
        - Forward/backward fill
        - Windowed averaging
        - Confidence intervals
        """)

    with col3:
        st.markdown("""
        **Quality Metrics**
        - Completeness %
        - Validity %
        - Reconstruction quality
        - Confidence scores
        - Alert thresholds
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: RANGE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Range Validation")

st.markdown("""
The first step in cleaning is **validation**: checking if values fall within
acceptable ranges. Let's create data with out-of-range values and validate it.
""")

try:
    from pipeline.cleaner import DataCleaner

    col1, col2, col3 = st.columns(3)

    with col1:
        num_points = st.slider("Number of data points", 20, 100, 50, 10, key="exp1_points")

    with col2:
        corruption_rate = st.slider("Corruption rate (%)", 0, 50, 20, 5, key="exp1_corrupt")

    with col3:
        valid_range_min = st.number_input("Valid min", -100.0, 100.0, 0.0, 1.0, key="exp1_min")
        valid_range_max = st.number_input("Valid max", -100.0, 100.0, 50.0, 1.0, key="exp1_max")

    if st.button("🔬 Generate and Validate Data", type="primary", key="exp1_run"):
        # Generate data
        np.random.seed(42)
        true_data = np.random.uniform(valid_range_min, valid_range_max, num_points)

        # Corrupt some values (out of range)
        corrupted_data = true_data.copy()
        num_corrupt = int(num_points * corruption_rate / 100)
        corrupt_indices = np.random.choice(num_points, num_corrupt, replace=False)

        for idx in corrupt_indices:
            # Set to clearly invalid value
            if np.random.rand() > 0.5:
                corrupted_data[idx] = valid_range_max + np.random.uniform(10, 50)
            else:
                corrupted_data[idx] = valid_range_min - np.random.uniform(10, 50)

        # Validate
        is_valid = (corrupted_data >= valid_range_min) & (corrupted_data <= valid_range_max)

        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Points", num_points)

        with col2:
            st.metric("Valid Points", np.sum(is_valid))

        with col3:
            st.metric("Invalid Points", np.sum(~is_valid), delta="Flagged")

        with col4:
            validity_pct = (np.sum(is_valid) / num_points) * 100
            st.metric("Validity %", f"{validity_pct:.1f}%")

        # Visualization
        fig = go.Figure()

        # Valid points
        valid_x = np.where(is_valid)[0]
        fig.add_trace(go.Scatter(
            x=valid_x,
            y=corrupted_data[valid_x],
            mode='markers',
            name='Valid',
            marker=dict(color='green', size=6)
        ))

        # Invalid points
        invalid_x = np.where(~is_valid)[0]
        fig.add_trace(go.Scatter(
            x=invalid_x,
            y=corrupted_data[invalid_x],
            mode='markers',
            name='Invalid (Flagged)',
            marker=dict(color='red', size=8, symbol='x')
        ))

        # Range bounds
        fig.add_hline(y=valid_range_min, line_dash="dash", line_color="blue",
                     annotation_text="Min Valid")
        fig.add_hline(y=valid_range_max, line_dash="dash", line_color="blue",
                     annotation_text="Max Valid")

        fig.update_layout(
            title="Data Validation: Flagging Out-of-Range Values",
            xaxis_title="Sample Index",
            yaxis_title="Value",
            height=400,
            hovermode='closest'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **📚 Key Observations:**
        - **Range validation** is the first line of defense against corruption
        - **Invalid values** are clearly visible as outliers
        - **Physical limits** define acceptable ranges (e.g., temp: -40 to 125°C)
        - **Flagged data** can be interpolated or discarded
        - **Validation rate** indicates transmission quality
        """)

except ImportError:
    st.warning("DataCleaner not available. Showing simulation with synthetic data.")

    # Fallback simulation if module not available
    col1, col2, col3 = st.columns(3)
    with col1:
        num_points = st.slider("Number of data points", 20, 100, 50, 10, key="exp1_points_fb")
    with col2:
        corruption_rate = st.slider("Corruption rate (%)", 0, 50, 20, 5, key="exp1_corrupt_fb")
    with col3:
        valid_range = st.slider("Valid range", 10.0, 100.0, 50.0, 5.0, key="exp1_range_fb")

    if st.button("🔬 Simulate Validation", type="primary", key="exp1_run_fb"):
        st.info("Simulation mode: DataCleaner module would perform this validation in production.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: MISSING DATA INTERPOLATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Missing Data Interpolation")

st.markdown("""
When packets are lost, data has **gaps**. We can fill these gaps using interpolation.
Let's compare different interpolation methods.
""")

col1, col2, col3 = st.columns(3)

with col1:
    num_samples = st.slider("Total samples", 30, 100, 60, 10, key="exp2_samples")

with col2:
    gap_percent = st.slider("Missing data (%)", 5, 40, 20, 5, key="exp2_gap")

with col3:
    interp_method = st.selectbox(
        "Interpolation method",
        ["Linear", "Cubic", "Forward Fill", "Nearest"],
        key="exp2_method"
    )

if st.button("🔬 Interpolate Missing Data", type="primary", key="exp2_run"):
    # Generate smooth signal
    x_full = np.linspace(0, 10, num_samples)
    y_true = 10 + 5 * np.sin(2 * np.pi * 0.3 * x_full) + np.random.normal(0, 0.3, num_samples)

    # Create gaps
    num_missing = int(num_samples * gap_percent / 100)
    missing_indices = np.random.choice(num_samples, num_missing, replace=False)
    missing_indices.sort()

    y_with_gaps = y_true.copy()
    y_with_gaps[missing_indices] = np.nan

    # Interpolate
    df = pd.DataFrame({'x': x_full, 'y': y_with_gaps})

    if interp_method == "Linear":
        df['y_interp'] = df['y'].interpolate(method='linear')
    elif interp_method == "Cubic":
        df['y_interp'] = df['y'].interpolate(method='cubic')
    elif interp_method == "Forward Fill":
        df['y_interp'] = df['y'].fillna(method='ffill')
    elif interp_method == "Nearest":
        df['y_interp'] = df['y'].interpolate(method='nearest')

    # Calculate error for interpolated points
    interp_error = np.abs(y_true[missing_indices] - df['y_interp'].iloc[missing_indices].values)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Points", num_samples)

    with col2:
        st.metric("Missing", num_missing)

    with col3:
        st.metric("Interpolated", num_missing)

    with col4:
        st.metric("Avg Error", f"{np.mean(interp_error):.3f}")

    # Visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Data with Gaps and Interpolation", "Interpolation Error"),
        vertical_spacing=0.15,
        row_heights=[0.65, 0.35]
    )

    # Original data
    valid_mask = ~df['y'].isna()
    fig.add_trace(go.Scatter(
        x=df['x'][valid_mask],
        y=df['y'][valid_mask],
        mode='markers',
        name='Valid Data',
        marker=dict(color='green', size=6)
    ), row=1, col=1)

    # Interpolated points
    fig.add_trace(go.Scatter(
        x=df['x'].iloc[missing_indices],
        y=df['y_interp'].iloc[missing_indices],
        mode='markers',
        name='Interpolated',
        marker=dict(color='orange', size=8, symbol='diamond')
    ), row=1, col=1)

    # True values (for comparison)
    fig.add_trace(go.Scatter(
        x=x_full,
        y=y_true,
        mode='lines',
        name='True Signal',
        line=dict(color='lightblue', width=1, dash='dot'),
        opacity=0.5
    ), row=1, col=1)

    # Interpolation line
    fig.add_trace(go.Scatter(
        x=df['x'],
        y=df['y_interp'],
        mode='lines',
        name=f'{interp_method} Interpolation',
        line=dict(color='steelblue', width=2)
    ), row=1, col=1)

    # Error plot
    fig.add_trace(go.Bar(
        x=missing_indices,
        y=interp_error,
        name='Abs Error',
        marker_color='orange'
    ), row=2, col=1)

    fig.update_xaxes(title_text="Sample Index", row=2, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Error", row=2, col=1)

    fig.update_layout(height=700, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Method comparison
    st.markdown("### 📊 Interpolation Method Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **{interp_method} Interpolation:**
        - RMSE: {np.sqrt(np.mean(interp_error**2)):.3f}
        - Max Error: {np.max(interp_error):.3f}
        - Mean Error: {np.mean(interp_error):.3f}
        - Std Error: {np.std(interp_error):.3f}
        """)

    with col2:
        st.markdown("""
        **Method Characteristics:**
        - **Linear**: Fast, simple, works well for slowly changing data
        - **Cubic**: Smooth curves, better for sinusoidal patterns
        - **Forward Fill**: Preserves last value, simple but creates steps
        - **Nearest**: Jumps to closest value, good for discrete states
        """)

    st.info("""
    **📚 Key Observations:**
    - **Interpolation quality** depends on signal characteristics
    - **Short gaps** (1-3 points) interpolate well
    - **Long gaps** have higher uncertainty
    - **Smooth signals** benefit from cubic interpolation
    - **Noisy signals** may prefer simpler methods
    - Always include **confidence bounds** on interpolated values
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: CORRUPTION RECONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Corrupted Data Reconstruction")

st.markdown("""
Sometimes data is corrupted but not completely lost. We can attempt to reconstruct
it using neighboring values and statistical methods.
""")

col1, col2 = st.columns(2)

with col1:
    num_points_exp3 = st.slider("Number of data points", 40, 120, 80, 20, key="exp3_points")

with col2:
    corruption_pct = st.slider("Corruption level (%)", 5, 30, 15, 5, key="exp3_corruption")

if st.button("🔬 Reconstruct Corrupted Data", type="primary", key="exp3_run"):
    # Generate smooth signal
    t = np.linspace(0, 10, num_points_exp3)
    true_signal = 25 + 10 * np.sin(2 * np.pi * 0.2 * t) + np.random.normal(0, 0.5, num_points_exp3)

    # Corrupt some points (add large random noise)
    corrupted = true_signal.copy()
    num_corrupt = int(num_points_exp3 * corruption_pct / 100)
    corrupt_idx = np.random.choice(num_points_exp3, num_corrupt, replace=False)

    for idx in corrupt_idx:
        corrupted[idx] += np.random.normal(0, 15)  # Large corruption

    # Simple reconstruction: replace outliers with moving average
    window_size = 5
    moving_avg = pd.Series(corrupted).rolling(window=window_size, center=True).mean()

    reconstructed = corrupted.copy()
    for idx in corrupt_idx:
        # If significantly different from moving average, replace
        if not np.isnan(moving_avg[idx]):
            reconstructed[idx] = moving_avg[idx]

    # Calculate reconstruction quality
    reconstruction_error = np.abs(reconstructed[corrupt_idx] - true_signal[corrupt_idx])
    original_error = np.abs(corrupted[corrupt_idx] - true_signal[corrupt_idx])

    # Visualization
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Original (Corrupted)", "After Reconstruction", "Error Comparison"),
        vertical_spacing=0.1,
        row_heights=[0.35, 0.35, 0.3]
    )

    # Corrupted signal
    fig.add_trace(go.Scatter(
        x=t, y=corrupted, mode='lines+markers',
        name='Corrupted', line=dict(color='red', width=1),
        marker=dict(size=4)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=t[corrupt_idx], y=corrupted[corrupt_idx],
        mode='markers', name='Corrupted Points',
        marker=dict(color='darkred', size=8, symbol='x')
    ), row=1, col=1)

    # Reconstructed signal
    fig.add_trace(go.Scatter(
        x=t, y=reconstructed, mode='lines+markers',
        name='Reconstructed', line=dict(color='green', width=1),
        marker=dict(size=4)
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=t, y=true_signal, mode='lines',
        name='True Signal', line=dict(color='blue', width=2, dash='dot'),
        opacity=0.5
    ), row=2, col=1)

    # Error comparison
    fig.add_trace(go.Bar(
        x=corrupt_idx, y=original_error,
        name='Error Before', marker_color='red', opacity=0.6
    ), row=3, col=1)

    fig.add_trace(go.Bar(
        x=corrupt_idx, y=reconstruction_error,
        name='Error After', marker_color='green', opacity=0.6
    ), row=3, col=1)

    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Value", row=2, col=1)
    fig.update_yaxes(title_text="Abs Error", row=3, col=1)

    fig.update_layout(height=900, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Corrupted Points", num_corrupt)

    with col2:
        st.metric("RMSE Before", f"{np.sqrt(np.mean(original_error**2)):.2f}")

    with col3:
        st.metric("RMSE After", f"{np.sqrt(np.mean(reconstruction_error**2)):.2f}")

    with col4:
        improvement = ((np.mean(original_error) - np.mean(reconstruction_error)) / np.mean(original_error)) * 100
        st.metric("Improvement", f"{improvement:.1f}%")

    st.success("""
    **✅ Reconstruction Analysis:**
    - **Moving average** smooths out corruption spikes
    - **Reconstruction quality** depends on corruption severity
    - **Neighboring values** provide context for repair
    - **Not all corruption** can be perfectly repaired
    - **Quality metrics** help assess trustworthiness
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: DATA QUALITY METRICS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Data Quality Assessment")

st.markdown("""
After cleaning, we must assess **data quality**. Multiple metrics combine to give
an overall quality score that guides decision-making.
""")

col1, col2, col3 = st.columns(3)

with col1:
    dataset_size = st.slider("Dataset size", 50, 200, 100, 25, key="exp4_size")

with col2:
    missing_pct = st.slider("Missing %", 0, 30, 10, 5, key="exp4_missing")

with col3:
    invalid_pct = st.slider("Invalid %", 0, 30, 5, 5, key="exp4_invalid")

if st.button("📊 Calculate Quality Metrics", type="primary", key="exp4_run"):
    # Simulate dataset
    num_missing = int(dataset_size * missing_pct / 100)
    num_invalid = int(dataset_size * invalid_pct / 100)
    num_valid = dataset_size - num_missing - num_invalid

    # Calculate quality metrics
    completeness = (dataset_size - num_missing) / dataset_size * 100
    validity = num_valid / (dataset_size - num_missing) * 100 if (dataset_size - num_missing) > 0 else 0
    overall_quality = (num_valid / dataset_size) * 100

    # Determine quality grade
    if overall_quality >= 95:
        grade = "A - Excellent"
        color = "green"
    elif overall_quality >= 85:
        grade = "B - Good"
        color = "lightgreen"
    elif overall_quality >= 70:
        grade = "C - Fair"
        color = "yellow"
    elif overall_quality >= 50:
        grade = "D - Poor"
        color = "orange"
    else:
        grade = "F - Unacceptable"
        color = "red"

    # Display metrics
    st.markdown("### 📊 Quality Metrics Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Completeness", f"{completeness:.1f}%",
                 help="Percentage of non-missing data")

    with col2:
        st.metric("Validity", f"{validity:.1f}%",
                 help="Percentage of in-range values")

    with col3:
        st.metric("Overall Quality", f"{overall_quality:.1f}%",
                 help="Combined quality score")

    with col4:
        st.metric("Quality Grade", grade)

    # Visualize breakdown
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Data Composition", "Quality Gauge"),
        specs=[[{"type": "pie"}, {"type": "indicator"}]]
    )

    # Pie chart
    fig.add_trace(go.Pie(
        labels=['Valid', 'Invalid', 'Missing'],
        values=[num_valid, num_invalid, num_missing],
        marker_colors=['green', 'orange', 'red']
    ), row=1, col=1)

    # Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=overall_quality,
        title={'text': "Overall Quality"},
        delta={'reference': 95, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "lightyellow"},
                {'range': [70, 85], 'color': "lightgreen"},
                {'range': [85, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ), row=1, col=2)

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed breakdown
    st.markdown("### 📋 Detailed Quality Report")

    report = f"""
    ```
    ═══════════════════════════════════════════════════
              DATA QUALITY ASSESSMENT REPORT
    ═══════════════════════════════════════════════════

    Dataset Size:        {dataset_size} samples

    Data Breakdown:
      • Valid:           {num_valid} samples ({num_valid/dataset_size*100:.1f}%)
      • Invalid:         {num_invalid} samples ({num_invalid/dataset_size*100:.1f}%)
      • Missing:         {num_missing} samples ({num_missing/dataset_size*100:.1f}%)

    Quality Metrics:
      • Completeness:    {completeness:.1f}%
      • Validity:        {validity:.1f}%
      • Overall Quality: {overall_quality:.1f}%

    Quality Grade:       {grade}

    Recommendations:
    """

    if overall_quality >= 95:
        report += """
      ✅ Data quality is excellent. Proceed with confidence.
      ✅ Suitable for all analysis and decision-making.
    """
    elif overall_quality >= 85:
        report += """
      ✅ Data quality is good. Minor issues present.
      ⚠️  Consider additional validation for critical decisions.
    """
    elif overall_quality >= 70:
        report += """
      ⚠️  Data quality is fair. Significant gaps or errors.
      ⚠️  Use caution in analysis. Consider re-collection.
    """
    else:
        report += """
      ❌ Data quality is poor. Not suitable for critical use.
      ❌ Recommend re-collection or additional cleaning.
    """

    report += """
    ═══════════════════════════════════════════════════
    ```
    """

    st.code(report, language="text")

    st.info("""
    **📚 Quality Metrics Interpretation:**
    - **Completeness**: Measures data availability (no missing values)
    - **Validity**: Measures data correctness (within expected ranges)
    - **Overall Quality**: Combined metric for decision-making
    - **Grade A (95%+)**: Excellent, suitable for critical decisions
    - **Grade B (85-95%)**: Good, suitable for most analyses
    - **Grade C (70-85%)**: Fair, use caution
    - **Grade D/F (<70%)**: Poor, not recommended for use
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Appendix C Complete!**

You've learned:
- ✅ Data validation and range checking techniques
- ✅ Multiple interpolation methods for missing data
- ✅ Corruption detection and reconstruction strategies
- ✅ Quality metrics and scoring systems
- ✅ How to assess data trustworthiness
- ✅ When data is good enough for decision-making

**Connection to Mission**: Data cleaning is essential for mission success. Poor
quality data leads to bad decisions. Understanding cleaning strategies and quality
metrics enables confident use of telemetry in operations.

**Next**: Proceed to Appendix D to learn how anomalies are detected in cleaned data.
""")

st.markdown("*Navigate to Appendix D: Anomaly Detection in the sidebar →*")
