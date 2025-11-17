"""
Meridian-3 Rover Mission Console - Home

This is the main landing page for the Meridian-3 interactive learning environment.

MISSION OVERVIEW:
    Welcome to the Meridian-3 rover simulation and mission console. This
    interactive learning environment teaches spacecraft systems engineering
    through a realistic rover simulation covering:

    - Sensor systems and telemetry generation
    - Environmental modeling and orbital mechanics
    - Telemetry pipeline engineering
    - Data quality and anomaly detection
    - Mission operations and archival

LEARNING PATH:
    This console is organized into 10 chapters, each focusing on a specific
    aspect of rover operations. Work through them sequentially for the full
    experience, or jump to topics of interest.

    Chapters 1-4: Simulation fundamentals
    Chapters 5-7: Telemetry pipeline
    Chapters 8-10: Mission operations

ARCHITECTURE:
    The system follows a layered design:
    Environment → Sensors → Packetizer → Corruptor → Cleaner →
    Anomaly Detector → Storage → UI

    Each layer is independently teachable and testable, demonstrating
    real-world systems engineering principles.

TEACHING PHILOSOPHY:
    - Code is heavily commented for learning
    - Each module includes ASCII diagrams
    - Debugging helpers show internal state
    - Extension points encourage experimentation
    - Real engineering tradeoffs are highlighted

IMPLEMENTATION STATUS:
    Phase 1: ✓ Foundation structure
    Phase 2: ✓ Core simulation
    Phase 3: ✓ Telemetry pipeline
    Phase 4: ✓ Interactive console (current)
    Phase 5: → Full integration

Full implementation in Phase 4, Step 31.
"""

import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

st.set_page_config(
    page_title="Meridian-3 Mission Console",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════
# HEADER AND MISSION BADGE
# ═══════════════════════════════════════════════════════════════════════════

st.title("🚀 Meridian-3 Rover Mission Console")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("""
    ### Interactive Systems Engineering Learning Environment
    *Master spacecraft telemetry through hands-on simulation*
    """)

with col2:
    st.metric("Mission Status", "OPERATIONAL", delta="Active")

with col3:
    st.metric("System Modules", "10", delta="All Online")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# MISSION NARRATIVE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
## 🌍 Welcome to Mars

You are the lead systems engineer for **Meridian-3**, an autonomous rover exploring
the Martian surface. Your mission: ensure continuous operations despite:

- **Harsh Environment**: Temperature swings, dust storms, radiation bursts
- **Limited Bandwidth**: Corrupted packets, transmission delays, data loss
- **Sensor Degradation**: Noise, drift, calibration errors, component wear
- **Unknown Hazards**: Terrain challenges, unexpected anomalies

This console is your **mission control interface** and **engineering workbench**.
Through 10 interactive chapters, you'll learn the complete pipeline from raw
sensor physics to operational mission data.

""")

# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM ARCHITECTURE DIAGRAM
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("📐 System Architecture Overview", expanded=True):
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    MERIDIAN-3 DATA PIPELINE                     │
    └─────────────────────────────────────────────────────────────────┘

         SIMULATION LAYER              TELEMETRY LAYER          OPERATIONS
    ┌──────────────────────┐      ┌──────────────────────┐   ┌──────────┐
    │                      │      │                      │   │          │
    │   🌍 Environment     │      │   📦 Packetizer      │   │    📊    │
    │  - Terrain model     │      │  - Frame encoding    │   │ Mission  │
    │  - Hazard events     │      │  - Timestamps        │   │ Console  │
    │  - Orbital mechanics │      │  - Metadata          │   │          │
    │                      │      │                      │   │  - Live  │
    └──────────┬───────────┘      └──────────┬───────────┘   │  - Plot  │
               │                             │               │  - Alert │
               ▼                             ▼               │          │
    ┌──────────────────────┐      ┌──────────────────────┐   └────┬─────┘
    │                      │      │                      │        │
    │   📡 Sensor Engine   │      │   ⚠️  Corruptor      │        │
    │  - IMU (orientation) │      │  - Packet loss       │        │
    │  - Power monitors    │      │  - Bit flips         │        │
    │  - Thermal array     │      │  - Jitter/delay      │        │
    │  - Position/velocity │      │  - Field corruption  │        │
    │                      │      │                      │        │
    └──────────┬───────────┘      └──────────┬───────────┘        │
               │                             │                    │
               │ sensor frames               │ corrupted packets  │
               │                             ▼                    │
               │                  ┌──────────────────────┐        │
               │                  │                      │        │
               │                  │   🔧 Cleaner         │        │
               │                  │  - Range validation  │        │
               │                  │  - Interpolation     │        │
               └─────────────────▶│  - Reconstruction    │        │
                                  │                      │        │
                                  └──────────┬───────────┘        │
                                             │ clean frames       │
                                             ▼                    │
                                  ┌──────────────────────┐        │
                                  │                      │        │
                                  │  🎯 Anomaly Detector │        │
                                  │  - Threshold checks  │        │
                                  │  - Derivative alarms │        │
                                  │  - Z-score detection │        │
                                  │                      │        │
                                  └──────────┬───────────┘        │
                                             │ labeled frames     │
                                             ▼                    │
                                  ┌──────────────────────┐        │
                                  │                      │        │
                                  │  💾 Storage          │◀───────┘
                                  │  - SQLite missions   │
                                  │  - JSON caching      │
                                  │  - Archive retrieval │
                                  │                      │
                                  └──────────────────────┘
    ```

    **Key Teaching Points:**
    - Each layer has a specific responsibility (separation of concerns)
    - Data flows top-to-bottom (unidirectional pipeline)
    - Degradation is intentional (teaches robustness)
    - Clean data reconstruction is the core challenge
    """)

# ═══════════════════════════════════════════════════════════════════════════
# LEARNING PATH GUIDE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 📚 Learning Path")

st.markdown("""
The 10 chapters are organized into three learning tracks. Work through them
sequentially for the complete experience, or jump to topics of interest.
""")

# Track 1: Simulation Fundamentals
st.markdown("### 🔬 Track 1: Simulation Fundamentals (Chapters 1-4)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Chapter 1: Sensors and Body** 📡
    - Rover physical state representation
    - Sensor suite overview and specifications
    - Understanding measurement vs. true state
    - Sensor noise characteristics

    **Chapter 2: Time and Orbits** 🌅
    - Martian sols and Earth time conversion
    - Solar position and day/night cycles
    - Power generation profiles
    - Thermal cycling effects
    """)

with col2:
    st.markdown("""
    **Chapter 3: Noise and Wear** 📉
    - Gaussian sensor noise modeling
    - Sensor drift and calibration errors
    - Component degradation over time
    - Temperature-dependent effects

    **Chapter 4: Terrain and Hazards** 🏔️
    - Terrain slope and traction modeling
    - Dust storm simulation
    - Radiation burst events
    - Slip detection and recovery
    """)

# Track 2: Telemetry Pipeline
st.markdown("### 🔧 Track 2: Telemetry Pipeline (Chapters 5-7)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Chapter 5: Packets and Loss** 📦
    - Frame-to-packet encoding
    - Packet transmission simulation
    - Corruption types: loss, bit flips, jitter
    - Understanding data degradation

    **Chapter 6: Cleaning and Validation** ✅
    - Range checking and outlier removal
    - Interpolation strategies
    - Data reconstruction techniques
    - Quality metrics and reporting
    """)

with col2:
    st.markdown("""
    **Chapter 7: Anomaly Detection** 🎯
    - Threshold-based detection
    - Rate-of-change alarms
    - Statistical anomaly scoring
    - Alert prioritization and classification
    """)

# Track 3: Mission Operations
st.markdown("### 🚀 Track 3: Mission Operations (Chapters 8-10)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Chapter 8: Mission Console** 🖥️
    - Live telemetry monitoring
    - Real-time plotting and visualization
    - Alert display and management
    - Mission control operations

    **Chapter 9: Post-Mission Archive** 📂
    - Mission data review
    - Historical analysis tools
    - Event timeline reconstruction
    - Performance metrics and reports
    """)

with col2:
    st.markdown("""
    **Chapter 10: Engineering Legacy** 📖
    - Complete system reference
    - Extension points and ideas
    - Performance optimization notes
    - Future enhancement roadmap
    """)

# ═══════════════════════════════════════════════════════════════════════════
# QUICK START GUIDE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

with st.expander("🚀 Quick Start Guide", expanded=False):
    st.markdown("""
    ### Getting Started with Meridian-3

    **First Time Here?**
    1. Start with **Chapter 1: Sensors and Body** to understand the rover's sensor suite
    2. Progress through **Chapters 2-4** to learn simulation fundamentals
    3. Master the telemetry pipeline in **Chapters 5-7**
    4. Apply your knowledge in **Chapters 8-10** for mission operations

    **Want to Jump Around?**
    - Interested in **data quality**? → Start at Chapter 6
    - Curious about **anomaly detection**? → Jump to Chapter 7
    - Ready for **live operations**? → Go to Chapter 8

    **For Educators:**
    - Each chapter is self-contained with teaching notes
    - Code includes extensive inline commentary
    - ASCII diagrams explain architecture
    - Debugging helpers show internal state
    - Extension ideas encourage experimentation

    **For Students:**
    - Interactive controls let you explore parameter effects
    - Visualizations show both "truth" and "measured" data
    - Try breaking things to learn failure modes
    - Check the Engineering Legacy (Ch. 10) for deep dives

    ### Navigation Tips
    - Use the **sidebar** to switch between chapters
    - Most chapters have **interactive controls** - try different settings!
    - Look for **expander sections** (▶) for additional details
    - **Metrics and charts** update in real-time as you adjust parameters
    """)

# ═══════════════════════════════════════════════════════════════════════════
# IMPLEMENTATION STATUS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🔧 System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **Phase 1** ✅
    Foundation
    *Complete*
    """)

with col2:
    st.markdown("""
    **Phase 2** ✅
    Simulation
    *Complete*
    """)

with col3:
    st.markdown("""
    **Phase 3** ✅
    Pipeline
    *Complete*
    """)

with col4:
    st.markdown("""
    **Phase 4** 🚧
    Console
    *In Progress*
    """)

# ═══════════════════════════════════════════════════════════════════════════
# TECHNICAL DETAILS
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("🔬 Technical Implementation Details", expanded=False):
    st.markdown("""
    ### Technology Stack

    **Frontend**: Streamlit (Python web framework)
    - Interactive controls and real-time updates
    - Multi-page application structure
    - Session state management for data persistence

    **Simulation**: NumPy + Custom Physics
    - Deterministic rover state evolution
    - Realistic sensor noise models
    - Environmental effects engine

    **Visualization**: Plotly + Matplotlib
    - Interactive time-series plots
    - 2D/3D terrain visualization
    - Statistical distribution displays

    **Data Pipeline**: Python + SQLite
    - In-memory frame processing
    - Persistent mission archival
    - JSON caching for fast retrieval

    **Architecture Principles**:
    - **Modularity**: Each component is independently testable
    - **Observability**: Extensive debugging helpers show internal state
    - **Teachability**: Code is heavily commented with narrative explanations
    - **Extensibility**: Clear extension points for student projects

    ### File Organization
    ```
    meridian3/
    ├── src/
    │   ├── simulator/      # Physics and sensor models
    │   ├── pipeline/       # Data processing layers
    │   ├── utils/          # Helpers and plotting tools
    │   └── config/         # Parameter configurations
    ├── streamlit_app/      # Interactive UI pages
    │   ├── Home.py        # This file
    │   └── pages/         # Chapters 1-10
    └── data/              # Mission archive and caches
    ```

    ### Performance Characteristics
    - **Simulation Rate**: ~1000 frames/second (single-threaded)
    - **Packet Processing**: ~5000 packets/second
    - **Storage**: SQLite with indexing for fast retrieval
    - **UI Refresh**: Real-time updates with Streamlit reactivity
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER AND NEXT STEPS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.info("""
💡 **Ready to Begin?**
Navigate to **Chapter 1: Sensors and Body** in the sidebar to start your journey!

*"In space systems, telemetry is not just data—it's the lifeline between
hardware and mission success. Understanding this pipeline is understanding
spacecraft engineering."*
""")

st.markdown("""
---
<div style='text-align: center; color: #666;'>
    <small>
    Meridian-3 Interactive Learning Console | Built with Streamlit + Python<br>
    An educational systems engineering environment
    </small>
</div>
""", unsafe_allow_html=True)
