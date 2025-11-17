# Rover Simulation Project - Claude Code Agent Guide

## Project Identity

You are working on **Rover**, a complete simulated rover environment with a 10-chapter interactive Streamlit learning console. This is an **educational codebase** where every component is designed for teaching through heavily commented code, narrative explanations, ASCII diagrams, debugging notes, and future-improvement sections.

## Critical Context

### Project Nature
- **Purpose**: Full-scale learning environment for simulation, telemetry pipelines, anomaly detection, storage, and UI engineering
- **Target Audience**: Students and engineers learning system design
- **Code Philosophy**: Educational and verbose, NOT minimal or production-optimized
- **Modularity**: Highly modular and extensible by design

### Teaching Goals

**Primary:**
- Architecture and modular system design
- Simulation modeling
- Telemetry pipeline engineering
- Data cleaning and anomaly detection
- Streamlit UI engineering

**Secondary:**
- Async programming
- Plotly/Matplotlib visualization
- Persistent state through SQLite and caches
- Code organization patterns and maintainability

## System Architecture

```
┌────────────────────┐
│   Environment       │
│ (terrain, hazards)  │
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│   Sensor Engine     │
└─────────┬──────────┘
          │ frames
┌──────────────▼───────────────┐
│       Packetizer Layer        │
└──────────────┬───────────────┘
          │ packets
┌─────────▼──────────┐
│     Corruptor       │
└─────────┬──────────┘
          │ degraded packets
┌────────────────────▼─────────────────────┐
│      Cleaning & Validation Layer          │
└────────────────────┬─────────────────────┘
          │ clean frames
┌──────────▼──────────┐
│   Anomaly Detector   │
└──────────┬──────────┘
          │ labeled frames
┌───────────────────────▼─────────────────────────┐
│               Storage & Archive                  │
└───────────────────────┬─────────────────────────┘
          │
┌──────────────▼───────────────┐
│    Streamlit Mission Console   │
└────────────────────────────────┘
```

### Data Flow
1. **Simulator** generates sensor frames
2. **Packetizer** encodes frames
3. **Corruptor** applies degradation (loss, jitter, field removal)
4. **Cleaner** validates and repairs frames
5. **Anomaly Detector** labels events
6. **Storage** archives mission data
7. **Streamlit Console** visualizes results

## Directory Structure

```
meridian3/
├── streamlit_app/
│   ├── Home.py
│   ├── pages/
│   │   ├── 01_Sensors_and_Body.py
│   │   ├── 02_Time_and_Orbits.py
│   │   ├── 03_Noise_and_Wear.py
│   │   ├── 04_Terrain_and_Hazards.py
│   │   ├── 05_Packets_and_Loss.py
│   │   ├── 06_Cleaning_and_Validation.py
│   │   ├── 07_Anomaly_Detection.py
│   │   ├── 08_Mission_Console.py
│   │   ├── 09_Post_Mission_Archive.py
│   │   └── 10_Engineering_Legacy.py
│   └── assets/
├── src/
│   ├── simulator/
│   │   ├── rover_state.py
│   │   ├── sensors.py
│   │   ├── environment.py
│   │   └── generator.py
│   ├── pipeline/
│   │   ├── packetizer.py
│   │   ├── corruptor.py
│   │   ├── cleaner.py
│   │   ├── anomalies.py
│   │   └── storage.py
│   ├── utils/
│   │   ├── timing.py
│   │   ├── math_helpers.py
│   │   └── plotting.py
│   └── config/
│       ├── default_params.yaml
│       └── mission_templates/
├── data/
│   ├── missions.sqlite
│   └── caches/
└── README.md
```

## CRITICAL RULES - MUST FOLLOW

### README Protection
⚠️ **DO NOT MODIFY README.md AFTER PHASE 1** ⚠️
- The README contains the master plan
- It is the source of truth for all phases
- Modifications after Phase 1 are strictly forbidden

### Phased Development Protocol
- Work is organized into 5 phases with 50 total steps (see README)
- **ONLY complete phases/steps when explicitly instructed**
- **DO NOT execute future phases early**
- **DO NOT modify completed phases** unless explicitly asked
- **DO NOT merge phases** or skip steps
- **DO NOT invent new directories** unless required by a specific step
- Follow the exact sequence defined in README

### Current Phase Awareness
Before starting any work:
1. Check README for current phase context
2. Confirm which phase/step you're being asked to complete
3. Review what has already been completed
4. Understand dependencies from prior phases

## Code Quality Standards

### Every File MUST Include

#### 1. Narrative Header Docstring
Each file requires a comprehensive header covering:
- **Purpose**: What this module does
- **Theory**: Relevant concepts and principles
- **Architecture Role**: How it fits in the system
- **Teaching Goals**: What learners should understand
- **Analogy/Story** (optional): Connection to Meridian-3 mission narrative

**Example Structure:**
```python
"""
Module: sensors.py
Purpose: Simulates rover sensor readings with realistic noise and degradation

THEORY:
Real rover sensors experience drift, noise, environmental interference, and
wear over time. This module models these effects to create realistic telemetry.

ARCHITECTURE ROLE:
Sits between RoverState (ground truth) and the Packetizer. Takes perfect
state values and adds realistic imperfections before transmission.

TEACHING GOALS:
- Understanding sensor noise characteristics
- Modeling environmental effects on measurements
- Balancing realism vs computational cost
- Debugging sensor anomalies

[Additional narrative content...]
"""
```

#### 2. ASCII Diagrams
Include diagrams for:
- Data flow through the module
- Class relationships
- Algorithm steps
- State transitions

**Example:**
```python
"""
SENSOR PIPELINE:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Ground Truth│───▶│ Add Noise    │───▶│ Apply Drift │
│  (Perfect)  │    │ + Environment│    │ + Wear      │
└─────────────┘    └──────────────┘    └─────────────┘
"""
```

#### 3. Rich Inline Comments
- Explain **why**, not just **what**
- Include teaching commentary
- Reference relevant theory
- Explain edge cases and design decisions

**Good Example:**
```python
# We use exponential smoothing here rather than a simple moving average
# because it gives more weight to recent values while maintaining history.
# This better models how sensor hardware actually responds to rapid changes.
# Alpha=0.3 chosen empirically to balance responsiveness vs noise filtering.
smoothed_value = alpha * current + (1 - alpha) * previous
```

**Bad Example:**
```python
# Calculate smoothed value
smoothed_value = alpha * current + (1 - alpha) * previous
```

#### 4. Debugging Notes Section
Add a section explaining:
- Common issues and their symptoms
- Debugging strategies
- Useful test values
- Validation approaches

**Example:**
```python
"""
DEBUGGING NOTES:
- If temperature readings spike unrealistically, check dust_factor scaling
- To test sensor drift: run 1000+ timesteps and plot cumulative error
- Validation: temperature should stay between -100°C and 50°C
- Use `sensor.reset_baseline()` to clear accumulated drift for testing
"""
```

#### 5. Future Extensions Section
Document potential improvements:
```python
"""
FUTURE EXTENSIONS:
1. Add correlated noise between related sensors (e.g., tilt affects IMU)
2. Implement sensor failure modes (stuck values, dropout)
3. Model battery level impact on sensor accuracy
4. Add calibration drift requiring periodic reset
5. Support sensor fusion algorithms
"""
```

## Development Patterns

### Code Style
- **Verbose over concise**: Favor readability and teaching clarity
- **Explicit over implicit**: Make assumptions visible
- **Documented over clever**: Explain non-obvious logic
- **Educational over optimal**: Performance is secondary to learning

### Function Documentation
Every function should explain:
- Parameters (with units and valid ranges)
- Return values (with types and meanings)
- Side effects
- Teaching context

```python
def calculate_solar_heating(
    sun_angle: float,      # degrees, 0=horizon, 90=directly overhead
    dust_opacity: float,   # 0.0-1.0, fraction of light blocked
    albedo: float         # 0.0-1.0, surface reflectivity
) -> float:
    """
    Calculate thermal heating from solar radiation.

    TEACHING NOTE: This simplified model ignores atmospheric scattering
    and assumes instantaneous thermal response. Real planetary heating
    involves thermal inertia and subsurface conduction.

    Returns: Temperature increase in Celsius
    """
    # Implementation with teaching comments...
```

### Class Design
- Use clear, descriptive names
- Document state variables and their meanings
- Explain invariants that must be maintained
- Include example usage in docstring

### Error Handling
- Use descriptive error messages
- Explain what went wrong and why
- Suggest corrective actions
- Include context for debugging

```python
if temperature < -273.15:  # Below absolute zero
    raise ValueError(
        f"Impossible temperature: {temperature}°C. "
        f"This suggests a bug in thermal calculation. "
        f"Check solar_heating and radiative_cooling terms."
    )
```

## Working with Phases

### Phase Structure (50 Steps Total)

**Phase 1 - Foundations (Steps 1-10)**
- Directory structure
- Module stubs with documentation
- ASCII diagrams
- Placeholder classes
- Configuration files

**Phase 2 - Simulator Core (Steps 11-20)**
- RoverState implementation
- Sensor models with noise
- Terrain effects engine
- Hazard generation
- Simulation loop

**Phase 3 - Telemetry Pipeline (Steps 21-30)**
- Packetizer layer
- Corruptor implementation
- Cleaning and validation
- Anomaly detection
- Storage layer

**Phase 4 - Streamlit Console (Steps 31-40)**
- All 10 Streamlit pages
- Interactive visualizations
- Tutorial content
- Mission console UI

**Phase 5 - Integration & Polish (Steps 41-50)**
- System orchestration
- Async implementation
- Session state management
- Final polish and documentation

### When Asked to Work on a Phase

1. **Confirm Understanding**
   - State which phase and steps you'll complete
   - Reference the README for exact requirements

2. **Check Dependencies**
   - Verify prior phases are complete
   - Identify what you're building upon

3. **Follow Step Sequence**
   - Complete steps in exact order
   - Don't skip or combine steps

4. **Maintain Standards**
   - Apply all code quality requirements
   - Include all required documentation sections

5. **Preserve Prior Work**
   - Don't modify completed phases
   - Build upon, don't replace

## Technology Stack

### Primary Technologies
- **Python 3.10+**: Core language
- **Streamlit**: Web UI framework
- **SQLite**: Mission data persistence
- **Plotly/Matplotlib**: Visualization
- **NumPy**: Numerical operations
- **PyYAML**: Configuration files

### Coding Conventions
- Use type hints where helpful for teaching
- Prefer explicit imports over wildcards
- Use descriptive variable names (clarity over brevity)
- Follow PEP 8 with educational exceptions (longer lines for comments OK)

## Common Pitfalls to Avoid

❌ **Don't:**
- Modify README after Phase 1
- Jump ahead to future phases
- Write minimal/production code
- Skip documentation requirements
- Invent new directories without instruction
- Merge or reorder steps
- Use cryptic variable names
- Omit teaching commentary

✅ **Do:**
- Follow phased approach strictly
- Write verbose educational code
- Include all required documentation
- Add ASCII diagrams
- Explain design decisions
- Think about teaching goals
- Include debugging and extension notes
- Ask for clarification if phase is ambiguous

## Questions to Ask Before Starting

1. **Which phase/steps should I complete?**
2. **Are there dependencies I need to verify?**
3. **Should I modify existing files or create new ones?**
4. **Are there specific teaching concepts to emphasize?**
5. **What has already been completed that I build upon?**

## Testing and Validation

While not test-driven, code should be:
- **Runnable**: No syntax errors, handles expected inputs
- **Demonstrable**: Can be shown working in Streamlit
- **Debuggable**: Includes self-test functions where appropriate
- **Educational**: Error cases teach about failure modes

## Success Criteria

You've succeeded when:
- ✅ README remains unchanged (after Phase 1)
- ✅ Requested phase/steps are complete
- ✅ All files have required documentation
- ✅ ASCII diagrams present in major modules
- ✅ Code is verbose and educational
- ✅ Teaching commentary explains concepts
- ✅ Debugging notes included
- ✅ Future extensions documented
- ✅ Directory structure matches specification
- ✅ No future phases started prematurely

## Getting Help

### Key Reference
- **README.md**: Master plan with all 50 steps
- **default_params.yaml**: Configuration structure (created in Phase 1)

### When Uncertain
1. Reference the README for the specific step description
2. Look at completed phases for patterns
3. Ask for clarification rather than guessing
4. Confirm phase/step before proceeding

## Summary

This is an **educational codebase** where **teaching is the primary goal**. Follow the **phased approach strictly**, include **comprehensive documentation**, and write **verbose, well-commented code**. Never modify the README after Phase 1, and only complete phases when explicitly instructed.

Think of yourself as creating a textbook through code, where every file is a chapter that teaches important concepts through working examples.
