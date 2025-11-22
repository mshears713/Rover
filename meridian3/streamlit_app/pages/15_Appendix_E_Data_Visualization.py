"""
Appendix E: How Data is Visualized

TEACHING FOCUS:
    - Plotting strategies for time-series telemetry
    - Interactive visualization with Plotly
    - Statistical distribution displays
    - Real-time monitoring dashboards

NARRATIVE:
    This appendix covers the visualization layer of the Meridian-3
    system. It explains how raw data becomes meaningful charts,
    graphs, and dashboards for mission monitoring.

LEARNING OBJECTIVES:
    - Understand visualization best practices
    - Learn Plotly techniques for telemetry
    - See real-time dashboard implementation
    - Master the data visualization pipeline
    - Choose appropriate chart types

ARCHITECTURE:
    Visualization transforms data into actionable insights:
    1. Time Series Plots: Trend analysis
    2. Distributions: Statistical patterns
    3. Correlations: Multi-variable relationships
    4. Dashboards: Integrated monitoring

TEACHING APPROACH:
    - Interactive plot customization
    - Chart type comparison
    - Best practices demonstrations
    - Dashboard design patterns

IMPLEMENTATION:
    Full interactive implementation following patterns from Chapters 1-3.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(
    page_title="Appendix E: Data Visualization",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Appendix E: How Data is Visualized")

st.markdown("""
## From Raw Numbers to Actionable Insights

Visualization is the final step that makes telemetry **understandable** to mission
operators and scientists. Good visualizations reveal patterns, anomalies, and trends
that would be invisible in raw data.

Understanding visualization techniques is essential for effective mission monitoring
and data analysis.
""")

# ═══════════════════════════════════════════════════════════════════════════
# ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Visualization Architecture", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │               DATA VISUALIZATION PIPELINE                    │
    └──────────────────────────────────────────────────────────────┘

         ┌─────────────────┐
         │  Clean Data     │  Input: Validated telemetry
         │  ─────────────  │
         │  Time series   │  - Timestamps
         │  Multi-sensor  │  - Multiple channels
         └────────┬────────┘
                  │
                  ├──────────────────┬──────────────────┬──────────────┐
                  ▼                  ▼                  ▼              ▼
         ┌─────────────┐    ┌─────────────┐    ┌──────────┐   ┌────────────┐
         │ Time Series │    │Distribution │    │Correlation│   │ Dashboard  │
         │   Plots     │    │   Charts    │    │  Plots    │   │  Widgets   │
         │ ─────────── │    │ ─────────── │    │ ────────  │   │ ────────── │
         │  Line       │    │ Histogram   │    │ Scatter   │   │  Metrics   │
         │  Scatter    │    │ Box plot    │    │ Heatmap   │   │  Gauges    │
         │  Area       │    │ Violin      │    │ Matrix    │   │  Tables    │
         └─────────────┘    └─────────────┘    └──────────┘   └────────────┘
                  │                  │                  │              │
                  └──────────────────┴──────────────────┴──────────────┘
                                     │
                                     ▼
                           ┌──────────────────┐
                           │ Interactive      │
                           │  Visualization   │
                           │  ──────────────  │
                           │  Zoom/Pan       │
                           │  Hover tooltips │
                           │  Export         │
                           └──────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Time Series**
        - Line plots
        - Area fills
        - Multi-axis
        - Time range selection
        - Trend lines
        """)

    with col2:
        st.markdown("""
        **Distributions**
        - Histograms
        - Box plots
        - Violin plots
        - KDE curves
        - Statistical overlays
        """)

    with col3:
        st.markdown("""
        **Dashboards**
        - Metric cards
        - Gauge indicators
        - Multi-plot layouts
        - Real-time updates
        - Status indicators
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: TIME SERIES VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Time Series Visualization Techniques")

st.markdown("""
Time series plots are the foundation of telemetry visualization. Let's explore
different plot types and their use cases.
""")

col1, col2, col3 = st.columns(3)

with col1:
    num_points = st.slider("Number of data points", 50, 300, 150, 25, key="exp1_points")

with col2:
    plot_type = st.selectbox(
        "Plot type",
        ["Line", "Scatter", "Line + Markers", "Area Fill", "Multi-axis"],
        key="exp1_type"
    )

with col3:
    add_annotations = st.checkbox("Add annotations", value=False, key="exp1_annotate")

if st.button("📊 Generate Plot", type="primary", key="exp1_run"):
    # Generate sample telemetry data
    t = np.linspace(0, 24, num_points)  # 24 hours
    temperature = 20 + 15 * np.sin(2 * np.pi * t / 24) + np.random.normal(0, 2, num_points)
    battery_soc = 85 - 10 * (t / 24) + 5 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 1.5, num_points)

    # Create visualization based on selection
    if plot_type in ["Line", "Scatter", "Line + Markers", "Area Fill"]:
        fig = go.Figure()

        if plot_type == "Line":
            fig.add_trace(go.Scatter(
                x=t, y=temperature,
                mode='lines',
                name='Temperature',
                line=dict(color='orange', width=2)
            ))
        elif plot_type == "Scatter":
            fig.add_trace(go.Scatter(
                x=t, y=temperature,
                mode='markers',
                name='Temperature',
                marker=dict(color='orange', size=6)
            ))
        elif plot_type == "Line + Markers":
            fig.add_trace(go.Scatter(
                x=t, y=temperature,
                mode='lines+markers',
                name='Temperature',
                line=dict(color='orange', width=2),
                marker=dict(size=4)
            ))
        elif plot_type == "Area Fill":
            fig.add_trace(go.Scatter(
                x=t, y=temperature,
                mode='lines',
                name='Temperature',
                line=dict(color='orange', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 165, 0, 0.3)'
            ))

        fig.update_layout(
            title=f"Temperature Over Time ({plot_type})",
            xaxis_title="Time (hours)",
            yaxis_title="Temperature (°C)",
            height=450,
            hovermode='x unified'
        )

        if add_annotations:
            max_idx = np.argmax(temperature)
            min_idx = np.argmin(temperature)
            fig.add_annotation(
                x=t[max_idx], y=temperature[max_idx],
                text=f"Peak: {temperature[max_idx]:.1f}°C",
                showarrow=True, arrowhead=2
            )
            fig.add_annotation(
                x=t[min_idx], y=temperature[min_idx],
                text=f"Low: {temperature[min_idx]:.1f}°C",
                showarrow=True, arrowhead=2
            )

    elif plot_type == "Multi-axis":
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=t, y=temperature, name="Temperature",
                      line=dict(color='orange', width=2)),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(x=t, y=battery_soc, name="Battery SoC",
                      line=dict(color='green', width=2)),
            secondary_y=True
        )

        fig.update_xaxes(title_text="Time (hours)")
        fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False)
        fig.update_yaxes(title_text="Battery SoC (%)", secondary_y=True)
        fig.update_layout(title="Multi-Axis Time Series", height=450)

    st.plotly_chart(fig, use_container_width=True)

    # Comparison table
    st.markdown("### 📋 Plot Type Guide")

    guide_df = pd.DataFrame({
        'Plot Type': ['Line', 'Scatter', 'Line + Markers', 'Area Fill', 'Multi-axis'],
        'Best For': [
            'Continuous trends',
            'Discrete samples',
            'Moderate density data',
            'Showing magnitude',
            'Comparing different units'
        ],
        'Pros': [
            'Clear trends',
            'Individual points visible',
            'Best of both worlds',
            'Emphasizes volume',
            'Different scales together'
        ],
        'Cons': [
            'Hides individual points',
            'Hard to see trends',
            'Can be cluttered',
            'Can obscure details',
            'More complex to read'
        ]
    })

    st.dataframe(guide_df, use_container_width=True, hide_index=True)

    st.info("""
    **📚 Time Series Best Practices:**
    - **Line plots**: Best for showing trends over time
    - **Scatter plots**: Use when individual data points matter
    - **Markers**: Help identify sample times in sparse data
    - **Area fills**: Good for emphasizing magnitude or volume
    - **Multi-axis**: When comparing variables with different scales
    - **Annotations**: Highlight important events or values
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: DISTRIBUTION VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Distribution Visualization")

st.markdown("""
Distribution plots reveal the **statistical character** of data: central tendency,
spread, skewness, and outliers.
""")

col1, col2 = st.columns(2)

with col1:
    num_samples_exp2 = st.slider("Sample size", 100, 1000, 500, 100, key="exp2_samples")

with col2:
    dist_type = st.selectbox(
        "Distribution plot type",
        ["Histogram", "Box Plot", "Violin Plot", "Combined"],
        key="exp2_dist"
    )

if st.button("📊 Plot Distribution", type="primary", key="exp2_run"):
    # Generate sample data (temperature readings)
    data = np.random.normal(25, 5, num_samples_exp2)

    # Add some outliers
    num_outliers = int(num_samples_exp2 * 0.05)
    outlier_indices = np.random.choice(num_samples_exp2, num_outliers, replace=False)
    data[outlier_indices] += np.random.choice([-1, 1], num_outliers) * np.random.uniform(15, 25, num_outliers)

    if dist_type == "Histogram":
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=40,
            name='Temperature Distribution',
            marker_color='steelblue',
            opacity=0.75
        ))

        # Add normal distribution overlay
        mean_val = np.mean(data)
        std_val = np.std(data)
        x_range = np.linspace(data.min(), data.max(), 100)
        normal_curve = (num_samples_exp2 * (data.max() - data.min()) / 40) * \
                      (1 / (std_val * np.sqrt(2 * np.pi))) * \
                      np.exp(-0.5 * ((x_range - mean_val) / std_val) ** 2)

        fig.add_trace(go.Scatter(
            x=x_range,
            y=normal_curve,
            mode='lines',
            name='Normal Fit',
            line=dict(color='red', width=2)
        ))

        fig.update_layout(
            title="Temperature Distribution Histogram",
            xaxis_title="Temperature (°C)",
            yaxis_title="Frequency",
            height=450
        )

    elif dist_type == "Box Plot":
        fig = go.Figure()

        fig.add_trace(go.Box(
            y=data,
            name='Temperature',
            marker_color='steelblue',
            boxmean='sd'  # Show mean and std dev
        ))

        fig.update_layout(
            title="Temperature Box Plot",
            yaxis_title="Temperature (°C)",
            height=450
        )

    elif dist_type == "Violin Plot":
        fig = go.Figure()

        fig.add_trace(go.Violin(
            y=data,
            name='Temperature',
            box_visible=True,
            meanline_visible=True,
            fillcolor='steelblue',
            opacity=0.6
        ))

        fig.update_layout(
            title="Temperature Violin Plot",
            yaxis_title="Temperature (°C)",
            height=450
        )

    elif dist_type == "Combined":
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=("Histogram", "Box Plot", "Violin Plot")
        )

        # Histogram
        fig.add_trace(go.Histogram(
            x=data, nbinsx=30, marker_color='steelblue', opacity=0.75, showlegend=False
        ), row=1, col=1)

        # Box plot
        fig.add_trace(go.Box(
            y=data, marker_color='steelblue', showlegend=False
        ), row=1, col=2)

        # Violin plot
        fig.add_trace(go.Violin(
            y=data, fillcolor='steelblue', opacity=0.6, showlegend=False
        ), row=1, col=3)

        fig.update_xaxes(title_text="Temperature (°C)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_yaxes(title_text="Temperature (°C)", row=1, col=2)
        fig.update_yaxes(title_text="Temperature (°C)", row=1, col=3)

        fig.update_layout(height=450, title="Distribution Comparison")

    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Mean", f"{np.mean(data):.2f}°C")

    with col2:
        st.metric("Std Dev", f"{np.std(data):.2f}°C")

    with col3:
        st.metric("Median", f"{np.median(data):.2f}°C")

    with col4:
        q75, q25 = np.percentile(data, [75, 25])
        iqr = q75 - q25
        st.metric("IQR", f"{iqr:.2f}°C")

    st.info("""
    **📚 Distribution Plot Uses:**
    - **Histogram**: Shows frequency distribution, good for understanding data shape
    - **Box Plot**: Highlights median, quartiles, and outliers compactly
    - **Violin Plot**: Combines box plot with kernel density estimation
    - **Compare all three**: Each reveals different aspects of the data
    - **Use for**: Quality checks, understanding sensor characteristics, detecting drift
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: CORRELATION AND MULTI-VARIABLE PLOTS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Correlation Visualization")

st.markdown("""
Correlation plots reveal **relationships between variables**. This is critical for
understanding sensor interactions and system behavior.
""")

col1, col2 = st.columns(2)

with col1:
    num_points_exp3 = st.slider("Number of observations", 50, 300, 150, 50, key="exp3_points")

with col2:
    correlation_strength = st.slider("Correlation strength", 0.0, 1.0, 0.7, 0.1, key="exp3_corr")

if st.button("📊 Visualize Correlation", type="primary", key="exp3_run"):
    # Generate correlated data
    # Battery temp and CPU temp should be correlated
    battery_temp = np.random.normal(25, 5, num_points_exp3)
    # Create correlation
    cpu_temp = battery_temp * correlation_strength + np.random.normal(0, 5 * (1 - correlation_strength), num_points_exp3)

    # Additional uncorrelated variable
    solar_voltage = np.random.uniform(12, 18, num_points_exp3)

    # Scatter plot matrix
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Battery vs CPU Temp", "Battery Temp vs Solar V",
                       "CPU Temp vs Solar V", "Correlation Heatmap"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "heatmap"}]]
    )

    # Battery vs CPU
    fig.add_trace(go.Scatter(
        x=battery_temp, y=cpu_temp,
        mode='markers',
        name='Battery-CPU',
        marker=dict(color='steelblue', size=6, opacity=0.6)
    ), row=1, col=1)

    # Battery vs Solar
    fig.add_trace(go.Scatter(
        x=battery_temp, y=solar_voltage,
        mode='markers',
        name='Battery-Solar',
        marker=dict(color='green', size=6, opacity=0.6)
    ), row=1, col=2)

    # CPU vs Solar
    fig.add_trace(go.Scatter(
        x=cpu_temp, y=solar_voltage,
        mode='markers',
        name='CPU-Solar',
        marker=dict(color='orange', size=6, opacity=0.6)
    ), row=2, col=1)

    # Correlation heatmap
    df_corr = pd.DataFrame({
        'Battery Temp': battery_temp,
        'CPU Temp': cpu_temp,
        'Solar Voltage': solar_voltage
    })
    corr_matrix = df_corr.corr()

    fig.add_trace(go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        showscale=True
    ), row=2, col=2)

    fig.update_xaxes(title_text="Battery Temp (°C)", row=1, col=1)
    fig.update_yaxes(title_text="CPU Temp (°C)", row=1, col=1)
    fig.update_xaxes(title_text="Battery Temp (°C)", row=1, col=2)
    fig.update_yaxes(title_text="Solar Voltage (V)", row=1, col=2)
    fig.update_xaxes(title_text="CPU Temp (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Solar Voltage (V)", row=2, col=1)

    fig.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Correlation statistics
    st.markdown("### 📊 Correlation Coefficients")

    col1, col2, col3 = st.columns(3)

    with col1:
        corr_battery_cpu = np.corrcoef(battery_temp, cpu_temp)[0, 1]
        st.metric("Battery-CPU", f"{corr_battery_cpu:.3f}",
                 help="Strong correlation: temps rise together")

    with col2:
        corr_battery_solar = np.corrcoef(battery_temp, solar_voltage)[0, 1]
        st.metric("Battery-Solar", f"{corr_battery_solar:.3f}",
                 help="Weak/no correlation: independent")

    with col3:
        corr_cpu_solar = np.corrcoef(cpu_temp, solar_voltage)[0, 1]
        st.metric("CPU-Solar", f"{corr_cpu_solar:.3f}",
                 help="Weak/no correlation: independent")

    st.info("""
    **📚 Correlation Interpretation:**
    - **+1.0**: Perfect positive correlation
    - **+0.7 to +1.0**: Strong positive correlation
    - **+0.3 to +0.7**: Moderate positive correlation
    - **-0.3 to +0.3**: Weak/no correlation
    - **-0.7 to -0.3**: Moderate negative correlation
    - **-1.0 to -0.7**: Strong negative correlation
    - **-1.0**: Perfect negative correlation

    **Use cases**: Finding sensor relationships, detecting anomalies through
    correlation breaks, understanding system dynamics
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: DASHBOARD DESIGN
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Mission Monitoring Dashboard")

st.markdown("""
Dashboards integrate multiple visualizations into a **unified monitoring interface**.
Let's design a mission control dashboard for real-time monitoring.
""")

if st.button("🎛️ Launch Dashboard", type="primary", key="exp4_run"):
    # Generate current mission data
    current_time = 12.5  # hours into mission
    t_history = np.linspace(current_time - 2, current_time, 50)  # Last 2 hours

    # Generate data streams
    battery_soc = 85 - 10 * (t_history / 24) + np.random.normal(0, 0.5, 50)
    temperature = 20 + 10 * np.sin(2 * np.pi * t_history / 24) + np.random.normal(0, 1, 50)
    cpu_load = 45 + 15 * np.sin(2 * np.pi * t_history / 3) + np.random.normal(0, 3, 50)

    st.markdown("### 🎛️ Mission Control Dashboard")

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Battery SoC",
            f"{battery_soc[-1]:.1f}%",
            delta=f"{battery_soc[-1] - battery_soc[-10]:.1f}%",
            help="State of Charge"
        )

    with col2:
        st.metric(
            "CPU Temperature",
            f"{temperature[-1]:.1f}°C",
            delta=f"{temperature[-1] - temperature[-10]:.1f}°C"
        )

    with col3:
        st.metric(
            "CPU Load",
            f"{cpu_load[-1]:.0f}%",
            delta=f"{cpu_load[-1] - cpu_load[-10]:.0f}%"
        )

    with col4:
        mission_hours = int(current_time)
        mission_mins = int((current_time - mission_hours) * 60)
        st.metric(
            "Mission Time",
            f"{mission_hours}h {mission_mins}m",
            help="Elapsed time since landing"
        )

    # Main plot area
    st.markdown("#### 📈 Real-Time Telemetry")

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Battery State of Charge", "CPU Temperature", "CPU Load"),
        vertical_spacing=0.08,
        row_heights=[0.33, 0.33, 0.33]
    )

    # Battery SoC
    fig.add_trace(go.Scatter(
        x=t_history, y=battery_soc,
        mode='lines+markers',
        name='Battery SoC',
        line=dict(color='green', width=2),
        marker=dict(size=4),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)'
    ), row=1, col=1)

    fig.add_hline(y=20, line_dash="dash", line_color="red",
                 annotation_text="Low Battery", row=1, col=1)

    # Temperature
    fig.add_trace(go.Scatter(
        x=t_history, y=temperature,
        mode='lines+markers',
        name='CPU Temp',
        line=dict(color='orange', width=2),
        marker=dict(size=4)
    ), row=2, col=1)

    fig.add_hline(y=50, line_dash="dash", line_color="red",
                 annotation_text="High Temp", row=2, col=1)

    # CPU Load
    fig.add_trace(go.Scatter(
        x=t_history, y=cpu_load,
        mode='lines+markers',
        name='CPU Load',
        line=dict(color='steelblue', width=2),
        marker=dict(size=4)
    ), row=3, col=1)

    fig.add_hline(y=85, line_dash="dash", line_color="red",
                 annotation_text="High Load", row=3, col=1)

    fig.update_xaxes(title_text="Mission Time (hours)", row=3, col=1)
    fig.update_yaxes(title_text="SoC (%)", row=1, col=1)
    fig.update_yaxes(title_text="Temp (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Load (%)", row=3, col=1)

    fig.update_layout(height=750, showlegend=False, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    # Status indicators
    st.markdown("#### 🚦 System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        battery_status = "🟢 Normal" if battery_soc[-1] > 30 else "🟡 Low" if battery_soc[-1] > 20 else "🔴 Critical"
        st.markdown(f"**Power System**: {battery_status}")

    with col2:
        temp_status = "🟢 Normal" if temperature[-1] < 40 else "🟡 Warm" if temperature[-1] < 50 else "🔴 Hot"
        st.markdown(f"**Thermal**: {temp_status}")

    with col3:
        load_status = "🟢 Normal" if cpu_load[-1] < 70 else "🟡 High" if cpu_load[-1] < 85 else "🔴 Critical"
        st.markdown(f"**Computing**: {load_status}")

    st.success("""
    **✅ Dashboard Design Best Practices:**
    - **Top-level metrics**: Most important values at a glance
    - **Trends over time**: Show recent history for context
    - **Color coding**: Green/yellow/red for status
    - **Threshold lines**: Visualize operational limits
    - **Delta indicators**: Show direction of change
    - **Update frequency**: Balance detail vs responsiveness
    - **Clean layout**: Avoid clutter, prioritize readability
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Appendix E Complete!**

You've learned:
- ✅ Time series visualization techniques (line, scatter, area, multi-axis)
- ✅ Distribution plots (histograms, box plots, violin plots)
- ✅ Correlation visualization and interpretation
- ✅ Dashboard design principles for mission monitoring
- ✅ When to use each visualization type
- ✅ Best practices for effective telemetry displays

**Connection to Mission**: Visualization is how mission operators understand telemetry.
Well-designed visualizations enable rapid situation assessment, anomaly detection,
and informed decision-making. Understanding visualization techniques ensures that
critical information is communicated clearly and effectively.

**🎉 Congratulations!** You've completed all five appendices covering the complete
Meridian-3 telemetry pipeline from sensor data generation through visualization.
""")

st.markdown("*You can now navigate back to any chapter or appendix to review specific topics.*")
