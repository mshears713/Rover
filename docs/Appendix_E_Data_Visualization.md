# Appendix E: Data Visualization with the Mission Console

This appendix explains how processed sensor data is visualized in real-time through an interactive dashboard, allowing operators to monitor rover health and respond to anomalies.

---

## Part 1: Why Visualization Matters

### From Numbers to Insight

**Beginner Explanation:**

Imagine trying to monitor the rover by reading thousands of lines of numbers:

```
timestamp: 1234.5, battery_soc: 75.3, cpu_temp: 35.2, ...
timestamp: 1235.5, battery_soc: 75.2, cpu_temp: 35.4, ...
timestamp: 1236.5, battery_soc: 75.1, cpu_temp: 35.3, ...
...
```

Your eyes would glaze over! But show the same data as a graph:

```
Battery SoC (%)
100 ┤
 80 ┤●●●●●●╲
 60 ┤      ╲
 40 ┤       ╲●●●
 20 ┤          ╲
  0 └─────────────► Time
```

Now you instantly see: "Battery was stable, then dropped sharply at hour 6!" Visualization turns data into insight.

<details>
<summary><b>🔍 Intermediate Details: Dashboard Design Principles</b></summary>

**Effective mission consoles follow key principles:**

1. **Information Hierarchy**:
   - Most critical info at top (battery, alerts)
   - Details accessible via drill-down
   - Color coding for severity

2. **Real-time Updates**:
   - Live plots with streaming data
   - Automatic refresh (0.1-1 second intervals)
   - No page reloads needed

3. **Contextual Alerts**:
   - Visual indicators (🟢🟡🔴)
   - Positioned near relevant data
   - Persistent until acknowledged

4. **Historical Context**:
   - Show recent history (last 100 samples)
   - Allow playback and zoom
   - Compare to mission norms

5. **Interactive Controls**:
   - Pause/resume simulation
   - Adjust playback speed
   - Export data for analysis

**Mission console for Curiosity rover:**
- 12 HD displays showing telemetry, images, terrain
- Real-time during critical operations (landing, drilling)
- Recorded during communication windows for later analysis

Our Streamlit implementation mirrors these concepts at educational scale.

</details>

---

## Part 2: The Mission Console Architecture

### How Data Flows to the Display

**Beginner Explanation:**

The Mission Console is the final stage where everything comes together:

```
┌──────────────────────────────────────────────────────────┐
│              COMPLETE DATA FLOW                          │
└──────────────────────────────────────────────────────────┘

Simulation → Sensors → Packets → Cleaner → Anomaly Detector
                                                    │
                                                    ▼
                  ┌─────────────────────────────────────┐
                  │    MISSION CONSOLE DISPLAY          │
                  ├─────────────────────────────────────┤
                  │  📊 Telemetry Dashboard             │
                  │      ├─ Battery SoC                 │
                  │      ├─ CPU Temperature             │
                  │      ├─ Solar Power                 │
                  │      └─ System Health               │
                  │                                     │
                  │  🚨 Alert Monitor                   │
                  │      └─ Active anomalies            │
                  │                                     │
                  │  📈 Real-time Plots                 │
                  │      ├─ Time-series charts          │
                  │      └─ Interactive zoom/pan        │
                  │                                     │
                  │  ⏯️  Playback Controls              │
                  │      ├─ Start/Pause                 │
                  │      ├─ Speed control               │
                  │      └─ Reset                       │
                  └─────────────────────────────────────┘
```

**File location:** `meridian3/streamlit_app/pages/08_Mission_Console.py:1-200`

<details>
<summary><b>🔍 Intermediate Details: Streamlit Framework</b></summary>

**Why Streamlit?**

Streamlit is a Python framework for building data dashboards:

```python
import streamlit as st
import plotly.graph_objects as go

# Simple dashboard
st.title("Rover Dashboard")
battery_soc = 75.3
st.metric("Battery", f"{battery_soc}%")

# Interactive plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=times, y=values))
st.plotly_chart(fig)
```

**Advantages:**
- **Pure Python**: No HTML/CSS/JavaScript needed
- **Reactive**: Auto-updates when data changes
- **Components**: Built-in widgets (sliders, buttons, charts)
- **Fast iteration**: Changes visible immediately

**Architecture:**

Streamlit uses a "rerun on interaction" model:
1. User clicks button
2. Entire script reruns top-to-bottom
3. New state rendered
4. Efficient caching prevents redundant computation

**Session state** persists between reruns:
```python
if 'sim_running' not in st.session_state:
    st.session_state.sim_running = False  # Initialize

if st.button("Start"):
    st.session_state.sim_running = True  # Modify

if st.session_state.sim_running:
    # Update simulation
    st.rerun()  # Trigger refresh
```

**Real-time updates:**
```python
while st.session_state.sim_running:
    # Generate new telemetry
    current = generate_telemetry_snapshot(mission_time)

    # Display
    st.metric("Battery", f"{current['battery_soc']:.1f}%")

    # Sleep and rerun
    time.sleep(0.1)
    st.rerun()
```

</details>

---

## Part 3: Current Telemetry Display

### The Status Dashboard

**Beginner Explanation:**

At the top of the console, we show the current rover status in a glanceable format:

```python
# Display current status
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    sol_num = int(mission_time / 88775)  # Martian day
    st.metric("Mission Time", f"Sol {sol_num}",
             delta=f"{mission_time % 88775:.0f}s")

with col2:
    st.metric("Battery SoC", f"{battery_soc:.1f}%",
             delta=f"{battery_voltage:.1f}V")

with col3:
    temp_status = "🟢" if cpu_temp < 60 else "🟡" if cpu_temp < 70 else "🔴"
    st.metric("CPU Temp", f"{temp_status} {cpu_temp:.1f}°C")

with col4:
    st.metric("Solar Power", f"{solar_power:.0f}W",
             delta=f"Angle: {solar_angle:.0f}°")

with col5:
    alert_count = len(anomalies)
    st.metric("Active Alerts", f"{'🚨' if alert_count > 0 else '✅'} {alert_count}")
```

**File location:** `meridian3/streamlit_app/pages/08_Mission_Console.py:143-175`

**What this looks like:**

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ Mission Time │ Battery SoC  │  CPU Temp    │ Solar Power  │ Active Alerts│
│   Sol 47     │    75.3%     │  🟢 35.2°C   │    45W       │   ✅ 0       │
│   ↑ 23456s   │   ↑ 28.3V    │              │  ↑ Angle:60° │              │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

<details>
<summary><b>🔍 Intermediate Details: Metric Widget Design</b></summary>

**st.metric() components:**

```python
st.metric(
    label="Battery SoC",           # Main label
    value="75.3%",                 # Primary value (large font)
    delta="28.3V",                 # Secondary value (small, with arrow)
    delta_color="normal"           # Arrow color: "normal", "inverse", "off"
)
```

**Visual encoding:**

- **Size**: Primary value is 3x larger (draw eye to most important)
- **Color**: Green arrow (↑) for increasing, red (↓) for decreasing
- **Icons**: Emoji status indicators (🟢🟡🔴) for quick assessment
- **Position**: Left-to-right priority (mission time → battery → temp → power → alerts)

**Responsive design:**

Streamlit automatically stacks columns on mobile:
```
Desktop:  [Col1] [Col2] [Col3] [Col4] [Col5]

Mobile:   [Col1]
          [Col2]
          [Col3]
          [Col4]
          [Col5]
```

**Color psychology:**

- 🟢 Green: Safe, normal, continue
- 🟡 Yellow: Caution, monitor closely
- 🔴 Red: Critical, immediate action

Thresholds match anomaly detector:
```python
if cpu_temp < 60:
    status = "🟢"      # Normal operating temperature
elif cpu_temp < 70:
    status = "🟡"      # Getting warm, watch it
else:
    status = "🔴"      # Too hot, potential damage
```

</details>

---

## Part 4: Real-Time Plots

### Time-Series Visualization

**Beginner Explanation:**

The heart of the console is the real-time plotting system using Plotly:

```python
# Create plots from history
if st.session_state.telemetry_history:
    history = st.session_state.telemetry_history
    times = [h['time'] for h in history]
    battery_values = [h['battery_soc'] for h in history]
    temp_values = [h['cpu_temp'] for h in history]

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Battery State of Charge", "CPU Temperature",
                       "Solar Power", "System Overview")
    )

    # Add battery trace
    fig.add_trace(
        go.Scatter(
            x=times,
            y=battery_values,
            name="Battery SoC",
            line=dict(color='green', width=2)
        ),
        row=1, col=1
    )

    # Add temperature trace
    fig.add_trace(
        go.Scatter(
            x=times,
            y=temp_values,
            name="CPU Temp",
            line=dict(color='red', width=2)
        ),
        row=1, col=2
    )

    # Display interactive chart
    st.plotly_chart(fig, use_container_width=True)
```

**File location:** `meridian3/streamlit_app/pages/08_Mission_Console.py:193-200`

<details>
<summary><b>🔍 Intermediate Details: Plotly Interactive Features</b></summary>

**Built-in interactivity:**

Plotly charts support:
- **Zoom**: Click and drag to zoom region
- **Pan**: Shift+drag to pan view
- **Hover**: Mouse over shows exact values
- **Legend toggle**: Click legend items to show/hide traces
- **Reset**: Double-click to reset view
- **Download**: Export as PNG image

**Configuration:**

```python
fig = go.Figure()

# Configure layout
fig.update_layout(
    title="Battery Health",
    xaxis_title="Mission Time (seconds)",
    yaxis_title="State of Charge (%)",
    hovermode='x unified',          # Show all traces on hover
    showlegend=True,
    height=400,
    margin=dict(l=50, r=50, t=50, b=50)
)

# Add threshold lines
fig.add_hline(
    y=20,                           # Critical threshold
    line_dash="dash",
    line_color="red",
    annotation_text="Critical"
)
fig.add_hline(
    y=30,                           # Warning threshold
    line_dash="dot",
    line_color="orange",
    annotation_text="Warning"
)

# Styling traces
fig.add_trace(go.Scatter(
    x=times,
    y=values,
    mode='lines+markers',           # Show line and points
    marker=dict(size=4),
    line=dict(
        color='green',
        width=2,
        shape='spline'              # Smooth curves
    ),
    fill='tozeroy',                 # Fill area under curve
    fillcolor='rgba(0,255,0,0.1)'
))
```

**Performance optimization:**

For long missions (1000+ points):
```python
# Downsample for display
if len(times) > 1000:
    step = len(times) // 1000
    times = times[::step]
    values = values[::step]

# Or use Scattergl for WebGL rendering
fig.add_trace(go.Scattergl(  # GPU-accelerated
    x=times,
    y=values
))
```

**Multi-trace coordination:**

```python
# Shared x-axis for time correlation
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,              # Zoom synced across plots
    vertical_spacing=0.05
)

# Add anomaly markers
for anomaly in anomalies:
    fig.add_vline(
        x=anomaly['timestamp'],
        line_color="red",
        line_dash="dash",
        annotation_text=anomaly['description'],
        row='all'                   # Show on all subplots
    )
```

</details>

---

## Part 5: Alert Monitoring

### Visual Anomaly Display

**Beginner Explanation:**

When the anomaly detector finds problems, they appear prominently:

```python
# Show alerts if any
if current['anomalies']:
    st.warning(f"⚠️ **Alerts**: {', '.join(current['anomalies'])}")
```

This creates a yellow warning box:

```
⚠️ Alerts: Low battery, High CPU temp
```

For a full alert dashboard:

```python
st.markdown("### 🚨 Active Anomalies")

if frame['metadata']['anomalies']:
    for anomaly in frame['metadata']['anomalies']:
        severity_color = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🔵'
        }

        st.error(f"""
        {severity_color[anomaly['severity']]} **{anomaly['field'].upper()}**
        - Value: {anomaly['value']:.2f}
        - Type: {anomaly['type']}
        - Description: {anomaly['description']}
        - Time: {anomaly['timestamp']:.1f}s
        """)
else:
    st.success("✅ No active anomalies - all systems nominal")
```

**Displays as:**

```
┌─────────────────────────────────────────────────────┐
│ 🔴 BATTERY_SOC                                      │
│ - Value: 12.00                                      │
│ - Type: threshold                                   │
│ - Description: battery_soc critically low: 12.00    │
│ - Time: 1234.5s                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🟡 CPU_TEMP                                         │
│ - Value: 68.50                                      │
│ - Type: z-score                                     │
│ - Description: cpu_temp statistical outlier         │
│ - Time: 1234.5s                                     │
└─────────────────────────────────────────────────────┘
```

<details>
<summary><b>🔍 Intermediate Details: Alert Management Strategies</b></summary>

**Production alert systems implement:**

1. **Deduplication**:
   ```python
   # Don't show same alert multiple times
   if anomaly not in acknowledged_alerts:
       display_alert(anomaly)
   ```

2. **Prioritization**:
   ```python
   # Show critical alerts first
   sorted_alerts = sorted(
       anomalies,
       key=lambda a: {'critical': 0, 'warning': 1, 'info': 2}[a['severity']]
   )
   ```

3. **Acknowledgment**:
   ```python
   if st.button(f"Acknowledge {anomaly['field']}", key=anomaly['timestamp']):
       acknowledged_alerts.add(anomaly)
       st.rerun()
   ```

4. **Alert History**:
   ```python
   # Track all alerts for timeline
   alert_history.append({
       'timestamp': anomaly['timestamp'],
       'field': anomaly['field'],
       'severity': anomaly['severity'],
       'acknowledged_by': operator_name,
       'acknowledged_time': current_time
   })
   ```

5. **Sound/Visual Alerts**:
   ```python
   if any(a['severity'] == 'critical' for a in anomalies):
       st.markdown("""
       <audio autoplay>
         <source src="alarm.mp3" type="audio/mpeg">
       </audio>
       """, unsafe_allow_html=True)

       # Flash border
       st.markdown("""
       <style>
       .main { animation: flash 1s infinite; }
       @keyframes flash {
         0%, 100% { border: none; }
         50% { border: 5px solid red; }
       }
       </style>
       """, unsafe_allow_html=True)
   ```

6. **Context Links**:
   ```python
   st.error(f"""
   🔴 {anomaly['description']}

   [View detailed telemetry](#telemetry-{anomaly['field']})
   [Check historical trends](#history)
   [Review procedures](#procedure-{anomaly['field']})
   """)
   ```

</details>

---

## Part 6: Playback Controls

### Interactive Simulation

**Beginner Explanation:**

The console lets you control the simulation like a video player:

```python
# Mission controls
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("▶️ Start" if not sim_running else "⏸️ Pause"):
        st.session_state.sim_running = not st.session_state.sim_running

with col2:
    if st.button("🔄 Reset"):
        st.session_state.mission_time = 0
        st.session_state.telemetry_history = []
        st.session_state.sim_running = False

with col3:
    speed = st.selectbox("Speed", ["1x", "2x", "5x", "10x"])
    speed_mult = int(speed.replace("x", ""))

with col4:
    history_len = st.slider("History (samples)", 20, 200, 100)
```

**File location:** `meridian3/streamlit_app/pages/08_Mission_Console.py:92-112`

<details>
<summary><b>🔍 Intermediate Details: Simulation Loop Integration</b></summary>

**The update cycle:**

```python
# Generate telemetry snapshot
def generate_telemetry_snapshot(mission_time):
    """Generate realistic telemetry at given mission time"""
    # Simulated values with realistic variations
    solar_angle = max(0, 90 * np.sin(2 * np.pi * mission_time / 88775))
    battery_soc = 85 - 0.001 * mission_time + 5 * np.sin(2 * np.pi * mission_time / 88775)
    battery_voltage = 26 + 2 * (battery_soc / 100) + np.random.normal(0, 0.1)
    cpu_temp = 35 + 15 * (solar_angle / 90) + np.random.normal(0, 2)

    # Check for anomalies
    anomalies = []
    if battery_soc < 30:
        anomalies.append("Low battery")

    return {
        'time': mission_time,
        'battery_soc': max(0, min(100, battery_soc)),
        'battery_voltage': battery_voltage,
        'cpu_temp': cpu_temp,
        'anomalies': anomalies
    }

# Main loop
if st.session_state.sim_running:
    # Advance time based on speed
    st.session_state.mission_time += speed_mult

    # Generate new data
    current = generate_telemetry_snapshot(st.session_state.mission_time)

    # Add to history
    st.session_state.telemetry_history.append(current)

    # Limit history size
    if len(st.session_state.telemetry_history) > history_len:
        st.session_state.telemetry_history = st.session_state.telemetry_history[-history_len:]

    # Sleep and rerun
    time.sleep(0.1)
    st.rerun()
```

**File location:** `meridian3/streamlit_app/pages/08_Mission_Console.py:114-191`

**Why this design?**

- **Responsive**: 10 Hz update rate (0.1s sleep)
- **Controllable**: Speed multiplier for fast-forward
- **Memory-efficient**: Fixed history size
- **Pausable**: Stop for detailed inspection

**Integration with full pipeline:**

In production, replace `generate_telemetry_snapshot()` with:

```python
# Full pipeline integration
def get_next_frame():
    # Generate from simulation
    raw_frame = sim_generator.generate_next()

    # Packetize
    packet = packetizer.encode_frame(raw_frame)

    # Simulate corruption
    corrupted = corruptor.corrupt_packet(packet)

    # Clean
    clean_frame = cleaner.clean_packet(corrupted)

    # Detect anomalies
    labeled_frame = anomaly_detector.analyze_frame(clean_frame)

    return labeled_frame

# In simulation loop
if st.session_state.sim_running:
    current_frame = get_next_frame()
    st.session_state.telemetry_history.append(current_frame)
    # ... display logic
```

</details>

---

## Part 7: Dashboard Best Practices

### Design Lessons

**Beginner Explanation:**

Good dashboards follow these principles:

1. **Most important info at top** (battery, alerts)
2. **Use color meaningfully** (red = danger, green = OK)
3. **Show trends, not just values** (graphs reveal patterns)
4. **Allow interaction** (zoom, pause, export)
5. **Provide context** (show thresholds, history)

<details>
<summary><b>🔍 Intermediate Details: Dashboard Anti-Patterns to Avoid</b></summary>

**Common mistakes:**

1. **Information overload**:
   ```python
   # BAD: Too much on one screen
   for i in range(100):
       st.metric(f"Sensor {i}", values[i])

   # GOOD: Summarize and drill down
   st.metric("Sensors OK", "97/100")
   with st.expander("View all sensors"):
       for sensor in sensors:
           st.write(f"{sensor.name}: {sensor.value}")
   ```

2. **Misleading visualizations**:
   ```python
   # BAD: Non-zero baseline exaggerates change
   fig.update_yaxes(range=[70, 80])  # Makes 2% change look huge

   # GOOD: Include zero or show full range
   fig.update_yaxes(range=[0, 100])
   ```

3. **No error handling**:
   ```python
   # BAD: Crashes on missing data
   battery = frame['battery_soc']

   # GOOD: Graceful degradation
   battery = frame.get('battery_soc', None)
   if battery is not None:
       st.metric("Battery", f"{battery}%")
   else:
       st.warning("Battery data unavailable")
   ```

4. **Poor responsiveness**:
   ```python
   # BAD: Blocks for minutes
   data = run_expensive_analysis(all_data)  # 5 minutes!

   # GOOD: Cache and paginate
   @st.cache_data
   def run_analysis(data_subset):
       return analyze(data_subset)

   page_size = 100
   data_page = all_data[page*page_size:(page+1)*page_size]
   result = run_analysis(data_page)
   ```

5. **No mobile support**:
   ```python
   # BAD: Fixed widths
   st.markdown('<div style="width: 1920px;">...</div>')

   # GOOD: Responsive columns
   col1, col2 = st.columns([2, 1])  # Ratios, not pixels
   ```

</details>

---

## Key Takeaways

1. **Visualization transforms numbers into insight** through charts and indicators
2. **Real-time dashboards** provide immediate feedback on rover health
3. **Interactive controls** allow exploration and playback
4. **Alert systems** highlight anomalies for operator response
5. **Good design** prioritizes critical information and enables quick decisions

### Where to Look in the Code

- **Mission Console**: `meridian3/streamlit_app/pages/08_Mission_Console.py:1-200`
- **Telemetry dashboard**: `meridian3/streamlit_app/pages/08_Mission_Console.py:143-175`
- **Real-time plots**: `meridian3/streamlit_app/pages/08_Mission_Console.py:179-200`
- **Simulation controls**: `meridian3/streamlit_app/pages/08_Mission_Console.py:92-112`
- **Telemetry generation**: `meridian3/streamlit_app/pages/08_Mission_Console.py:114-141`

---

## Complete Data Flow Summary

From sensor to screen, here's the complete journey:

```
1. RoverState (ground truth)
   ↓
2. Sensors add noise
   ↓
3. Telemetry frame created
   ↓
4. Packetizer wraps in packet structure
   ↓
5. Corruptor simulates transmission errors
   ↓
6. Cleaner validates and repairs data
   ↓
7. Anomaly Detector labels unusual patterns
   ↓
8. Mission Console displays:
   - Current metrics
   - Real-time plots
   - Active alerts
   - Historical trends
```

**Every piece serves the mission:** Keep the rover alive, collect science data, and return safely.

---

**Previous:** [Appendix D: Anomaly Detection](./Appendix_D_Anomaly_Detection.md)
