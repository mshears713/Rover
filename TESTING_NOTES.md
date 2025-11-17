# Meridian-3 Rover Simulation - Comprehensive Testing Campaign Notes

**Created:** 2025-11-17
**Purpose:** Document all components that need testing and define test strategies

---

## TABLE OF CONTENTS
1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Testing Strategy](#testing-strategy)
4. [Component Testing Matrix](#component-testing-matrix)
5. [Test Priorities](#test-priorities)
6. [Known Edge Cases](#known-edge-cases)
7. [Testing Roadmap](#testing-roadmap)

---

## PROJECT OVERVIEW

The Meridian-3 project is a comprehensive Mars rover simulation with:
- **Simulator**: RoverState, Sensors (IMU, Power, Thermal), Environment (terrain, hazards, orbital mechanics)
- **Telemetry Pipeline**: Packetizer, Corruptor, Cleaner, Anomaly Detector, Storage
- **Utilities**: Math helpers (noise, smoothing, interpolation), Timing, Debug helpers
- **Streamlit UI**: 10 pages for visualization and interaction
- **Examples**: pipeline_demo.py for end-to-end demonstration

**Primary Goal**: Ensure the program runs seamlessly in production use

---

## ARCHITECTURE SUMMARY

```
┌─────────────────────────────────────────────────────────────┐
│                    SIMULATION FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Environment → RoverState → Sensors → Telemetry Frames     │
│                     ↓                        ↓              │
│                 Generator  →  Packetizer → Corruptor        │
│                                                 ↓           │
│                            Cleaner ← [corrupted packets]    │
│                                ↓                            │
│                        Anomaly Detector                     │
│                                ↓                            │
│                            Storage (SQLite)                 │
│                                ↓                            │
│                      Streamlit Mission Console              │
└─────────────────────────────────────────────────────────────┘
```

---

## TESTING STRATEGY

### 1. Unit Tests
Test individual components in isolation with mocked dependencies.

### 2. Integration Tests
Test how components work together (e.g., Simulator → Packetizer → Corruptor).

### 3. End-to-End Tests
Test complete pipeline from simulation to storage to UI.

### 4. Edge Case Tests
Test boundary conditions, error handling, and unusual inputs.

### 5. Performance Tests
Verify system can handle long-running simulations without memory leaks or slowdowns.

---

## COMPONENT TESTING MATRIX

### SIMULATOR COMPONENTS

#### 1. RoverState (`meridian3/src/simulator/rover_state.py`)
**What it does:** Manages rover's complete physical and operational state

**Tests needed:**
- ✅ Initialization with default values
- ✅ __repr__ string formatting
- ✅ State field ranges (battery_soc 0-100%, temperatures, voltages)
- ✅ Boolean flags (is_moving, is_charging, heater_active, science_active)
- ⚠️ **Edge cases:**
  - Negative battery values
  - Extreme temperature values (-999, +999)
  - Invalid roll/pitch/heading angles
  - Time fields (mission_time, sol, local_time consistency)

**Priority:** HIGH (foundation for everything)

---

#### 2. Sensors (`meridian3/src/simulator/sensors.py`)
**What it does:** Simulates IMU, Power, and Thermal sensors with realistic noise and drift

**Components:**
- `SensorBase`: Base class with noise, bias, drift
- `IMUSensor`: Roll, pitch, heading measurements
- `PowerSensor`: Battery and solar measurements
- `ThermalSensor`: Temperature measurements
- `SensorSuite`: Orchestrates all sensors

**Tests needed:**
- ✅ Noise application (add_gaussian_noise)
- ✅ Drift accumulation over time
- ✅ Quantization (temperature to 0.1°C resolution)
- ✅ Sensor reading ranges match RoverState ranges
- ✅ SensorSuite.read_all() returns complete telemetry frame
- ⚠️ **Edge cases:**
  - Noise stddev = 0 (should return clean values)
  - Very large drift rates
  - Negative time deltas (dt < 0)
  - Extreme rover state values (sensors should still function)

**Priority:** HIGH (telemetry quality depends on this)

---

#### 3. Environment (`meridian3/src/simulator/environment.py`)
**What it does:** Models terrain, hazards, and Mars orbital mechanics

**Components:**
- `TerrainModel`: Slope, surface type, roughness, dust
- `HazardSystem`: Dust devils, radiation spikes, slip events
- `OrbitalMechanics`: Solar angle, day/night cycles
- `Environment`: Main orchestrator

**Tests needed:**
- ✅ Terrain power multiplier calculation
- ✅ Solar angle calculation (0° at midnight, 90° at noon)
- ✅ Solar power calculation (0W at night, max during day)
- ✅ Battery charge/discharge based on power balance
- ✅ Thermal dynamics (CPU, battery, motor, chassis temps)
- ✅ Hazard event generation (Poisson process)
- ✅ Hazard effects application (dust devil, radiation, slip)
- ✅ Day/night cycle (local_time wraps at sol boundary)
- ⚠️ **Edge cases:**
  - Solar angle exactly 0° or 90°
  - Battery SoC reaching 0% or 100%
  - Extreme hazard severities (0.0 to 1.0)
  - Negative power consumption
  - Temperature equilibration at edges

**Priority:** HIGH (realistic simulation depends on this)

---

#### 4. Generator (`meridian3/src/simulator/generator.py`)
**What it does:** Main simulation loop that orchestrates all components

**Tests needed:**
- ✅ Timestep management
- ✅ Frame generation (yield pattern)
- ✅ Max duration termination
- ✅ Frame metadata (timestamp, frame_id, sol, local_time)
- ✅ Motion physics (position update based on velocity and heading)
- ✅ Automatic behaviors (low battery stop, science activation)
- ✅ Random seed reproducibility
- ✅ reset() function
- ⚠️ **Edge cases:**
  - Zero timestep (should error)
  - Very large timestep (> 1 hour)
  - Zero duration
  - Infinite duration (max_duration=None)
  - run_mission() memory usage for long durations

**Priority:** CRITICAL (heart of simulation)

---

### PIPELINE COMPONENTS

#### 5. Packetizer (`meridian3/src/pipeline/packetizer.py`)
**What it does:** Encodes telemetry frames into transmission packets

**Tests needed:**
- ✅ Packet structure (header, payload, footer)
- ✅ Sequence number incrementing
- ✅ Checksum calculation
- ✅ Checksum verification (valid packets)
- ✅ Checksum verification (corrupted packets)
- ✅ Priority calculation based on frame content
- ✅ Packet size estimation
- ✅ Statistics tracking
- ⚠️ **Edge cases:**
  - Empty frame (minimal data)
  - Very large frame (all fields populated)
  - Missing frame fields (timestamp, frame_id)
  - Counter overflow (after millions of packets)
  - Different encoding modes

**Priority:** HIGH (critical for pipeline)

---

#### 6. Corruptor (`meridian3/src/pipeline/corruptor.py`)
**What it does:** Simulates realistic transmission errors

**Tests needed:**
- ✅ Packet loss rate (verify actual rate matches configured rate)
- ✅ Field corruption rate (verify actual rate matches configured rate)
- ✅ Timing jitter application
- ✅ Field removal (None values)
- ✅ Field distortion (numeric value changes)
- ✅ Type errors (string "CORRUPTED")
- ✅ Corruption metadata in footer
- ✅ Deep copy (original packet unchanged)
- ✅ Statistics tracking
- ⚠️ **Edge cases:**
  - Corruption rate = 0% (no changes)
  - Corruption rate = 100% (all fields corrupted)
  - Packet loss rate = 100% (always None)
  - Very large jitter stddev
  - Corrupting already corrupted packet
  - Random seed reproducibility

**Priority:** HIGH (testing robustness of cleaning)

---

#### 7. Cleaner (`meridian3/src/pipeline/cleaner.py`)
**What it does:** Validates and repairs corrupted telemetry

**Tests needed:**
- ✅ Lost packet handling (None input)
- ✅ Checksum validation
- ✅ Field-by-field cleaning
- ✅ None value interpolation
- ✅ Type error handling
- ✅ Range clamping
- ✅ Rate-of-change limiting
- ✅ Interpolation from history
- ✅ Lost frame interpolation
- ✅ Quality assessment (high/medium/low)
- ✅ Repair metadata tracking
- ✅ History management
- ⚠️ **Edge cases:**
  - First frame (no history)
  - All packets lost (no data to interpolate)
  - Fields not in VALID_RANGES or RATE_LIMITS
  - Extreme values (infinity, NaN)
  - Large gaps (10+ consecutive lost packets)
  - Boundary values (exactly at min/max range)

**Priority:** CRITICAL (data quality depends on this)

---

#### 8. Anomaly Detector (`meridian3/src/pipeline/anomalies.py`)
**What it does:** Detects threshold, derivative, and statistical anomalies

**Tests needed:**
- ✅ Threshold detection (low/high warning/critical)
- ✅ Derivative detection (rate of change)
- ✅ Z-score detection (statistical outliers)
- ✅ History accumulation
- ✅ Anomaly metadata structure
- ✅ Severity assignment
- ✅ Statistics tracking
- ⚠️ **Edge cases:**
  - First frame (no history for derivative/z-score)
  - Constant values (stddev = 0, can't detect z-score outliers)
  - Values at exact threshold boundaries
  - Multiple anomalies in same frame
  - Warmup period (insufficient history)
  - Very high z-score threshold (nothing detected)
  - Very low z-score threshold (everything detected)

**Priority:** HIGH (mission safety depends on this)

---

#### 9. Storage (`meridian3/src/pipeline/storage.py`)
**What it does:** Persists telemetry to SQLite database

**Tests needed:**
- ✅ Database initialization
- ✅ Table and index creation
- ✅ Frame storage
- ✅ Anomaly storage (separate table)
- ✅ Time range queries
- ✅ Latest frames query
- ✅ Anomaly queries (by severity)
- ✅ Cache hit/miss behavior
- ✅ Mission export (JSON)
- ✅ Statistics tracking
- ✅ Database file creation
- ⚠️ **Edge cases:**
  - Database file doesn't exist (should create)
  - Database file is corrupt
  - Disk full scenarios
  - Very large frames (serialization limits)
  - Concurrent access (multiple processes)
  - Query with no results
  - Export empty mission
  - Close and reopen database

**Priority:** HIGH (data persistence is critical)

---

### UTILITY COMPONENTS

#### 10. Math Helpers (`meridian3/src/utils/math_helpers.py`)
**What it does:** Common mathematical operations for simulation

**Tests needed:**
- ✅ Gaussian noise (check distribution statistics)
- ✅ Uniform noise (check distribution)
- ✅ Random walk drift (accumulation)
- ✅ Pink noise (correlation)
- ✅ Moving average smoothing
- ✅ Exponential smoothing
- ✅ Median filter (spike removal)
- ✅ Linear interpolation
- ✅ Series interpolation (gap filling)
- ✅ Clamp function
- ✅ Normalize function
- ✅ Moving stddev
- ⚠️ **Edge cases:**
  - Zero stddev/noise
  - Empty lists
  - Single-element lists
  - All None values in series
  - Window size larger than data
  - Alpha = 0 or 1 in smoothing
  - Division by zero in normalize

**Priority:** MEDIUM (utilities, but heavily used)

---

#### 11. Timing (`meridian3/src/utils/timing.py`)
**What it does:** Mission time management and conversions

**Tests needed:**
- ✅ MET to sol conversion
- ✅ MET to local time conversion
- ✅ Local time to HMS conversion
- ✅ Time formatting
- ✅ Solar elevation calculation
- ✅ Timestep validation
- ✅ Timestep recommendation
- ✅ MissionClock tick/reset
- ⚠️ **Edge cases:**
  - MET = 0 (landing)
  - Sol boundary crossing (88775 seconds)
  - Very large MET (years of mission time)
  - Negative timestep
  - Zero timestep
  - Extreme latitudes (-90°, +90°)
  - Midnight vs noon solar angles

**Priority:** MEDIUM (important but straightforward)

---

### INTEGRATION TESTS

#### 12. Simulator Integration
**What it tests:** Environment → RoverState → Sensors → Generator

**Tests needed:**
- ✅ Complete simulation run (100 frames)
- ✅ Battery discharge over time
- ✅ Thermal equilibration
- ✅ Hazard event occurrence
- ✅ Day/night cycle transitions
- ✅ Sensor noise consistency
- ✅ Frame metadata correctness

---

#### 13. Pipeline Integration
**What it tests:** Packetizer → Corruptor → Cleaner → Anomaly Detector → Storage

**Tests needed:**
- ✅ End-to-end pipeline (as in pipeline_demo.py)
- ✅ Data integrity through pipeline
- ✅ Error recovery (lost packets, corrupted fields)
- ✅ Anomaly detection on real simulated data
- ✅ Storage query correctness
- ✅ Statistics consistency across components

---

#### 14. Full System Integration
**What it tests:** Complete simulation + pipeline + storage

**Tests needed:**
- ✅ Long-running simulation (1 hour simulated time)
- ✅ Memory stability (no leaks)
- ✅ Database growth rate
- ✅ Query performance with large datasets
- ✅ Reproducibility with random seeds
- ✅ Reset and restart capability

---

## TEST PRIORITIES

### CRITICAL (Must pass before any deployment)
1. SimulationGenerator - core simulation loop
2. Cleaner - data integrity
3. Storage - data persistence
4. End-to-end pipeline integration

### HIGH (Important for correctness)
5. RoverState - state management
6. Sensors - measurement quality
7. Environment - realistic simulation
8. Packetizer - data encoding
9. Corruptor - error simulation
10. AnomalyDetector - safety monitoring

### MEDIUM (Important for quality)
11. Math helpers - utility functions
12. Timing - time management
13. Streamlit UI - user experience

### LOW (Nice to have)
14. Debug helpers
15. Documentation examples

---

## KNOWN EDGE CASES

### 1. **Empty/Null Data**
- Empty frames
- Missing fields
- None values
- Zero-length lists

### 2. **Boundary Values**
- Battery SoC exactly 0% or 100%
- Temperatures at sensor limits
- Solar angle exactly 0° or 90°
- Packet counter overflow

### 3. **Time Edge Cases**
- Mission start (t=0)
- Sol boundaries (88775 seconds)
- Very long missions (> 1 year)
- Zero or negative timesteps

### 4. **Statistical Edge Cases**
- Zero variance (constant values)
- Single data point (no statistics)
- All corrupted data
- Very sparse data (many gaps)

### 5. **Concurrency**
- Multiple readers (SQLite WAL mode)
- Database locks
- Cache invalidation

### 6. **Resource Limits**
- Memory (long simulations)
- Disk space (large databases)
- Computation time (fine timesteps)

---

## TESTING ROADMAP

### Phase 1: Setup (CURRENT)
- ✅ Read and analyze entire codebase
- ⏳ Create testing notes document
- ⏳ Set up pytest infrastructure
- ⏳ Configure test fixtures and utilities

### Phase 2: Unit Tests (Simulator)
- RoverState tests
- Sensor tests (SensorBase, IMU, Power, Thermal, Suite)
- Environment tests (Terrain, Hazards, Orbital, Environment)
- Generator tests

### Phase 3: Unit Tests (Pipeline)
- Packetizer tests
- Corruptor tests
- Cleaner tests
- AnomalyDetector tests
- Storage tests

### Phase 4: Unit Tests (Utilities)
- Math helpers tests
- Timing tests

### Phase 5: Integration Tests
- Simulator integration
- Pipeline integration
- Full system integration

### Phase 6: End-to-End Tests
- Complete mission simulation
- Performance tests
- Stress tests

### Phase 7: Documentation and Coverage
- Test coverage report
- Document findings
- Fix any issues discovered
- Final validation

---

## DEPENDENCIES AND REQUIREMENTS

### Testing Framework
- `pytest>=7.4.0` - main testing framework
- `pytest-cov>=4.1.0` - coverage reporting

### Already Installed
- `numpy>=1.24.0` - numerical operations
- `pandas>=2.0.0` - data handling (not heavily used, but available)
- `streamlit>=1.28.0` - UI framework

### Testing Utilities Needed
- Fixtures for common objects (RoverState, frames, packets)
- Mock random number generator for deterministic tests
- Temporary database for storage tests
- Performance profiling tools

---

## SUCCESS CRITERIA

### Test Coverage
- **Unit Tests:** > 90% line coverage
- **Integration Tests:** All major flows covered
- **Edge Cases:** All known edge cases tested

### Test Quality
- All tests must pass
- No flaky tests (non-deterministic failures)
- Clear test names and documentation
- Fast execution (< 60 seconds for full suite)

### Documentation
- Testing notes document (this file)
- Test coverage report
- Known issues and limitations documented
- Troubleshooting guide for common test failures

---

## NOTES FOR TROUBLESHOOTING

### Common Issues to Watch For

1. **Random seed management**
   - Tests using randomness must set seeds for reproducibility
   - Use `random.seed()` and pass random_seed parameters

2. **Floating point comparisons**
   - Use `pytest.approx()` for float comparisons
   - Define reasonable tolerances (e.g., 1e-6)

3. **Database cleanup**
   - Use temporary files or in-memory databases (`:memory:`)
   - Clean up test databases in teardown

4. **Time-dependent tests**
   - Don't rely on wall-clock time
   - Use mission elapsed time (MET)
   - Mock time if needed

5. **State accumulation**
   - Reset objects between tests
   - Use fresh instances or fixture factories

---

**END OF TESTING NOTES**
