"""
Chapter 5: Packets and Loss

TEACHING FOCUS:
    - Telemetry packet structure
    - Transmission encoding and metadata
    - Communication channel imperfections
    - Packet loss and corruption modeling

NARRATIVE:
    Telemetry doesn't magically appear on Earth. It travels hundreds of
    millions of kilometers through space, facing interference, noise, and
    data loss. Understanding the transmission layer is critical for robust
    ground systems.

LEARNING OBJECTIVES:
    - Understand packet structure and encoding
    - Model realistic transmission errors
    - Calculate packet loss statistics
    - Design for degraded communication channels

ARCHITECTURE:
    Packetizer → Corruptor → Receiver
    - Packetizer encodes frames as packets
    - Corruptor simulates transmission errors
    - Receiver must handle corrupted/missing packets

TEACHING APPROACH:
    - Interactive packet encoding demo
    - Corruption simulator with adjustable rates
    - Real-time visualization of packet integrity
    - Statistics on loss patterns

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 36.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

st.set_page_config(page_title="Packets and Loss", page_icon="📦", layout="wide")

st.title("📦 Chapter 5: Packets and Loss")

st.markdown("""
## From Rover to Earth: The Transmission Challenge

Raw sensor frames must be packaged, encoded, and transmitted across vast
distances. Not all data makes it through intact. This chapter explores the
realities of space communication.
""")

# ═══════════════════════════════════════════════════════════════════════════
# PACKET STRUCTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📦 Packet Structure Overview", expanded=True):
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────┐
    │                  TELEMETRY PACKET FORMAT                     │
    └──────────────────────────────────────────────────────────────┘

    ┌─────────────┬────────────────────────┬─────────────┐
    │   HEADER    │        PAYLOAD         │   FOOTER    │
    ├─────────────┼────────────────────────┼─────────────┤
    │ - Packet ID │ - Sensor readings      │ - Checksum  │
    │ - Timestamp │ - Engineering data     │ - CRC-16    │
    │ - Type      │ - Status flags         │ - End marker│
    │ - Length    │ - Compressed data      │             │
    │   (12 bytes)│      (variable)        │   (4 bytes) │
    └─────────────┴────────────────────────┴─────────────┘

    CORRUPTION MODES:
    ┌──────────────────────────────────────────────────────────────┐
    │ 📦 → 📦 → 📦 → ❌ → 📦 → 📦   (Packet Loss)                  │
    │ 📦 → 📦 → ⚠️  → 📦 → 📦 → 📦   (Bit Flip)                    │
    │ 📦 → 📦 → 📦 → 📦 → 📦 → ⏰   (Timing Jitter)                │
    │ 📦 → 📦 → 📛 → 📦 → 📦 → 📦   (Field Corruption)             │
    └──────────────────────────────────────────────────────────────┘
    ```
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Packet Loss**
        - Entire packets don't arrive
        - Typical: 1-5% nominal
        - Higher during conjunction
        - Gaps in telemetry timeline
        """)

    with col2:
        st.markdown("""
        **Bit Flips**
        - Individual bits corrupted
        - Rate: 10^-6 to 10^-4 per bit
        - Detected by checksum
        - May pass if within valid range
        """)

    with col3:
        st.markdown("""
        **Field Corruption**
        - Partial payload damage
        - Some fields valid, others not
        - Requires field-level validation
        - Complex recovery needed
        """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: PACKET ENCODING DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 1: Packet Encoding")

st.markdown("""
Let's see how a raw telemetry frame gets encoded into a packet for transmission.
""")

if st.button("📦 Generate Sample Packet", type="primary", key="encode_exp1"):
    # Create a sample telemetry frame
    sample_frame = {
        "timestamp": 12345.678,
        "battery_voltage": 28.4,
        "battery_soc": 85.2,
        "cpu_temp": 45.3,
        "roll": 0.12,
        "pitch": -0.05,
        "heading": 135.7
    }

    # Simulate packet structure
    packet_id = np.random.randint(1000, 9999)
    packet_type = "TELEMETRY"
    payload_json = json.dumps(sample_frame)
    payload_size = len(payload_json)

    # Calculate simple checksum (sum of bytes % 65536)
    checksum = sum(payload_json.encode()) % 65536

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Raw Telemetry Frame")
        st.json(sample_frame)

    with col2:
        st.markdown("### Encoded Packet")
        packet = {
            "header": {
                "packet_id": packet_id,
                "timestamp": sample_frame["timestamp"],
                "type": packet_type,
                "length": payload_size
            },
            "payload": sample_frame,
            "footer": {
                "checksum": checksum,
                "end_marker": "EOF"
            }
        }
        st.json(packet)

    # Display packet metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Packet ID", f"#{packet_id}")

    with col2:
        st.metric("Payload Size", f"{payload_size} bytes")

    with col3:
        st.metric("Total Size", f"{payload_size + 16} bytes",
                 help="Header(12) + Payload + Footer(4)")

    with col4:
        st.metric("Checksum", f"0x{checksum:04X}",
                 help="CRC for error detection")

    st.info("""
    **📚 Packet Structure:**
    - **Header**: Identifies and describes the packet
    - **Payload**: The actual telemetry data (can be compressed)
    - **Footer**: Error detection (checksum/CRC) and termination marker
    - Receiver validates checksum to detect corruption
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: PACKET LOSS SIMULATION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 2: Packet Loss Simulation")

st.markdown("""
Simulate a stream of packets with configurable loss rate to see the impact
on telemetry continuity.
""")

col1, col2, col3 = st.columns(3)

with col1:
    num_packets = st.slider("Number of packets", 50, 500, 200, step=50,
                           help="Total packets in transmission")

with col2:
    loss_rate = st.slider("Loss rate (%)", 0.0, 20.0, 5.0, step=0.5,
                         help="Percentage of packets lost")

with col3:
    burst_loss = st.checkbox("Burst losses", value=False,
                            help="Lose packets in bursts (realistic)")

if st.button("📡 Simulate Transmission", type="primary", key="loss_exp2"):
    # Generate packet stream
    packets = np.arange(num_packets)
    received = np.ones(num_packets, dtype=bool)

    # Apply packet loss
    if burst_loss:
        # Burst mode: lose packets in groups
        num_bursts = max(1, int(num_packets * loss_rate / 100 / 5))
        for _ in range(num_bursts):
            burst_start = np.random.randint(0, num_packets - 5)
            burst_length = np.random.randint(3, 8)
            received[burst_start:min(burst_start + burst_length, num_packets)] = False
    else:
        # Random mode: independent loss
        received = np.random.random(num_packets) > (loss_rate / 100)

    # Calculate statistics
    num_received = np.sum(received)
    num_lost = num_packets - num_received
    actual_loss_rate = (num_lost / num_packets) * 100

    # Find gaps (consecutive losses)
    gaps = []
    gap_start = None
    for i, r in enumerate(received):
        if not r and gap_start is None:
            gap_start = i
        elif r and gap_start is not None:
            gaps.append((gap_start, i - 1))
            gap_start = None
    if gap_start is not None:
        gaps.append((gap_start, num_packets - 1))

    max_gap = max([end - start + 1 for start, end in gaps]) if gaps else 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Packets Sent", f"{num_packets}")

    with col2:
        st.metric("Packets Received", f"{num_received}",
                 delta=f"-{num_lost} lost")

    with col3:
        st.metric("Actual Loss Rate", f"{actual_loss_rate:.1f}%",
                 help="Realized loss percentage")

    with col4:
        st.metric("Max Gap", f"{max_gap} packets",
                 help="Longest consecutive loss")

    # Visualization
    fig = go.Figure()

    # Show received packets as green dots, lost as red X
    received_packets = packets[received]
    lost_packets = packets[~received]

    fig.add_trace(go.Scatter(
        x=received_packets,
        y=np.ones(len(received_packets)),
        mode='markers',
        name='Received',
        marker=dict(symbol='circle', size=8, color='green'),
        hovertemplate='Packet %{x}: Received<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=lost_packets,
        y=np.ones(len(lost_packets)),
        mode='markers',
        name='Lost',
        marker=dict(symbol='x', size=12, color='red', line=dict(width=2)),
        hovertemplate='Packet %{x}: LOST<extra></extra>'
    ))

    # Highlight gaps
    for gap_start, gap_end in gaps:
        fig.add_vrect(
            x0=gap_start - 0.5, x1=gap_end + 0.5,
            fillcolor="red", opacity=0.1,
            layer="below", line_width=0
        )

    fig.update_layout(
        title=f"Packet Transmission ({num_received}/{num_packets} received, {actual_loss_rate:.1f}% loss)",
        xaxis_title="Packet Sequence Number",
        yaxis=dict(showticklabels=False, range=[0.5, 1.5]),
        height=250,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Gap analysis
    if gaps:
        st.markdown("### 📊 Loss Gaps Analysis")
        gap_df = pd.DataFrame([
            {"Gap #": i + 1, "Start Packet": start, "End Packet": end, "Length": end - start + 1}
            for i, (start, end) in enumerate(gaps)
        ])
        st.dataframe(gap_df, use_container_width=True, hide_index=True)

    st.warning(f"""
    **⚠️ Impact of {actual_loss_rate:.1f}% Packet Loss:**
    - **{num_lost}** packets completely lost
    - **{len(gaps)}** gaps in telemetry timeline
    - Longest gap: **{max_gap}** packets (must interpolate across this)
    - Critical data may be missing
    - Mission operations must handle incomplete data
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: BIT FLIP CORRUPTION
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 3: Bit Flip Corruption")

st.markdown("""
Bit flips corrupt individual bits in the data stream. Some are detected by
checksums, others may pass unnoticed if they result in valid-looking values.
""")

col1, col2 = st.columns(2)

with col1:
    bit_error_rate = st.select_slider(
        "Bit Error Rate (BER)",
        options=[1e-6, 1e-5, 1e-4, 1e-3, 1e-2],
        value=1e-4,
        format_func=lambda x: f"10^{int(np.log10(x))}",
        help="Probability of any single bit flipping"
    )

with col2:
    num_test_packets = st.slider("Test packets", 10, 100, 50, step=10)

if st.button("⚠️ Simulate Bit Flips", type="primary", key="bitflip_exp3"):
    # Simulate packets with bit flips
    corrupted_count = 0
    detected_count = 0
    undetected_count = 0

    results = []

    for i in range(num_test_packets):
        # Generate random data (simulating a packet)
        original_value = np.random.uniform(20, 30)  # e.g., battery voltage

        # Convert to binary representation (simplified)
        # Assume 32-bit float = 32 bits
        num_bits = 32

        # Simulate bit flips
        num_flips = np.random.binomial(num_bits, bit_error_rate)

        if num_flips > 0:
            corrupted_count += 1
            # Simulate corruption effect
            corruption_magnitude = num_flips * 0.1  # Each flip changes value slightly
            corrupted_value = original_value + np.random.uniform(-corruption_magnitude, corruption_magnitude)

            # Simple checksum detection (detects ~95% of corruptions)
            detected = np.random.random() < 0.95

            if detected:
                detected_count += 1
                status = "Detected & Rejected"
                color = "orange"
            else:
                undetected_count += 1
                status = "Undetected!"
                color = "red"
        else:
            corrupted_value = original_value
            status = "Clean"
            color = "green"

        results.append({
            "Packet": i + 1,
            "Original": original_value,
            "Received": corrupted_value,
            "Bit Flips": num_flips,
            "Status": status,
            "Color": color
        })

    df = pd.DataFrame(results)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Corrupted Packets", f"{corrupted_count}",
                 delta=f"{corrupted_count/num_test_packets*100:.1f}%")

    with col2:
        st.metric("Detected", f"{detected_count}",
                 help="Caught by checksum")

    with col3:
        st.metric("Undetected", f"{undetected_count}",
                 delta="Critical!",
                 delta_color="inverse" if undetected_count > 0 else "off",
                 help="Passed checksum but still corrupt")

    with col4:
        detection_rate = (detected_count / corrupted_count * 100) if corrupted_count > 0 else 100
        st.metric("Detection Rate", f"{detection_rate:.0f}%",
                 help="Percentage of corruptions caught")

    # Visualization
    fig = go.Figure()

    # Plot original and received values
    clean_df = df[df['Status'] == 'Clean']
    detected_df = df[df['Status'] == 'Detected & Rejected']
    undetected_df = df[df['Status'] == 'Undetected!']

    fig.add_trace(go.Scatter(
        x=clean_df['Packet'], y=clean_df['Received'],
        mode='markers', name='Clean',
        marker=dict(color='green', size=8, symbol='circle')
    ))

    fig.add_trace(go.Scatter(
        x=detected_df['Packet'], y=detected_df['Received'],
        mode='markers', name='Corrupted (Detected)',
        marker=dict(color='orange', size=10, symbol='x')
    ))

    fig.add_trace(go.Scatter(
        x=undetected_df['Packet'], y=undetected_df['Received'],
        mode='markers', name='Corrupted (Undetected!)',
        marker=dict(color='red', size=12, symbol='diamond')
    ))

    fig.update_layout(
        title="Packet Corruption Detection",
        xaxis_title="Packet Number",
        yaxis_title="Value",
        height=400,
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show detailed table
    with st.expander("📋 Detailed Packet Log"):
        st.dataframe(
            df[['Packet', 'Original', 'Received', 'Bit Flips', 'Status']].style.apply(
                lambda row: ['background-color: ' + df.loc[row.name, 'Color'] if c == 'Status' else ''
                            for c in row.index], axis=1
            ),
            use_container_width=True,
            hide_index=True
        )

    st.error(f"""
    **🔴 Bit Flip Impact:**
    - **{corrupted_count}** packets affected by bit flips
    - **{detected_count}** caught by checksum and discarded
    - **{undetected_count}** UNDETECTED corruptions (false negatives!)
    - Undetected corruptions look valid but contain wrong data
    - Additional validation layers are essential
    """)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: COMBINED CORRUPTION SCENARIO
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## 🔬 Experiment 4: Realistic Communication Channel")

st.markdown("""
Real space communication channels have **multiple simultaneous** corruption modes:
packet loss, bit flips, and timing jitter all happening together.
""")

col1, col2, col3 = st.columns(3)

with col1:
    scenario = st.selectbox(
        "Channel Conditions",
        ["Nominal", "Moderate Degradation", "Severe Degradation", "Conjunction"],
        help="Pre-configured realistic scenarios"
    )

scenarios = {
    "Nominal": {"loss": 2.0, "ber": 1e-5, "jitter": 0.1},
    "Moderate Degradation": {"loss": 8.0, "ber": 5e-5, "jitter": 0.5},
    "Severe Degradation": {"loss": 15.0, "ber": 1e-4, "jitter": 1.0},
    "Conjunction": {"loss": 35.0, "ber": 5e-4, "jitter": 2.0}
}

params = scenarios[scenario]

with col2:
    st.metric("Packet Loss", f"{params['loss']:.1f}%")

with col3:
    st.metric("Bit Error Rate", f"10^{int(np.log10(params['ber']))}")

if st.button("📡 Simulate Mission Segment", type="primary", key="combined_exp4"):
    # Simulate 1-hour mission segment, 1 packet/second
    total_packets = 3600
    packets_sent = np.arange(total_packets)

    # Apply packet loss
    received_mask = np.random.random(total_packets) > (params['loss'] / 100)
    packets_received = packets_sent[received_mask]

    # Apply bit corruption to received packets
    num_received = len(packets_received)
    corrupted_mask = np.random.random(num_received) < (params['ber'] * 32 * 8)  # Assume 32-byte packets
    detected_mask = corrupted_mask & (np.random.random(num_received) < 0.95)
    undetected_mask = corrupted_mask & ~detected_mask

    # Count results
    num_lost = total_packets - num_received
    num_corrupted = np.sum(corrupted_mask)
    num_detected = np.sum(detected_mask)
    num_undetected = np.sum(undetected_mask)
    num_clean = num_received - num_corrupted

    # Final usable packets
    usable_packets = num_clean
    usable_rate = (usable_packets / total_packets) * 100

    # Metrics
    st.markdown("### 📊 Mission Segment Results")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Sent", f"{total_packets}")

    with col2:
        st.metric("Lost", f"{num_lost}",
                 delta=f"{params['loss']:.1f}%",
                 delta_color="inverse")

    with col3:
        st.metric("Corrupted", f"{num_corrupted}",
                 help="Bit flips in received packets")

    with col4:
        st.metric("Rejected", f"{num_detected}",
                 help="Corruptions caught by checksum")

    with col5:
        st.metric("Usable", f"{usable_packets}",
                 delta=f"{usable_rate:.1f}%",
                 help="Clean, uncorrupted packets")

    # Breakdown visualization
    fig = go.Figure(data=[go.Pie(
        labels=['Clean', 'Lost', 'Detected Corruption', 'Undetected Corruption'],
        values=[num_clean, num_lost, num_detected, num_undetected],
        marker=dict(colors=['green', 'red', 'orange', 'darkred']),
        hole=0.3
    )])

    fig.update_layout(
        title=f"Packet Fate Distribution - {scenario} Conditions",
        height=400,
        annotations=[dict(text=f'{usable_rate:.1f}%<br>Usable', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    st.plotly_chart(fig, use_container_width=True)

    # Data quality over time
    window_size = 300  # 5-minute windows
    num_windows = total_packets // window_size
    quality_by_window = []

    for i in range(num_windows):
        window_start = i * window_size
        window_end = (i + 1) * window_size
        window_received = received_mask[window_start:window_end]
        quality = np.sum(window_received) / window_size * 100
        quality_by_window.append(quality)

    fig_quality = go.Figure()
    fig_quality.add_trace(go.Scatter(
        x=np.arange(num_windows) * 5,  # Minutes
        y=quality_by_window,
        mode='lines+markers',
        name='Data Quality',
        line=dict(color='blue', width=2),
        fill='tozeroy'
    ))

    fig_quality.add_hline(y=100 - params['loss'], line_dash="dash", line_color="green",
                         annotation_text=f"Expected ({100 - params['loss']:.0f}%)")

    fig_quality.update_layout(
        title="Data Quality Over Mission Segment (5-minute windows)",
        xaxis_title="Mission Time (minutes)",
        yaxis_title="Packet Reception Rate (%)",
        height=300
    )

    st.plotly_chart(fig_quality, use_container_width=True)

    # Summary
    if scenario == "Nominal":
        st.success(f"""
        **✅ Nominal Conditions:**
        - Only **{params['loss']:.1f}%** packet loss - very manageable
        - **{usable_rate:.1f}%** of telemetry is usable
        - Standard interpolation can fill small gaps
        - Mission operations proceed normally
        """)
    elif scenario == "Conjunction":
        st.error(f"""
        **🔴 Conjunction - Critical Degradation:**
        - **{params['loss']:.0f}%** packet loss - severe!
        - Only **{usable_rate:.1f}%** of telemetry usable
        - Large data gaps require aggressive interpolation
        - May need to suspend critical operations until link improves
        - Store data onboard for retransmission
        """)
    else:
        st.warning(f"""
        **⚠️ {scenario}:**
        - **{params['loss']:.1f}%** packet loss
        - **{usable_rate:.1f}%** of telemetry usable
        - Data cleaning and validation crucial
        - Monitor link quality closely
        """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.success("""
**🎓 Chapter 5 Complete!**

You've learned:
- ✅ Telemetry packet structure (header, payload, footer)
- ✅ Packet loss patterns and statistics
- ✅ Bit flip corruption and detection
- ✅ Combined corruption in realistic scenarios
- ✅ Data quality metrics for mission segments
- ✅ Why robust error handling is essential

**Next Steps**: Proceed to Chapter 6 to learn how the data cleaning layer
reconstructs usable telemetry from corrupted packets.
""")

st.markdown("*Navigate to Chapter 6: Cleaning and Validation in the sidebar →*")
