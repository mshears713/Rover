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

ARCHITECTURE:
    Time management connects all subsystems:
    - Environment uses LST to determine day/night
    - Sensors use time for drift accumulation
    - Power system tracks solar angle
    - Storage uses timestamps for indexing

TEACHING APPROACH:
    - Interactive time converters
    - Solar angle visualization
    - Diurnal cycle simulation
    - Power prediction from orbital position

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 33.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

st.set_page_config(page_title="Time and Orbits", page_icon="🌅", layout="wide")

st.title("🌅 Chapter 2: Time and Orbits")

st.markdown("""
## Understanding Martian Time

The rover operates on **Mars time**, not Earth time. Understanding the local
solar environment is critical for power management and mission planning.

A Martian day (called a **sol**) is 24 hours, 39 minutes, 35 seconds —
about 2.7% longer than an Earth day.
""")

# ═══════════════════════════════════════════════════════════════════════════
# TIME SYSTEMS OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("⏰ Time Systems Explained", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │              MERIDIAN-3 TIME COORDINATE SYSTEMS              │
    └──────────────────────────────────────────────────────────────┘

    Mission Elapsed Time (MET)
    ┌─────────────────────────────────────────────────────┐
    │  0s  →  88,775s  →  177,550s  →  266,325s  → ...   │
    │  Landing   Sol 1       Sol 2       Sol 3            │
    └─────────────────────────────────────────────────────┘
          ↓ Convert to Sol Number
    ┌─────────────────────────────────────────────────────┐
    │  Sol 0   │   Sol 1   │   Sol 2   │   Sol 3   │ ... │
    └─────────────────────────────────────────────────────┘
          ↓ Convert to Local Solar Time (LST)
    ┌───────────────────────────────────┐
    │  🌑 Midnight → 🌅 Dawn → ☀️ Noon  │
    │  → 🌇 Dusk → 🌑 Midnight          │
    │                                   │
    │  0s     22,194s   44,387s         │
    │         (sunrise) (noon)          │
    └───────────────────────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Mission Elapsed Time (MET)**
        - **What**: Seconds since landing
        - **Range**: 0 to infinity
        - **Use**: Logging, timestamping
        - **Monotonic**: Never goes backward
        - **Example**: MET = 250,000s
        """)

    with col2:
        st.markdown("""
        **Sol Number**
        - **What**: Martian days since landing
        - **Range**: Sol 0, Sol 1, Sol 2...
        - **Use**: Mission planning
        - **Discrete**: Integer counter
        - **Example**: Sol 2
        """)

    with col3:
        st.markdown("""
        **Local Solar Time (LST)**
        - **What**: Time of day on Mars
        - **Range**: 0 to 88,775 seconds
        - **Use**: Solar angle, power
        - **Cyclic**: Resets each sol
        - **Example**: 12:00 (noon)
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE TIME CONVERTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🕐 Interactive Time Converter")

st.markdown("""
Enter a mission elapsed time to see it converted to sol number and local solar time.
""")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from utils.timing import (
        MARS_SOL_SECONDS,
        mission_time_to_sol,
        mission_time_to_local_time,
        local_time_to_hms,
        calculate_solar_elevation
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        met_input = st.number_input(
            "Mission Elapsed Time (seconds)",
            min_value=0,
            max_value=10000000,
            value=177550,
            step=1000,
            help="Seconds since landing on Mars"
        )

    with col2:
        # Quick presets
        st.markdown("**Quick Presets:**")
        preset_col1, preset_col2 = st.columns(2)
        with preset_col1:
            if st.button("Landing (0s)"):
                met_input = 0
            if st.button("Sol 5"):
                met_input = int(5 * MARS_SOL_SECONDS)
        with preset_col2:
            if st.button("Sol 1"):
                met_input = int(MARS_SOL_SECONDS)
            if st.button("Sol 10"):
                met_input = int(10 * MARS_SOL_SECONDS)

    # Convert time
    sol_number = mission_time_to_sol(met_input)
    lst_seconds = mission_time_to_local_time(met_input)
    hours, minutes, seconds = local_time_to_hms(lst_seconds)
    solar_elevation = calculate_solar_elevation(lst_seconds)

    # Display conversions
    st.markdown("### ⏱️ Time Breakdown")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Mission Elapsed Time",
            f"{met_input:,}s",
            help="Total seconds since landing"
        )

    with col2:
        st.metric(
            "Sol Number",
            f"Sol {sol_number}",
            help="Martian days since landing"
        )

    with col3:
        st.metric(
            "Local Solar Time",
            f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            help="Time of day on Mars (HH:MM:SS)"
        )

    with col4:
        # Determine time of day
        if solar_elevation < 0:
            time_of_day = "Night"
            icon = "🌑"
        elif solar_elevation < 10:
            time_of_day = "Dawn/Dusk"
            icon = "🌅"
        elif solar_elevation < 45:
            time_of_day = "Morning/Evening"
            icon = "🌤️"
        else:
            time_of_day = "Midday"
            icon = "☀️"

        st.metric(
            "Time of Day",
            f"{icon} {time_of_day}",
            delta=f"{solar_elevation:.1f}° elevation"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # SOLAR ANGLE AND POWER PREDICTION
    # ═══════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.markdown("## ☀️ Solar Angle and Power Prediction")

    st.markdown(f"""
    At **{hours:02d}:{minutes:02d}** local solar time, the sun is at
    **{solar_elevation:.1f}°** elevation above the horizon.
    """)

    # Calculate power based on solar angle
    # Power = max_power * sin(elevation) when elevation > 0
    max_power = 100.0  # Watts
    if solar_elevation > 0:
        power_available = max_power * math.sin(math.radians(solar_elevation))
    else:
        power_available = 0.0

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Solar Elevation",
            f"{solar_elevation:.1f}°",
            help="Angle of sun above horizon"
        )
        st.metric(
            "Available Solar Power",
            f"{power_available:.1f} W",
            delta=f"{(power_available/max_power)*100:.0f}% of max" if power_available > 0 else "Night mode"
        )

    with col2:
        # Show power level gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=power_available,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Solar Power"},
            delta={'reference': max_power},
            gauge={
                'axis': {'range': [None, max_power]},
                'bar': {'color': "orange"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "lightyellow"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "gold"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20  # Minimum operating power
                }
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════
    # DIURNAL CYCLE SIMULATION
    # ═══════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.markdown("## 🌍 Full Diurnal Cycle Simulation")

    st.markdown("""
    Visualize how solar angle and power availability change over a complete Martian day.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        num_sols_to_plot = st.slider(
            "Number of sols to simulate",
            min_value=1,
            max_value=5,
            value=2,
            help="Plot multiple sols to see the daily pattern"
        )

    with col2:
        show_power_only = st.checkbox("Show power curve only", value=False)

    # Generate data for full diurnal cycle
    time_points = np.linspace(0, num_sols_to_plot * MARS_SOL_SECONDS, num_sols_to_plot * 100)
    solar_angles = []
    power_values = []
    lst_values = []

    for t in time_points:
        lst = mission_time_to_local_time(t)
        elevation = calculate_solar_elevation(lst)
        power = max_power * math.sin(math.radians(elevation)) if elevation > 0 else 0.0

        solar_angles.append(elevation)
        power_values.append(power)
        lst_values.append(lst)

    # Convert time to hours for x-axis
    time_hours = time_points / 3600.0

    # Create plot
    if show_power_only:
        fig_cycle = go.Figure()
        fig_cycle.add_trace(go.Scatter(
            x=time_hours,
            y=power_values,
            name='Solar Power',
            line=dict(color='orange', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 165, 0, 0.2)'
        ))
        fig_cycle.update_yaxes(title="Power (W)", range=[0, max_power * 1.1])
        fig_cycle.update_layout(title="Solar Power Availability Over Time")
    else:
        # Dual-axis plot
        fig_cycle = make_subplots(specs=[[{"secondary_y": True}]])

        fig_cycle.add_trace(
            go.Scatter(x=time_hours, y=solar_angles, name='Solar Elevation',
                      line=dict(color='steelblue', width=2)),
            secondary_y=False
        )

        fig_cycle.add_trace(
            go.Scatter(x=time_hours, y=power_values, name='Available Power',
                      line=dict(color='orange', width=3),
                      fill='tozeroy', fillcolor='rgba(255, 165, 0, 0.2)'),
            secondary_y=True
        )

        fig_cycle.update_yaxes(title_text="Solar Elevation (°)", secondary_y=False)
        fig_cycle.update_yaxes(title_text="Power (W)", range=[0, max_power * 1.1], secondary_y=True)
        fig_cycle.update_layout(title="Diurnal Cycle: Solar Angle and Power")

    fig_cycle.update_xaxes(title="Mission Time (hours)")
    fig_cycle.update_layout(height=400, hovermode='x unified')

    # Add day/night shading
    for sol in range(num_sols_to_plot):
        # Night regions (roughly 18:00 to 06:00 LST)
        night_start = sol * (MARS_SOL_SECONDS / 3600) + 18
        night_end = (sol + 1) * (MARS_SOL_SECONDS / 3600) + 6

        fig_cycle.add_vrect(
            x0=night_start, x1=night_end if sol < num_sols_to_plot - 1 else night_start + 12,
            fillcolor="lightblue", opacity=0.1,
            layer="below", line_width=0,
        )

    st.plotly_chart(fig_cycle, use_container_width=True)

    # Summary statistics
    st.markdown("### 📊 Daily Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        daylight_hours = sum(1 for e in solar_angles if e > 0) / (100 / num_sols_to_plot)
        st.metric("Daylight Hours", f"{daylight_hours:.1f} hrs/sol")

    with col2:
        avg_power_daylight = np.mean([p for p in power_values if p > 0])
        st.metric("Avg Power (day)", f"{avg_power_daylight:.1f} W")

    with col3:
        total_energy_per_sol = sum(power_values) / (100 / num_sols_to_plot) * 3600 / 1000  # kWh
        st.metric("Energy/Sol", f"{total_energy_per_sol:.2f} kWh")

    with col4:
        max_observed = max(solar_angles)
        st.metric("Peak Elevation", f"{max_observed:.1f}°")

    st.info("""
    **📚 Key Observations:**
    - Solar power is only available during daylight (roughly 12 hours per sol)
    - Power peaks at local noon when the sun is highest
    - The rover must store enough energy during the day to survive the night
    - Seasonal and latitude variations affect peak solar elevation
    """)

    # ═══════════════════════════════════════════════════════════════════════
    # SUNRISE/SUNSET CALCULATOR
    # ═══════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.markdown("## 🌅 Sunrise/Sunset Calculator")

    st.markdown("""
    Calculate sunrise and sunset times for mission planning.
    """)

    # For simplicity, approximate sunrise/sunset as when solar elevation = 0
    # In reality, there's atmospheric refraction, but we'll use the simple model
    sunrise_lst = MARS_SOL_SECONDS / 4  # Roughly 06:00 LST
    sunset_lst = 3 * MARS_SOL_SECONDS / 4  # Roughly 18:00 LST

    sunrise_h, sunrise_m, sunrise_s = local_time_to_hms(sunrise_lst)
    sunset_h, sunset_m, sunset_s = local_time_to_hms(sunset_lst)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        **🌅 Sunrise**
        - Local Time: {sunrise_h:02d}:{sunrise_m:02d}:{sunrise_s:02d}
        - LST: {sunrise_lst:.0f}s
        - Solar panels begin charging
        """)

    with col2:
        st.markdown(f"""
        **☀️ Solar Noon**
        - Local Time: 12:00:00
        - LST: {MARS_SOL_SECONDS/2:.0f}s
        - Maximum power available
        """)

    with col3:
        st.markdown(f"""
        **🌇 Sunset**
        - Local Time: {sunset_h:02d}:{sunset_m:02d}:{sunset_s:02d}
        - LST: {sunset_lst:.0f}s
        - Battery mode begins
        """)

except ImportError as e:
    st.error(f"""
    ⚠️ **Timing utilities not found**

    Make sure Phase 2 is complete and timing.py is implemented.

    Error: {str(e)}
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Chapter 2 Complete!**

You've learned:
- ✅ Martian time systems (MET, Sol, LST)
- ✅ Time conversion between coordinate systems
- ✅ Solar elevation calculation
- ✅ Diurnal cycle and power availability
- ✅ Sunrise/sunset prediction

**Next Steps**: Proceed to Chapter 3 to learn about sensor noise, drift,
and component wear over time.
""")

st.markdown("*Navigate to Chapter 3: Noise and Wear in the sidebar →*")
