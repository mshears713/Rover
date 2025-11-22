"""
Appendix B: How Data Gets Packetized

TEACHING FOCUS:
    - Frame-to-packet encoding process
    - Metadata and timestamp management
    - Packet structure and organization
    - Binary encoding and data serialization

NARRATIVE:
    This appendix explores how raw sensor frames are encoded into
    packets for transmission. It covers the packetization process,
    metadata handling, and the structure of transmitted data.

LEARNING OBJECTIVES:
    - Understand the packetization pipeline
    - Learn packet structure and metadata
    - See how timestamps are managed
    - Master the frame encoding architecture
    - Explore binary encoding and compression

ARCHITECTURE:
    The packetization pipeline transforms JSON frames into binary packets:
    1. Frame Reception: Receive dictionary of sensor readings
    2. Metadata Addition: Add timestamps and sequence numbers
    3. Encoding: Convert to binary format
    4. Packaging: Create structured packet with header

TEACHING APPROACH:
    - Interactive packet construction
    - Binary data visualization
    - Encoding efficiency analysis
    - Batch processing demonstrations

IMPLEMENTATION:
    Full interactive implementation following patterns from Chapters 1-3.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(
    page_title="Appendix B: Data Packetization",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Appendix B: How Data Gets Packetized")

st.markdown("""
## From Telemetry Frames to Transmission Packets

Once sensors generate telemetry frames, those frames must be **packetized** for
transmission. This process adds metadata, timestamps, and prepares data for the
communication channel.

Understanding packetization is essential for debugging transmission issues and
optimizing bandwidth usage.
""")

# ═══════════════════════════════════════════════════════════════════════════
# ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📋 Packetization Architecture", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │              DATA PACKETIZATION PIPELINE                     │
    └──────────────────────────────────────────────────────────────┘

         ┌─────────────────┐
         │ Telemetry Frame │  Input: Dictionary
         │  ─────────────  │
         │  {             │  - Sensor readings
         │   "roll": 0.12 │  - Float values
         │   "temp": 25.3 │  - No metadata yet
         │   ...          │  - JSON format
         │  }             │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   Packetizer    │  Add Metadata
         │  ─────────────  │
         │  + Timestamp    │  - Mission time
         │  + Sequence #   │  - Packet counter
         │  + Frame ID     │  - Unique identifier
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Binary Packet  │  Output: Bytes
         │  ─────────────  │
         │  [Header]      │  - Fixed structure
         │  [Metadata]    │  - Compact encoding
         │  [Payload]     │  - Ready for transmission
         └─────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Telemetry Frame**
        - Human-readable dict
        - Flexible structure
        - Float precision
        - No transmission overhead
        - Produced by sensors
        """)

    with col2:
        st.markdown("""
        **Packetizer Operations**
        - Add timestamps
        - Assign sequence numbers
        - Validate data ranges
        - Prepare for encoding
        - Track packet history
        """)

    with col3:
        st.markdown("""
        **Binary Packet**
        - Compact binary format
        - Fixed header structure
        - Efficient encoding
        - Ready for transmission
        - Includes error detection
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: FRAME TO PACKET ENCODING
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Frame Encoding Process")

st.markdown("""
Let's take a sensor frame and walk through the packetization process step by step.
We'll see how a dictionary becomes a binary packet ready for transmission.
""")

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite
    from pipeline.packetizer import Packetizer

    if st.button("📦 Generate and Packetize Frame", type="primary", key="exp1_run"):
        # Generate a frame
        rover = RoverState()
        sensors = SensorSuite()
        frame = sensors.read_all(rover, mission_time=100.0)

        # Packetize it
        packetizer = Packetizer()
        packet = packetizer.packetize(frame, mission_time=100.0)

        st.markdown("### Step 1: Input Telemetry Frame")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Frame Contents:**")
            st.json(frame)

        with col2:
            st.markdown("**Frame Statistics:**")
            frame_str = json.dumps(frame)
            st.metric("Number of Fields", len(frame))
            st.metric("JSON Size (bytes)", len(frame_str))
            st.metric("Average Value Length", f"{len(frame_str)/len(frame):.1f}")

        st.markdown("### Step 2: Packet with Metadata")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Complete Packet Structure:**")
            st.json(packet)

        with col2:
            st.markdown("**Added Metadata:**")
            st.code(f"""
Timestamp:    {packet.get('timestamp', 'N/A')}
Packet ID:    {packet.get('packet_id', 'N/A')}
Sequence:     {packet.get('sequence', 'N/A')}
Frame Count:  {len(packet.get('data', {}))} fields
            """, language="text")

        # Size comparison
        st.markdown("### Step 3: Size Analysis")

        packet_str = json.dumps(packet)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Original Frame", f"{len(frame_str)} bytes")

        with col2:
            metadata_overhead = len(packet_str) - len(frame_str)
            st.metric("Metadata Overhead", f"{metadata_overhead} bytes")

        with col3:
            st.metric("Total Packet", f"{len(packet_str)} bytes")

        with col4:
            overhead_pct = (metadata_overhead / len(frame_str)) * 100
            st.metric("Overhead %", f"{overhead_pct:.1f}%")

        st.info("""
        **📚 Key Observations:**
        - **Timestamp** enables time-series reconstruction
        - **Packet ID** allows tracking and deduplication
        - **Sequence number** detects missing packets
        - **Metadata overhead** is typically 10-20% of frame size
        - All metadata is essential for robust communication
        """)

except ImportError as e:
    st.error(f"⚠️ Pipeline modules not found. Error: {str(e)}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: PACKET STRUCTURE INSPECTOR
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Packet Structure Deep Dive")

st.markdown("""
Examine the internal structure of packets in detail. We'll visualize how data
is organized and explore different encoding strategies.
""")

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite
    from pipeline.packetizer import Packetizer

    col1, col2 = st.columns([2, 1])

    with col1:
        mission_time = st.number_input(
            "Mission Time (seconds)",
            min_value=0.0,
            max_value=100000.0,
            value=1000.0,
            step=10.0,
            key="exp2_time"
        )

    with col2:
        if st.button("🔍 Inspect Packet", type="primary", key="exp2_run"):
            st.session_state['exp2_packet'] = True

    if st.session_state.get('exp2_packet', False):
        # Generate packet
        rover = RoverState()
        sensors = SensorSuite()
        frame = sensors.read_all(rover, mission_time=mission_time)
        packetizer = Packetizer()
        packet = packetizer.packetize(frame, mission_time=mission_time)

        st.markdown("### 📦 Packet Breakdown")

        # Extract sections
        metadata_fields = ['timestamp', 'packet_id', 'sequence']
        data_fields = {k: v for k, v in packet.items() if k not in metadata_fields}

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Metadata Section**")
            for field in metadata_fields:
                if field in packet:
                    st.code(f"{field}: {packet[field]}", language="text")

        with col2:
            st.markdown("**Data Section Preview**")
            preview_count = 5
            for i, (k, v) in enumerate(data_fields.items()):
                if i < preview_count:
                    st.code(f"{k}: {v}", language="text")
            if len(data_fields) > preview_count:
                st.code(f"... {len(data_fields) - preview_count} more fields", language="text")

        with col3:
            st.markdown("**Packet Statistics**")
            total_size = len(json.dumps(packet))
            metadata_size = len(json.dumps({k: packet[k] for k in metadata_fields if k in packet}))
            data_size = total_size - metadata_size

            st.metric("Total Size", f"{total_size} bytes")
            st.metric("Metadata", f"{metadata_size} bytes")
            st.metric("Data", f"{data_size} bytes")

        # Visualize packet composition
        st.markdown("### 📊 Packet Composition")

        fig = go.Figure(data=[go.Pie(
            labels=['Metadata', 'Sensor Data'],
            values=[metadata_size, data_size],
            hole=0.3,
            marker_colors=['lightblue', 'lightgreen']
        )])

        fig.update_layout(
            title="Packet Size Breakdown",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **📚 Packet Structure Insights:**
        - **Metadata** provides context for data interpretation
        - **Sensor data** comprises the majority of packet size
        - **Fixed metadata** enables consistent parsing
        - **Variable data** section adapts to sensor suite changes
        - This structure balances flexibility and efficiency
        """)

except ImportError as e:
    st.error(f"⚠️ Pipeline modules not found. Error: {str(e)}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: BATCH PACKETIZATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Batch Packet Generation")

st.markdown("""
In real missions, packets are generated continuously. Let's simulate a batch
of packets and analyze the packet stream characteristics.
""")

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite
    from pipeline.packetizer import Packetizer

    col1, col2 = st.columns(2)

    with col1:
        num_packets = st.slider(
            "Number of packets to generate",
            5, 50, 20, 5,
            help="Simulate a packet stream",
            key="exp3_num"
        )

    with col2:
        time_interval = st.slider(
            "Time interval (seconds)",
            0.1, 10.0, 1.0, 0.1,
            help="Time between packets",
            key="exp3_interval"
        )

    if st.button("📦 Generate Packet Stream", type="primary", key="exp3_run"):
        rover = RoverState()
        sensors = SensorSuite()
        packetizer = Packetizer()

        packets_data = []
        packet_sizes = []

        for i in range(num_packets):
            mission_time = i * time_interval
            frame = sensors.read_all(rover, mission_time=mission_time)
            packet = packetizer.packetize(frame, mission_time=mission_time)

            packet_size = len(json.dumps(packet))
            packet_sizes.append(packet_size)

            packets_data.append({
                'Packet': i,
                'Time (s)': f"{mission_time:.2f}",
                'Sequence': packet.get('sequence', i),
                'Size (bytes)': packet_size,
                'Fields': len(packet.get('data', packet)) if 'data' in packet else len(packet)
            })

        df = pd.DataFrame(packets_data)

        st.markdown("### 📊 Packet Stream Overview")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Packets", num_packets)

        with col2:
            avg_size = np.mean(packet_sizes)
            st.metric("Avg Packet Size", f"{avg_size:.0f} bytes")

        with col3:
            total_size = np.sum(packet_sizes)
            st.metric("Total Data", f"{total_size:,} bytes")

        with col4:
            total_time = (num_packets - 1) * time_interval
            if total_time > 0:
                throughput = total_size / total_time
                st.metric("Throughput", f"{throughput:.0f} bytes/s")

        # Visualize packet stream
        st.markdown("### 📈 Packet Stream Visualization")

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Packet Sizes Over Time", "Size Distribution"),
            horizontal_spacing=0.12
        )

        # Time series
        times = [i * time_interval for i in range(num_packets)]
        fig.add_trace(
            go.Scatter(
                x=times,
                y=packet_sizes,
                mode='lines+markers',
                name='Packet Size',
                line=dict(color='steelblue', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )

        # Histogram
        fig.add_trace(
            go.Histogram(
                x=packet_sizes,
                nbinsx=20,
                name='Distribution',
                marker_color='lightgreen',
                opacity=0.7
            ),
            row=1, col=2
        )

        fig.update_xaxes(title_text="Time (s)", row=1, col=1)
        fig.update_xaxes(title_text="Packet Size (bytes)", row=1, col=2)
        fig.update_yaxes(title_text="Size (bytes)", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=2)

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Bandwidth analysis
        st.markdown("### 📡 Bandwidth Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Data Rate Requirements:**")
            bits_per_second = (avg_size * 8) / time_interval
            st.code(f"""
Average packet size: {avg_size:.0f} bytes
Transmission interval: {time_interval:.1f} seconds
Required bandwidth: {bits_per_second:.0f} bits/s
                    {bits_per_second/1000:.2f} kbps
            """, language="text")

        with col2:
            st.markdown("**Efficiency Metrics:**")
            size_variation = np.std(packet_sizes)
            st.code(f"""
Size std deviation: {size_variation:.1f} bytes
Size consistency: {((1 - size_variation/avg_size) * 100):.1f}%
Total data volume: {total_size/1024:.2f} KB
Compression potential: ~30-50% typical
            """, language="text")

        st.success("""
        **✅ Packet Stream Generated Successfully!**

        This stream would now flow through:
        1. **Corruptor** → Simulate transmission errors
        2. **Channel** → Model bandwidth and latency
        3. **Receiver** → Reassemble and validate
        4. **Cleaner** → Reconstruct corrupted data
        """)

except ImportError as e:
    st.error(f"⚠️ Pipeline modules not found. Error: {str(e)}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: TIMESTAMP AND SEQUENCING
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Timestamp and Sequence Management")

st.markdown("""
Timestamps and sequence numbers are critical for reconstructing time-ordered
data and detecting packet loss. Let's explore how they work.
""")

try:
    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite
    from pipeline.packetizer import Packetizer

    col1, col2 = st.columns(2)

    with col1:
        start_time = st.number_input(
            "Start time (seconds)",
            0.0, 10000.0, 0.0, 1.0,
            key="exp4_start"
        )

    with col2:
        num_samples = st.slider(
            "Number of samples",
            5, 30, 15, 1,
            key="exp4_samples"
        )

    if st.button("⏱️ Analyze Timestamps", type="primary", key="exp4_run"):
        rover = RoverState()
        sensors = SensorSuite()
        packetizer = Packetizer()

        timestamp_data = []

        for i in range(num_samples):
            mission_time = start_time + i
            frame = sensors.read_all(rover, mission_time=mission_time)
            packet = packetizer.packetize(frame, mission_time=mission_time)

            timestamp_data.append({
                'Index': i,
                'Mission Time': mission_time,
                'Timestamp': packet.get('timestamp', mission_time),
                'Sequence': packet.get('sequence', i),
                'Delta (s)': 1.0 if i > 0 else 0.0
            })

        df = pd.DataFrame(timestamp_data)

        st.markdown("### ⏰ Timestamp Sequence Analysis")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Visualize sequence
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['Index'],
            y=df['Timestamp'],
            mode='lines+markers',
            name='Timestamp',
            line=dict(color='steelblue', width=2),
            marker=dict(size=8, color='steelblue')
        ))

        fig.update_layout(
            title="Timestamp Progression",
            xaxis_title="Packet Index",
            yaxis_title="Mission Time (s)",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("First Timestamp", f"{df['Timestamp'].iloc[0]:.1f}s")

        with col2:
            st.metric("Last Timestamp", f"{df['Timestamp'].iloc[-1]:.1f}s")

        with col3:
            duration = df['Timestamp'].iloc[-1] - df['Timestamp'].iloc[0]
            st.metric("Duration", f"{duration:.1f}s")

        with col4:
            avg_interval = duration / (num_samples - 1) if num_samples > 1 else 0
            st.metric("Avg Interval", f"{avg_interval:.2f}s")

        st.info("""
        **📚 Timestamp Management:**
        - **Monotonic timestamps** enable time-series reconstruction
        - **Sequence numbers** detect missing or duplicate packets
        - **Regular intervals** indicate healthy transmission
        - **Gaps** reveal packet loss or transmission delays
        - Both are essential for data integrity validation
        """)

except ImportError as e:
    st.error(f"⚠️ Pipeline modules not found. Error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Appendix B Complete!**

You've learned:
- ✅ How telemetry frames are packetized for transmission
- ✅ Packet structure including metadata and payload
- ✅ Size overhead and bandwidth considerations
- ✅ Batch packet stream generation and analysis
- ✅ Timestamp and sequence number management
- ✅ The role of packetization in data integrity

**Connection to Mission**: Packetization is the bridge between sensor data
and transmission. Understanding this process is crucial for optimizing bandwidth,
detecting transmission errors, and ensuring data arrives in usable form.

**Next**: Proceed to Appendix C to learn how corrupted and incomplete packets are cleaned and validated.
""")

st.markdown("*Navigate to Appendix C: Data Cleaning in the sidebar →*")
