# Appendix C: Data Cleaning & Validation

This appendix explains how corrupted telemetry is detected and repaired through validation, interpolation, and sanity checking - the critical "data quality" layer of the pipeline.

---

## Part 1: Why Data Cleaning is Essential

### The Corruption Problem

**Beginner Explanation:**
Radio transmissions from Mars aren't perfect. Sometimes data gets corrupted:
- A number becomes gibberish: `battery_soc: 75.2` → `battery_soc: "CORRUPTED"`
- A value becomes impossible: `temperature: 25°C` → `temperature: 999°C`
- An entire packet goes missing

We can't just ignore bad data! The rover's life depends on accurate monitoring. So we need to:
1. **Detect** what's wrong
2. **Repair** what we can
3. **Track** what we fixed

<details>
<summary><b>🔍 Intermediate Details: Types of Data Corruption</b></summary>

**Common corruption modes:**

1. **Packet Loss** (0-10% of packets)
   - Cause: Radio interference, terrain occlusion, cosmic rays
   - Detection: Missing sequence numbers
   - Repair: Interpolate from surrounding packets

2. **Field Corruption** (random fields set to None or garbage)
   - Cause: Bit flips during transmission
   - Detection: Type checking, range validation
   - Repair: Interpolate from history or use last known value

3. **Checksum Failures** (entire packet suspect)
   - Cause: Multiple bit errors
   - Detection: Checksum mismatch
   - Repair: Field-by-field validation, interpolation

4. **Out-of-Range Values** (physically impossible)
   - Cause: Bit corruption in numeric fields
   - Detection: Range checking against hardware limits
   - Repair: Clamp to valid range or interpolate

5. **Rate-of-Change Violations** (impossible jumps)
   - Cause: Value corruption makes it look like sudden change
   - Detection: Compare to previous value, check rate limit
   - Repair: Use previous value or interpolate

The cleaner handles **all of these** automatically!

</details>

---

## Part 2: The Cleaning Pipeline

### Five-Stage Process

**Beginner Explanation:**
When a packet arrives, the cleaner runs through five stages:

```
╔══════════════════════════════════════════════════════════════╗
║                    CLEANING PIPELINE                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Corrupted Packet                                            ║
║      │                                                       ║
║      ▼                                                       ║
║  ┌──────────────────────────────────────┐                   ║
║  │  STEP 1: Checksum Validation         │                   ║
║  │  Valid? Mark packet quality          │                   ║
║  └──────────────┬───────────────────────┘                   ║
║                 │                                            ║
║                 ▼                                            ║
║  ┌──────────────────────────────────────┐                   ║
║  │  STEP 2: Extract Telemetry           │                   ║
║  │  Pull data from packet payload       │                   ║
║  └──────────────┬───────────────────────┘                   ║
║                 │                                            ║
║                 ▼                                            ║
║  ┌──────────────────────────────────────┐                   ║
║  │  STEP 3: Field-by-Field Validation   │                   ║
║  │  For each field:                     │                   ║
║  │    - Check if None/missing           │                   ║
║  │    - Check data type                 │                   ║
║  │    - Check range bounds              │                   ║
║  │    - Check rate of change            │                   ║
║  └──────────────┬───────────────────────┘                   ║
║                 │                                            ║
║                 ▼                                            ║
║  ┌──────────────────────────────────────┐                   ║
║  │  STEP 4: Repair Attempts             │                   ║
║  │  - Interpolate from history          │                   ║
║  │  - Clamp to valid range              │                   ║
║  │  - Use last known good value         │                   ║
║  └──────────────┬───────────────────────┘                   ║
║                 │                                            ║
║                 ▼                                            ║
║  ┌──────────────────────────────────────┐                   ║
║  │  STEP 5: Add Quality Metadata        │                   ║
║  │  Tag repaired fields & confidence    │                   ║
║  └──────────────┬───────────────────────┘                   ║
║                 │                                            ║
║                 ▼                                            ║
║  Clean Telemetry Frame                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

<details>
<summary><b>🔍 Intermediate Details: Design Philosophy</b></summary>

The cleaner balances two competing goals:

**1. Data Fidelity**: Don't change valid data
- Over-aggressive cleaning can hide real anomalies
- Example: High temperature might be real equipment failure, not corruption

**2. Data Usability**: Make corrupted data useful
- Leaving garbage values breaks downstream analysis
- Example: `None` values crash plotting code

**Our strategy:**
- **Conservative repairs**: Only fix obvious corruption
- **Metadata tracking**: Record what was changed and why
- **Quality labels**: Mark data as "high", "medium", "low", or "interpolated"
- **Transparency**: Downstream systems can see repair history

This follows the principle: *"Clean enough to be usable, but preserve truth"*

</details>

---

## Part 3: Valid Ranges - Physical Limits

### Range Checking

**Beginner Explanation:**
Every sensor has physical limits. A battery can't be 150% charged, and Mars temperatures don't reach 1000°C. We define valid ranges for each field:

```python
VALID_RANGES = {
    # Power system ranges
    'battery_voltage': (20.0, 35.0),     # Lithium-ion cell limits
    'battery_current': (-10.0, 10.0),    # Charge/discharge range
    'battery_soc': (0.0, 100.0),         # State of charge percentage
    'battery_temp': (-40.0, 60.0),       # Safe operating temperature

    # IMU ranges
    'roll': (-180.0, 180.0),             # Rotation limits
    'pitch': (-180.0, 180.0),
    'heading': (0.0, 360.0),             # Compass bearing

    # Thermal ranges
    'motor_temp': (-100.0, 80.0),        # Mars ambient to max operating
    'electronics_temp': (-100.0, 70.0),

    # Position
    'x': (-10000.0, 10000.0),            # Mission area bounds (meters)
    'y': (-10000.0, 10000.0),
    'z': (-1000.0, 1000.0),              # Elevation range
    'velocity': (0.0, 2.0),              # Max rover speed m/s
}
```

**File location:** `meridian3/src/pipeline/cleaner.py:139-163`

<details>
<summary><b>🔍 Intermediate Details: Where Ranges Come From</b></summary>

Valid ranges are derived from:

**Hardware specifications:**
- Battery voltage (20-35V): Li-ion cells have ~3.0-4.2V per cell, 8 cells in series = 24-33.6V nominal, allow margin
- Battery SoC (0-100%): Physical definition of state of charge
- Motor temp (up to 80°C): Manufacturer rating for stepper motors

**Environmental constraints:**
- Mars surface temperature: -125°C to +20°C typical
- Elevation range: Based on landing site topography
- Velocity: Rover design limit (~5 cm/s = 0.05 m/s nominal, 2 m/s is safety margin)

**Operational limits:**
- Battery temp (-40 to 60°C): Heaters maintain above -40°C, charging disabled above 45°C
- CPU temp (-40 to 85°C): Electronics operating range, thermal shutdown at 85°C

**Why margins matter:**
Values near limits trigger warnings but aren't necessarily errors. We use two-tier limits:
- **Valid range**: Physically possible (for cleaning)
- **Nominal range**: Operationally safe (for anomaly detection)

Example for battery SoC:
- Physically possible: 0-100%
- Operationally nominal: 20-90%
- Warning threshold: <30%
- Critical threshold: <15%

</details>

---

## Part 4: Interpolation - Filling Gaps

### How Interpolation Works

**Beginner Explanation:**
When a value is missing or corrupted, we can estimate it from nearby good values. It's like filling in a missing frame in a video by looking at the frames before and after.

**Linear interpolation example:**
```
Time 100: battery_soc = 80.0%  (good)
Time 101: battery_soc = ???    (corrupted!)
Time 102: battery_soc = 78.0%  (good)

Estimate: battery_soc ≈ 79.0%  (halfway between 80 and 78)
```

<details>
<summary><b>🔍 Intermediate Details: Interpolation Algorithm</b></summary>

The cleaner implements **linear interpolation** between surrounding points:

```python
def _interpolate_field(self, field_name: str, timestamp: float) -> Optional[float]:
    """Interpolate missing field value from history."""
    if len(self.frame_history) < 2:
        return None  # Need at least 2 points

    # Find two surrounding points with valid data
    values_with_time = []
    for frame in self.frame_history:
        if field_name in frame['data']:
            val = frame['data'][field_name]
            if isinstance(val, (int, float)):
                values_with_time.append((frame['timestamp'], val))

    if len(values_with_time) < 2:
        return None

    # Use last two points for linear interpolation
    t1, v1 = values_with_time[-2]
    t2, v2 = values_with_time[-1]

    # Linear interpolation: v = v1 + (v2-v1) * (t-t1)/(t2-t1)
    if t2 != t1:
        slope = (v2 - v1) / (t2 - t1)
        interpolated = v1 + slope * (timestamp - t1)
        return interpolated
    else:
        return v2  # Same timestamp - use last value
```

**File location:** `meridian3/src/pipeline/cleaner.py:421-467`

**When interpolation works well:**
- Values change smoothly (battery SoC, temperature)
- Short gaps (1-2 missing frames)
- Stable conditions (not during rapid maneuvers)

**When interpolation fails:**
- Discrete states (boolean flags)
- Long gaps (no recent context)
- Rapid changes (during thruster firing)

**Alternatives considered:**
- **Last-value hold**: Just use previous value (simpler but less accurate)
- **Spline interpolation**: Smoother curves (more complex, needs more history)
- **Kalman filtering**: Optimal estimation (requires physics model)

We chose linear interpolation as a good balance of simplicity and accuracy.

</details>

---

## Part 5: Field-by-Field Cleaning

### The Cleaning Logic

**Beginner Explanation:**
Every field goes through a series of checks. If it fails a check, we try to repair it:

```python
def _clean_field(self, field_name: str, value: Any, timestamp: float):
    """Clean a single telemetry field."""

    # Case 1: Value is None or missing
    if value is None:
        interpolated = self._interpolate_field(field_name, timestamp)
        if interpolated is not None:
            return interpolated, True, "interpolation_none"
        else:
            default = self._get_default_value(field_name)
            return default, True, "default_value"

    # Case 2: Value is wrong type (string corruption)
    if not isinstance(value, (int, float)):
        interpolated = self._interpolate_field(field_name, timestamp)
        if interpolated is not None:
            return interpolated, True, "interpolation_type_error"
        else:
            default = self._get_default_value(field_name)
            return default, True, "default_type_error"

    # Case 3: Value is extreme (infinity, NaN)
    if not (-1e6 < value < 1e6):
        interpolated = self._interpolate_field(field_name, timestamp)
        # ... (similar repair logic)

    # Case 4: Value violates range constraints
    if field_name in self.VALID_RANGES:
        min_val, max_val = self.VALID_RANGES[field_name]
        if not (min_val <= value <= max_val):
            # Out of range - clamp to bounds
            clamped = max(min_val, min(max_val, value))
            return clamped, True, "range_clamp"

    # Case 5: Value has impossible rate of change
    if field_name in self.RATE_LIMITS and len(self.frame_history) > 0:
        last_value = self.frame_history[-1]['data'][field_name]
        last_time = self.frame_history[-1]['timestamp']
        dt = timestamp - last_time

        if dt > 0:
            rate = abs(value - last_value) / dt
            max_rate = self.RATE_LIMITS[field_name]

            if rate > max_rate:
                # Rate too high - likely corrupted
                interpolated = self._interpolate_field(field_name, timestamp)
                # ... (repair logic)

    # Value is clean - pass through unchanged
    return value, False, "none"
```

**File location:** `meridian3/src/pipeline/cleaner.py:320-419`

<details>
<summary><b>🔍 Intermediate Details: Rate-of-Change Limits</b></summary>

Some corruption creates values within valid range but changing impossibly fast:

```python
RATE_LIMITS = {
    'battery_soc': 2.0,          # Can't change more than 2%/sec
    'battery_temp': 5.0,         # 5°C/sec is very fast
    'battery_voltage': 1.0,      # Voltage shouldn't jump quickly
}
```

**File location:** `meridian3/src/pipeline/cleaner.py:166-174`

**Example scenario:**
```
Time 100: battery_soc = 75.0%
Time 101: battery_soc = 95.0%  (20% increase in 1 second!)

Rate = |95.0 - 75.0| / 1.0 = 20 %/sec
Limit = 2 %/sec
20 > 2 → VIOLATION!

Action: Interpolate or use last value (75.0%)
```

**Why this matters:**
Physical systems have **thermal inertia** and **capacitance**:
- Battery SoC changes at ~1-5% per minute (not per second) depending on load
- Temperature changes limited by heat capacity and conductivity
- Voltage changes limited by capacitor discharge rates

**Rate limits come from physics:**
```
Battery discharge rate:
  Capacity: 100 Ah
  Max current: 10 A
  Max rate: 10 A / 100 Ah = 0.1 per hour = 0.1/3600 per second ≈ 0.003%/sec

We use 2%/sec as a safety margin (600x faster than max physical rate)
```

This catches corruption while allowing real transients (motor startup, etc.)

</details>

---

## Part 6: Quality Metadata

### Tracking Repairs

**Beginner Explanation:**
The cleaner doesn't just fix data - it tracks *what* was fixed and *how*. This creates a "repair receipt":

```python
clean_frame = {
    'timestamp': 123.4,
    'frame_id': 100,
    'data': {
        'battery_soc': 75.0,      # Repaired!
        'battery_voltage': 28.3,  # Clean
        'cpu_temp': 35.4,         # Clean
    },
    'metadata': {
        'quality': 'medium',  # Some repairs made
        'checksum_valid': False,
        'repairs': [
            {
                'field': 'battery_soc',
                'method': 'interpolation_none',
                'original': None,
                'repaired': 75.0
            }
        ],
        'warnings': []
    }
}
```

<details>
<summary><b>🔍 Intermediate Details: Quality Assessment</b></summary>

The cleaner assigns quality levels based on repair count:

```python
if repair_count > 0:
    self.stats['frames_with_repairs'] += 1
    if repair_count > 3:
        clean_frame['metadata']['quality'] = 'low'
    elif repair_count > 0:
        clean_frame['metadata']['quality'] = 'medium'
```

**File location:** `meridian3/src/pipeline/cleaner.py:306-311`

**Quality levels:**
- **high**: Checksum valid, no repairs (trustworthy)
- **medium**: Minor repairs (1-3 fields), likely accurate
- **low**: Many repairs (>3 fields), use with caution
- **interpolated**: Entire frame reconstructed from history

**Why this matters:**

Downstream systems can filter by quality:
```python
# Only use high-quality data for critical decisions
if frame['metadata']['quality'] == 'high':
    engage_thruster(frame['data']['heading'])

# Use medium-quality data with confirmation
elif frame['metadata']['quality'] == 'medium':
    if confirm_with_next_frame():
        engage_thruster(frame['data']['heading'])

# Don't use low-quality data for critical operations
else:
    wait_for_better_data()
```

**Statistics tracking:**
```python
stats = cleaner.get_statistics()
# {
#     'frames_processed': 1000,
#     'frames_with_repairs': 120,
#     'fields_repaired': 180,
#     'checksum_failures': 50,
#     'repair_rate': 0.12  # 12% of frames needed repair
# }
```

High repair rates indicate:
- Poor communication link
- Sensor failures
- Environmental interference
- Time to adjust transmission parameters

</details>

---

## Part 7: Complete Cleaning Example

### Real-World Scenario

**Beginner Explanation:**
Let's walk through a complete cleaning operation:

**Input: Corrupted Packet**
```python
corrupted_packet = {
    'header': {
        'timestamp': 456.7,
        'frame_id': 200,
        'packet_id': 198,
    },
    'payload': {
        'telemetry': {
            'battery_soc': None,        # Missing!
            'battery_voltage': 999.9,   # Out of range!
            'cpu_temp': 35.4,           # Clean
            'roll': "CORRUPTED",        # Wrong type!
            'heading': 45.2,            # Clean
        }
    },
    'footer': {
        'checksum': "bad_checksum",
        'corruption_detected': True  # Checksum failed!
    }
}
```

**Processing:**

```python
cleaner = Cleaner(history_size=10)
clean_frame = cleaner.clean_packet(corrupted_packet)
```

**Output: Cleaned Frame**
```python
{
    'timestamp': 456.7,
    'frame_id': 200,
    'data': {
        'battery_soc': 74.5,      # Interpolated from history
        'battery_voltage': 35.0,  # Clamped to max valid (35.0)
        'cpu_temp': 35.4,         # Passed through (no issues)
        'roll': 2.1,              # Interpolated from history
        'heading': 45.2,          # Passed through (no issues)
    },
    'metadata': {
        'quality': 'low',  # 3 repairs
        'checksum_valid': False,
        'repairs': [
            {
                'field': 'battery_soc',
                'method': 'interpolation_none',
                'original': None,
                'repaired': 74.5
            },
            {
                'field': 'battery_voltage',
                'method': 'range_clamp',
                'original': 999.9,
                'repaired': 35.0
            },
            {
                'field': 'roll',
                'method': 'interpolation_type_error',
                'original': "CORRUPTED",
                'repaired': 2.1
            }
        ],
        'warnings': []
    }
}
```

<details>
<summary><b>🔍 Intermediate Details: Lost Packet Handling</b></summary>

When an entire packet is lost (not just corrupted), the cleaner can interpolate the whole frame:

```python
# Packet completely lost
result = cleaner.clean_packet(None)
```

If sufficient history exists (≥2 frames), it estimates all fields:

```python
def _interpolate_lost_frame(self) -> dict:
    """Interpolate entire frame when packet is lost."""
    frame1 = self.frame_history[-2]
    frame2 = self.frame_history[-1]

    # Estimate timestamp (assume regular spacing)
    dt = frame2['timestamp'] - frame1['timestamp']
    estimated_timestamp = frame2['timestamp'] + dt

    interpolated_frame = {
        'timestamp': estimated_timestamp,
        'frame_id': -1,  # Unknown
        'data': {},
        'metadata': {
            'quality': 'interpolated',
            'warnings': ['Entire frame interpolated due to packet loss'],
        }
    }

    # For each field, extrapolate forward
    for field_name in frame2['data'].keys():
        v1 = frame1['data'][field_name]
        v2 = frame2['data'][field_name]
        # Linear extrapolation: v_next = v2 + (v2 - v1)
        interpolated_frame['data'][field_name] = v2 + (v2 - v1)

    return interpolated_frame
```

**File location:** `meridian3/src/pipeline/cleaner.py:469-523`

**Limitations:**
- Assumes constant rate of change (not always valid)
- Accumulates error with multiple consecutive losses
- Can't detect sudden events during gap

**Best practice**: Mark as low confidence, confirm with next real frame

</details>

---

## Key Takeaways

1. **Range validation** ensures values are physically possible
2. **Interpolation** fills gaps using historical context
3. **Rate-of-change limits** catch impossible jumps
4. **Quality metadata** tracks what was repaired and why
5. **Statistics** monitor overall data health

### Where to Look in the Code

- **Cleaner class**: `meridian3/src/pipeline/cleaner.py:129-595`
- **Valid ranges**: `meridian3/src/pipeline/cleaner.py:139-163`
- **Rate limits**: `meridian3/src/pipeline/cleaner.py:166-174`
- **clean_packet() method**: `meridian3/src/pipeline/cleaner.py:204-318`
- **_clean_field() method**: `meridian3/src/pipeline/cleaner.py:320-419`
- **Interpolation**: `meridian3/src/pipeline/cleaner.py:421-467`

---

**Previous:** [Appendix B: Data Packetization & Transmission](./Appendix_B_Data_Packetization.md)
**Next:** [Appendix D: Anomaly Detection](./Appendix_D_Anomaly_Detection.md)
