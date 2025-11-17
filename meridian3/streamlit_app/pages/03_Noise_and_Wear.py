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

ARCHITECTURE:
    Noise is added at the sensor layer, mimicking real hardware:
    - Gaussian noise: Random fluctuations around true value
    - Drift: Slow bias accumulation over time
    - Quantization: ADC resolution limits
    - Temperature effects: Noise scales with thermal state

TEACHING APPROACH:
    - Interactive noise distribution visualization
    - Drift accumulation simulator
    - SNR calculator with real-time examples
    - Combined noise source analysis

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 34.
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

st.set_page_config(page_title="Noise and Wear", page_icon="📉", layout="wide")

st.title("📉 Chapter 3: Noise and Wear")

st.markdown("""
## Imperfect Measurements in a Perfect Simulation

Real sensors lie. Not maliciously - they simply cannot be perfect.
Understanding sensor imperfections is the key to robust telemetry systems.

Every sensor has multiple error sources that corrupt the true signal. This
chapter explores these error modes and teaches you to recognize them in data.
""")

# ═══════════════════════════════════════════════════════════════════════════
# NOISE TYPES OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Sensor Error Types Overview", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │                  SENSOR ERROR TAXONOMY                       │
    └──────────────────────────────────────────────────────────────┘

         True Value: 25.0°C
              │
              ├─→ [Random Noise] → 25.3°C, 24.8°C, 25.1°C...
              │    • Gaussian distribution
              │    • Zero mean (unbiased)
              │    • Reduces with averaging
              │
              ├─→ [Systematic Bias] → Always reads +0.5°C high
              │    • Constant offset
              │    • Fixed by calibration
              │    • Doesn't average out
              │
              ├─→ [Drift] → Bias changes over time
              │    • 0.01°C/hour increase
              │    • Cumulative effect
              │    • Requires recalibration
              │
              ├─→ [Quantization] → 24.9°C, 25.0°C, 25.1°C only
              │    • Limited ADC resolution
              │    • Stair-step pattern
              │    • Cannot be removed
              │
              └─→ [Temperature Effect] → Noise increases at extremes
                   • Multiplicative error
                   • Environment-dependent
                   • Predictable pattern
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Random Noise**
        - Source: Electronic thermal noise
        - Distribution: Gaussian (normal)
        - Typical: ±0.1° to ±0.5° (1-sigma)
        - Mitigation: Averaging, filtering
        """)

    with col2:
        st.markdown("""
        **Drift**
        - Source: Component aging, temperature
        - Rate: 0.01°/hour typical
        - Cumulative: Yes
        - Mitigation: Periodic calibration
        """)

    with col3:
        st.markdown("""
        **Quantization**
        - Source: ADC bit depth
        - Level: 2^N discrete values
        - 12-bit ADC: ~0.01° steps
        - Mitigation: None (fundamental)
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: GAUSSIAN NOISE VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Gaussian Noise Visualization")

st.markdown("""
Most sensor noise follows a **Gaussian (normal) distribution**. Let's explore
this by taking many measurements of a constant value and analyzing the results.
""")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    noise_samples = st.slider("Number of samples", 100, 5000, 1000, step=100,
                             help="More samples give better statistical clarity")

with col2:
    noise_sigma = st.slider("Noise σ (std dev)", 0.1, 2.0, 0.5, step=0.1,
                           help="Standard deviation of Gaussian noise")

with col3:
    true_value = st.number_input("True value", value=25.0, step=0.5,
                                help="The actual (unknown) value being measured")

if st.button("🔬 Generate Noisy Measurements", type="primary", key="noise_exp1"):
    # Generate noisy measurements
    measurements = np.random.normal(true_value, noise_sigma, noise_samples)

    # Calculate statistics
    measured_mean = np.mean(measurements)
    measured_std = np.std(measurements)

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("True Value", f"{true_value:.2f}", help="The actual value (unknown in real sensors)")

    with col2:
        error = measured_mean - true_value
        st.metric("Measured Mean", f"{measured_mean:.2f}",
                 delta=f"Error: {error:.2f}",
                 help="Average of all measurements")

    with col3:
        st.metric("Measured σ", f"{measured_std:.2f}",
                 delta=f"Expected: {noise_sigma:.2f}",
                 help="Standard deviation of measurements")

    with col4:
        # Calculate what percentage are within 1 sigma
        within_1sigma = np.sum(np.abs(measurements - measured_mean) <= measured_std) / noise_samples * 100
        st.metric("Within 1σ", f"{within_1sigma:.1f}%",
                 delta="Expected: 68.3%",
                 help="Should be ~68% for Gaussian")

    # Create visualization
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Measurement Time Series", "Histogram (Distribution)"),
        horizontal_spacing=0.12
    )

    # Time series
    fig.add_trace(
        go.Scatter(x=list(range(noise_samples)), y=measurements,
                  mode='markers', marker=dict(size=3, color='steelblue', opacity=0.6),
                  name='Measurements'),
        row=1, col=1
    )
    fig.add_hline(y=true_value, line_dash="dash", line_color="red",
                 annotation_text="True Value", row=1, col=1)
    fig.add_hline(y=measured_mean, line_dash="dot", line_color="green",
                 annotation_text="Measured Mean", row=1, col=1)

    # Histogram
    fig.add_trace(
        go.Histogram(x=measurements, nbinsx=50, name='Distribution',
                    marker_color='steelblue', opacity=0.7),
        row=1, col=2
    )

    # Add Gaussian overlay
    x_range = np.linspace(measurements.min(), measurements.max(), 200)
    gaussian = (noise_samples * (measurements.max() - measurements.min()) / 50) * \
               (1 / (noise_sigma * np.sqrt(2 * np.pi))) * \
               np.exp(-0.5 * ((x_range - measured_mean) / noise_sigma) ** 2)
    fig.add_trace(
        go.Scatter(x=x_range, y=gaussian, mode='lines',
                  line=dict(color='red', width=2), name='Theoretical Gaussian'),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Sample Number", row=1, col=1)
    fig.update_xaxes(title_text="Value", row=1, col=2)
    fig.update_yaxes(title_text="Measured Value", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)

    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.info("""
    **📚 Key Observations:**
    - Individual measurements are **scattered** around the true value
    - The **mean** of many measurements approaches the true value (unbiased)
    - The distribution is **bell-shaped** (Gaussian/normal)
    - About **68%** of measurements fall within ±1σ of the mean
    - About **95%** fall within ±2σ, and **99.7%** within ±3σ
    - This is the **central limit theorem** in action!
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: DRIFT ACCUMULATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Sensor Drift Over Time")

st.markdown("""
Unlike random noise, **drift** is a systematic error that accumulates over time.
Drift can be caused by component aging, temperature changes, or radiation damage.
""")

col1, col2, col3 = st.columns(3)

with col1:
    drift_duration = st.slider("Mission duration (hours)", 1, 100, 24, step=1,
                              help="How long to simulate drift")

with col2:
    drift_rate = st.slider("Drift rate (°/hour)", 0.0, 0.5, 0.05, step=0.01,
                          help="How fast the sensor drifts")

with col3:
    drift_noise = st.slider("Additional noise σ", 0.0, 1.0, 0.2, step=0.05,
                           help="Random noise on top of drift")

if st.button("🔬 Simulate Drift", type="primary", key="drift_exp2"):
    # Generate time series with drift
    time_points = 1000
    time_hours = np.linspace(0, drift_duration, time_points)

    # True value remains constant
    true_signal = np.ones(time_points) * 25.0

    # Drift accumulates linearly
    drift_component = drift_rate * time_hours

    # Random noise added
    noise_component = np.random.normal(0, drift_noise, time_points)

    # Measured value = true + drift + noise
    measured_signal = true_signal + drift_component + noise_component

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Initial Reading", f"{measured_signal[0]:.2f}°",
                 help="First measurement")

    with col2:
        st.metric("Final Reading", f"{measured_signal[-1]:.2f}°",
                 delta=f"+{measured_signal[-1] - measured_signal[0]:.2f}°",
                 help="Last measurement")

    with col3:
        total_drift = drift_rate * drift_duration
        st.metric("Total Drift", f"{total_drift:.2f}°",
                 help="Accumulated drift over mission")

    with col4:
        # When would drift exceed 3-sigma of noise?
        if drift_noise > 0:
            time_to_exceed = (3 * drift_noise) / drift_rate if drift_rate > 0 else float('inf')
            st.metric("Drift > 3σ at", f"{time_to_exceed:.1f}h" if time_to_exceed < 1000 else "Never",
                     help="When drift becomes detectable above noise")

    # Visualization
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=time_hours, y=true_signal,
                            mode='lines', name='True Value',
                            line=dict(color='red', width=2, dash='dash')))

    fig.add_trace(go.Scatter(x=time_hours, y=measured_signal,
                            mode='lines', name='Measured (with drift + noise)',
                            line=dict(color='steelblue', width=1)))

    fig.add_trace(go.Scatter(x=time_hours, y=true_signal + drift_component,
                            mode='lines', name='True + Drift (no noise)',
                            line=dict(color='orange', width=1, dash='dot')))

    fig.update_layout(
        title="Sensor Drift Accumulation Over Mission",
        xaxis_title="Time (hours)",
        yaxis_title="Temperature (°C)",
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.warning("""
    **⚠️ Drift is Dangerous:**
    - Unlike noise, drift **doesn't average out** - it accumulates
    - Small drift rates (0.01°/hour) become large errors over days
    - Drift can **masquerade as real trends** in data
    - Regular **calibration** is the only mitigation
    - Uncalibrated sensors become unreliable over time
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: QUANTIZATION EFFECTS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Quantization and ADC Resolution")

st.markdown("""
Analog sensors are digitized by **Analog-to-Digital Converters (ADCs)** with
finite resolution. This creates a "stair-step" effect where continuous values
are rounded to discrete levels.
""")

col1, col2 = st.columns(2)

with col1:
    adc_bits = st.select_slider("ADC Resolution (bits)",
                                options=[8, 10, 12, 14, 16],
                                value=12,
                                help="Higher bits = finer resolution")

with col2:
    measurement_range = st.slider("Measurement Range (°C)", 10, 200, 100, step=10,
                                 help="Full-scale range of sensor")

# Calculate quantization level
num_levels = 2 ** adc_bits
quantization_step = measurement_range / num_levels

st.markdown(f"""
**Configuration:**
- ADC Resolution: **{adc_bits} bits** = **{num_levels:,} discrete levels**
- Measurement Range: **{measurement_range}°C**
- Quantization Step: **{quantization_step:.4f}°C**
""")

if st.button("🔬 Show Quantization Effect", type="primary", key="quant_exp3"):
    # Generate smooth signal
    time = np.linspace(0, 10, 1000)
    true_signal = 50 + 10 * np.sin(2 * np.pi * 0.3 * time)

    # Quantize the signal
    # Map to ADC levels (0 to num_levels-1)
    normalized = (true_signal / measurement_range) * num_levels
    quantized_levels = np.floor(normalized).astype(int)
    quantized_levels = np.clip(quantized_levels, 0, num_levels - 1)

    # Convert back to physical units
    quantized_signal = (quantized_levels / num_levels) * measurement_range

    # Quantization error
    quant_error = quantized_signal - true_signal

    # Visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Signal with Quantization", "Quantization Error"),
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4]
    )

    # Signal plot
    fig.add_trace(go.Scatter(x=time, y=true_signal,
                            mode='lines', name='True Signal',
                            line=dict(color='red', width=2)),
                 row=1, col=1)

    fig.add_trace(go.Scatter(x=time, y=quantized_signal,
                            mode='lines', name='Quantized Signal',
                            line=dict(color='steelblue', width=1)),
                 row=1, col=1)

    # Error plot
    fig.add_trace(go.Scatter(x=time, y=quant_error,
                            mode='lines', name='Error',
                            line=dict(color='orange', width=1),
                            fill='tozeroy'),
                 row=2, col=1)

    fig.update_xaxes(title_text="Time (s)", row=2, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Error (°C)", row=2, col=1)

    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Max Quant Error", f"{np.max(np.abs(quant_error)):.4f}°C")

    with col2:
        st.metric("RMS Error", f"{np.sqrt(np.mean(quant_error**2)):.4f}°C")

    with col3:
        st.metric("Quantization Step", f"{quantization_step:.4f}°C")

    with col4:
        st.metric("Effective SNR", f"{20 * np.log10(num_levels):.1f} dB")

    st.info("""
    **📚 Key Observations:**
    - Quantization creates a **stair-step** pattern in the signal
    - Maximum error is **half the quantization step**
    - Higher bit depth = finer steps = less error
    - 8-bit ADC: ~0.4°C steps | 12-bit: ~0.024°C | 16-bit: ~0.0015°C
    - Quantization error cannot be removed - it's a fundamental limit
    - For slow signals, quantization is visible; for noisy signals, it's hidden
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: SIGNAL-TO-NOISE RATIO (SNR)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Signal-to-Noise Ratio (SNR) Calculator")

st.markdown("""
**SNR** quantifies how much "real signal" versus "noise" you have. High SNR means
clean data; low SNR means the noise dominates.
""")

col1, col2 = st.columns(2)

with col1:
    signal_amplitude = st.slider("Signal Amplitude", 1.0, 50.0, 10.0, step=1.0,
                                help="Peak-to-peak swing of the real signal")

with col2:
    noise_level = st.slider("Noise Level (σ)", 0.1, 10.0, 1.0, step=0.1,
                           help="Standard deviation of noise")

# Calculate SNR
snr_linear = signal_amplitude / noise_level if noise_level > 0 else float('inf')
snr_db = 20 * np.log10(snr_linear) if snr_linear > 0 else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("SNR (linear)", f"{snr_linear:.2f}")

with col2:
    st.metric("SNR (dB)", f"{snr_db:.1f} dB")

with col3:
    quality = "Excellent" if snr_db > 40 else "Good" if snr_db > 20 else "Fair" if snr_db > 10 else "Poor"
    st.metric("Signal Quality", quality)

if st.button("🔬 Visualize SNR", type="primary", key="snr_exp4"):
    # Generate signal + noise
    time = np.linspace(0, 10, 1000)
    clean_signal = signal_amplitude * np.sin(2 * np.pi * 0.5 * time)
    noise = np.random.normal(0, noise_level, len(time))
    noisy_signal = clean_signal + noise

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(f"Clean Signal (Amplitude={signal_amplitude})",
                       f"Noisy Signal (SNR={snr_db:.1f} dB)"),
        vertical_spacing=0.15
    )

    fig.add_trace(go.Scatter(x=time, y=clean_signal,
                            mode='lines', name='Clean',
                            line=dict(color='green', width=2)),
                 row=1, col=1)

    fig.add_trace(go.Scatter(x=time, y=noisy_signal,
                            mode='lines', name='Noisy',
                            line=dict(color='steelblue', width=1)),
                 row=2, col=1)

    fig.update_xaxes(title_text="Time (s)", row=2, col=1)
    fig.update_yaxes(title_text="Signal", row=1, col=1)
    fig.update_yaxes(title_text="Signal + Noise", row=2, col=1)

    fig.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"""
    **SNR Interpretation:**
    - **> 40 dB**: Excellent - noise barely visible
    - **20-40 dB**: Good - signal clearly distinguishable
    - **10-20 dB**: Fair - signal visible but noisy
    - **< 10 dB**: Poor - noise dominates, filtering required

    Your current SNR: **{snr_db:.1f} dB** ({quality})
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 5: COMBINED NOISE SOURCES
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 5: Combined Noise Sources")

st.markdown("""
Real sensors have **all error sources simultaneously**: random noise, drift,
quantization, and temperature effects. Let's see them all together.
""")

col1, col2, col3 = st.columns(3)

with col1:
    enable_noise = st.checkbox("Random Noise", value=True)
    enable_drift = st.checkbox("Drift", value=True)

with col2:
    enable_quant = st.checkbox("Quantization", value=True)
    enable_temp = st.checkbox("Temperature Effect", value=False)

with col3:
    combined_duration = st.slider("Duration (hours)", 1, 48, 12, step=1,
                                 key="combined_dur")

if st.button("🔬 Show Combined Effects", type="primary", key="combined_exp5"):
    time_points = 500
    time_hours = np.linspace(0, combined_duration, time_points)

    # Start with true constant value
    true_value = 25.0
    signal = np.ones(time_points) * true_value

    # Add each error source
    if enable_noise:
        signal += np.random.normal(0, 0.3, time_points)

    if enable_drift:
        signal += 0.05 * time_hours

    if enable_quant:
        # Quantize to 12-bit resolution over 100°C range
        quant_step = 100 / 4096
        signal = np.round(signal / quant_step) * quant_step

    if enable_temp:
        # Simulate temperature-dependent noise increase
        temp_factor = 1 + 0.5 * np.sin(2 * np.pi * time_hours / 24)
        signal += np.random.normal(0, 0.2, time_points) * temp_factor

    # Plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=time_hours, y=np.ones(time_points) * true_value,
                            mode='lines', name='True Value',
                            line=dict(color='red', width=2, dash='dash')))

    fig.add_trace(go.Scatter(x=time_hours, y=signal,
                            mode='lines', name='Measured (all errors)',
                            line=dict(color='steelblue', width=1)))

    fig.update_layout(
        title="Combined Error Sources",
        xaxis_title="Time (hours)",
        yaxis_title="Temperature (°C)",
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    total_error = signal - true_value
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Mean Error", f"{np.mean(total_error):.3f}°C")

    with col2:
        st.metric("Std Dev", f"{np.std(total_error):.3f}°C")

    with col3:
        st.metric("Max Error", f"{np.max(np.abs(total_error)):.3f}°C")

    with col4:
        st.metric("RMS Error", f"{np.sqrt(np.mean(total_error**2)):.3f}°C")

    st.success("""
    **🎓 Understanding Combined Errors:**
    - Real sensors have **multiple simultaneous** error sources
    - Errors combine in complex ways (some add, some multiply)
    - **Total uncertainty** is greater than any single source
    - This is why sensor datasheets specify total error budgets
    - Good telemetry systems must account for **all** error modes
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Chapter 3 Complete!**

You've learned:
- ✅ Gaussian noise characteristics and distributions
- ✅ Sensor drift accumulation over time
- ✅ Quantization effects from ADC resolution
- ✅ Signal-to-noise ratio (SNR) concepts
- ✅ Combined error sources in real sensors
- ✅ Why calibration and filtering are essential

**Next Steps**: Proceed to Chapter 4 to learn about terrain effects and
environmental hazards that add another layer of complexity to telemetry.
""")

st.markdown("*Navigate to Chapter 4: Terrain and Hazards in the sidebar →*")
