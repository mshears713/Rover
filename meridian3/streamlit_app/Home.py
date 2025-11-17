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

IMPLEMENTATION STATUS:
    Phase 1: Foundation structure (current)
    Phase 2: Core simulation
    Phase 3: Telemetry pipeline
    Phase 4: Interactive console
    Phase 5: Full integration

Full implementation in Phase 4, Step 31.
"""

import streamlit as st

st.set_page_config(
    page_title="Meridian-3 Mission Console",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Meridian-3 Rover Mission Console")

st.markdown("""
## Welcome to the Meridian-3 Learning Environment

This interactive console teaches spacecraft systems engineering through a complete
rover simulation. You'll learn about:

- **Sensor Physics & Telemetry**: How rovers measure their world
- **Environmental Effects**: Terrain, hazards, and orbital mechanics
- **Data Pipeline Engineering**: From raw signals to clean, validated data
- **Anomaly Detection**: Identifying problems before they become critical
- **Mission Operations**: Planning, monitoring, and archival

---

### 📚 Learning Chapters

Navigate using the sidebar to explore each chapter:

1. **Sensors and Body** - Rover physical state and sensor suite
2. **Time and Orbits** - Martian sols, solar angles, day/night cycles
3. **Noise and Wear** - Realistic sensor imperfections
4. **Terrain and Hazards** - Environmental challenges
5. **Packets and Loss** - Transmission and corruption
6. **Cleaning and Validation** - Data quality engineering
7. **Anomaly Detection** - Pattern recognition and alerts
8. **Mission Console** - Live operations interface
9. **Post-Mission Archive** - Data review and analysis
10. **Engineering Legacy** - Reference and extensions

---

### 🔧 Current Status

**Phase 1 Complete**: Foundation structure established

Future phases will implement the full simulation and interactive features.

---

*"The best way to learn systems engineering is to build a system."*
""")

# Placeholder for future interactive content
st.info("Interactive simulation features will be added in Phase 4")
