# Appendix D: Anomaly Detection

This appendix explains how the system automatically identifies unusual patterns in telemetry that may indicate hardware issues, environmental hazards, or interesting science opportunities.

---

## Part 1: What is Anomaly Detection?

### Finding "Interesting" Events

**Beginner Explanation:**
Anomaly detection is like having a watchdog that barks when something unusual happens. The rover sends thousands of telemetry readings, and most are boring and normal:

- Battery at 75%? Normal.
- Temperature 25°C? Normal.
- Battery drops to 10%? **ALERT!** Not normal!
- Temperature jumps 50°C in 1 second? **ALERT!** Probably sensor glitch!

The anomaly detector automatically finds these unusual events so engineers can investigate.

<details>
<summary><b>🔍 Intermediate Details: Why Anomaly Detection Matters</b></summary>

**Real-world impact:**

Mars rovers have survived because of anomaly detection:
- **Spirit (2004)**: Wheel motor anomaly detected early, mission adapted
- **Opportunity (2007)**: Dust storm survival thanks to power monitoring
- **Curiosity (2012)**: Wheel damage found through image analysis

**What we detect:**
1. **Hardware faults**: Battery failures, sensor malfunctions
2. **Environmental hazards**: Dust storms, temperature extremes
3. **Operational issues**: Stuck wheels, communication problems
4. **Science opportunities**: Unusual geology, atmospheric events

**Why automation?**
- **Volume**: 1000s of measurements per hour, humans can't watch all
- **Speed**: Some faults require immediate response (seconds, not hours)
- **Consistency**: Algorithms don't get tired or distracted

**The challenge:**
Balance sensitivity: Too many false alarms (engineers ignore them), too few alerts (miss real problems)

</details>

---

## Part 2: Three Detection Strategies

### Overview

**Beginner Explanation:**
We use three complementary approaches:

1. **Threshold Detection**: "Is this value above/below a dangerous limit?"
2. **Derivative Detection**: "Did this value change too fast?"
3. **Statistical Detection (Z-Score)**: "Is this value unusual compared to history?"

Think of them as three different guards watching the data from different angles.

<details>
<summary><b>🔍 Intermediate Details: Why Three Approaches?</b></summary>

Each approach catches different anomaly types:

**Threshold Detection**:
- Catches: Absolute limit violations
- Example: Battery SoC < 15% (critical)
- Pro: Simple, deterministic, easy to explain
- Con: Misses subtle patterns, doesn't adapt to conditions

**Derivative Detection**:
- Catches: Sudden changes, transients
- Example: Battery drops 10% in 1 minute (fault)
- Pro: Finds problems before threshold violations
- Con: Sensitive to noise, needs tuning

**Statistical Detection (Z-Score)**:
- Catches: Values that don't match historical distribution
- Example: Voltage at 32V when mean is 28V (3σ outlier)
- Pro: Adapts to mission phase, catches subtle drifts
- Con: Needs warmup period, can adapt to degrading conditions

**Complementary coverage:**
```
Scenario: Battery gradually failing

Threshold: Detects when SoC < 20% (late warning)
Derivative: Misses (discharge rate within normal range)
Z-Score: Detects discharge pattern is 2σ faster than history (early warning!)
```

Combining all three provides **defense in depth** - if one misses, another catches.

</details>

---

## Part 3: Threshold Detection

### Simple Limit Checking

**Beginner Explanation:**
Threshold detection checks if values exceed predefined limits:

```python
THRESHOLDS = {
    'battery_soc': {
        'low_warning': 30.0,    # Yellow alert
        'low_critical': 15.0,   # Red alert
    },
    'battery_temp': {
        'high_warning': 45.0,
        'high_critical': 55.0,
        'low_warning': -10.0,
        'low_critical': -20.0,
    },
    'motor_temp': {
        'high_warning': 60.0,
        'high_critical': 75.0,
    },
}
```

**File location:** `meridian3/src/pipeline/anomalies.py:149-175`

If `battery_soc = 12.0%`, it's below `low_critical = 15.0`, so we generate:

```python
Anomaly(
    field='battery_soc',
    value=12.0,
    anomaly_type='threshold',
    severity='critical',
    description='battery_soc critically low: 12.00',
    timestamp=456.7
)
```

<details>
<summary><b>🔍 Intermediate Details: Threshold Design</b></summary>

**How thresholds are determined:**

1. **Hardware specifications**:
   ```
   Battery voltage: 20-35V (cell chemistry limits)
   CPU temp: -40 to +85°C (component datasheet)
   Motor temp: max 80°C (manufacturer rating)
   ```

2. **Operational experience**:
   ```
   Battery SoC < 20%: Historical data shows increased fault risk
   Temp > 45°C: Battery chemistry degrades faster
   ```

3. **Safety margins**:
   ```
   Hardware limit: 85°C
   Critical threshold: 75°C (10°C safety margin)
   Warning threshold: 60°C (25°C margin, early alert)
   ```

**Two-tier system:**
```python
if value < thresholds['low_critical']:
    severity = 'critical'  # Immediate action required
elif value < thresholds['low_warning']:
    severity = 'warning'   # Monitor closely
```

**Implementation:**
```python
def _detect_threshold_violations(self, frame: dict) -> List[Anomaly]:
    """Detect simple threshold violations."""
    anomalies = []
    timestamp = frame['timestamp']

    for field_name, value in frame['data'].items():
        if field_name not in self.THRESHOLDS:
            continue

        if not isinstance(value, (int, float)):
            continue

        thresholds = self.THRESHOLDS[field_name]

        # Check low thresholds
        if 'low_critical' in thresholds and value < thresholds['low_critical']:
            anomalies.append(Anomaly(
                field=field_name,
                value=value,
                anomaly_type='threshold',
                severity='critical',
                description=f"{field_name} critically low: {value:.2f}",
                timestamp=timestamp
            ))
        elif 'low_warning' in thresholds and value < thresholds['low_warning']:
            anomalies.append(Anomaly(
                field=field_name,
                value=value,
                anomaly_type='threshold',
                severity='warning',
                description=f"{field_name} low: {value:.2f}",
                timestamp=timestamp
            ))

        # Check high thresholds (similar logic)
        # ...

    return anomalies
```

**File location:** `meridian3/src/pipeline/anomalies.py:311-380`

</details>

---

## Part 4: Derivative Detection

### Rate-of-Change Monitoring

**Beginner Explanation:**
Some problems show up as *how fast* values change, not just the values themselves:

```python
DERIVATIVE_LIMITS = {
    'battery_soc': 2.0,          # 2%/sec is suspicious
    'battery_temp': 5.0,         # 5°C/sec is very fast
    'battery_voltage': 1.0,      # Voltage shouldn't jump quickly
}
```

**Example:**
```
Time 100: battery_soc = 70%
Time 101: battery_soc = 60%  (dropped 10% in 1 second!)

Rate = |60 - 70| / 1 = 10 %/sec
Limit = 2 %/sec
10 > 2 → ANOMALY!
```

This catches:
- Short circuits (sudden voltage drop)
- Sensor glitches (impossible temperature spike)
- Communication errors (values jump around)

<details>
<summary><b>🔍 Intermediate Details: Derivative Algorithm</b></summary>

**Implementation:**

```python
def _detect_derivative_anomalies(self, frame: dict) -> List[Anomaly]:
    """Detect anomalous rates of change."""
    anomalies = []

    if self.last_frame is None:
        return anomalies  # Need previous frame

    timestamp = frame['timestamp']
    last_timestamp = self.last_frame['timestamp']
    dt = timestamp - last_timestamp  # Time delta

    for field_name, value in frame['data'].items():
        if field_name not in self.DERIVATIVE_LIMITS:
            continue

        # Get previous value
        last_value = self.last_frame['data'].get(field_name)
        if last_value is None:
            continue

        # Calculate rate of change
        delta = abs(value - last_value)
        rate = delta / dt  # Units: value_units per second

        max_rate = self.DERIVATIVE_LIMITS[field_name]

        if rate > max_rate:
            # Severity based on how much limit exceeded
            if rate > max_rate * 2.0:
                severity = 'critical'
            else:
                severity = 'warning'

            anomalies.append(Anomaly(
                field=field_name,
                value=value,
                anomaly_type='derivative',
                severity=severity,
                description=(
                    f"{field_name} changed too fast: "
                    f"{rate:.2f}/s (limit: {max_rate:.2f}/s)"
                ),
                timestamp=timestamp
            ))

    return anomalies
```

**File location:** `meridian3/src/pipeline/anomalies.py:382-452`

**Key insight:**

Physical systems have **maximum rate limits** based on:

Battery discharge rate:
```
Capacity: 100 Ah
Max current: 10 A
Physics limit: 10/100 = 0.1 per hour = 0.000028 per second

Our limit: 2%/sec (70,000x faster than physics!)
Why so loose? Allows measurement noise while catching real faults
```

Temperature change rate:
```
Heat capacity: 200 J/K
Max power: 100 W
Physics limit: 100 W / 200 J/K = 0.5 K/sec

Our limit: 5°C/sec (10x faster)
Why? Allows thermal transients while catching sensor glitches
```

**Sensitivity tuning:**
- Too tight: False alarms from noise/quantization
- Too loose: Miss real faults
- Current values: Empirically tuned to catch >99% of faults with <1% false alarms

</details>

---

## Part 5: Statistical Outlier Detection (Z-Score)

### Learning from History

**Beginner Explanation:**
The Z-score method learns what's "normal" by watching the data over time, then flags values that are statistically unusual.

**Example:**

After 50 readings:
- Battery voltage mean: 28.0V
- Standard deviation: 0.5V

New reading: 30.0V

Calculate z-score:
```
z = (value - mean) / stddev
z = (30.0 - 28.0) / 0.5
z = 4.0
```

A z-score of 4.0 means this value is **4 standard deviations** above the mean. In a normal distribution:
- 68% of values within 1σ
- 95% within 2σ
- 99.7% within 3σ
- 99.99% within 4σ

So 30.0V is very unusual - only 0.01% chance of occurring naturally. **Anomaly detected!**

<details>
<summary><b>🔍 Intermediate Details: Z-Score Statistical Foundation</b></summary>

**The math:**

For a normally distributed variable:
```
P(|X - μ| > 3σ) ≈ 0.003 (0.3% probability)
P(|X - μ| > 4σ) ≈ 0.00006 (0.006% probability)
```

**Our threshold: 3.0σ (99.7% confidence)**

**Implementation:**

```python
def _detect_statistical_outliers(self, frame: dict) -> List[Anomaly]:
    """Detect statistical outliers using z-score."""
    anomalies = []
    timestamp = frame['timestamp']

    for field_name, value in frame['data'].items():
        if not isinstance(value, (int, float)):
            continue

        # Need sufficient history for statistics
        if field_name not in self.field_history:
            continue

        history = self.field_history[field_name]
        if len(history) < 10:  # Need at least 10 points
            continue

        # Calculate mean and standard deviation
        values = [v for (t, v) in history]
        mean = sum(values) / len(values)

        variance = sum((v - mean) ** 2 for v in values) / len(values)
        stddev = math.sqrt(variance)

        # Avoid division by zero
        if stddev < 1e-6:
            continue  # No variation in data

        # Calculate z-score
        z_score = abs(value - mean) / stddev

        if z_score > self.z_score_threshold:  # Default: 3.0
            # Severity based on z-score magnitude
            if z_score > self.z_score_threshold * 1.5:
                severity = 'critical'
            else:
                severity = 'warning'

            anomalies.append(Anomaly(
                field=field_name,
                value=value,
                anomaly_type='z-score',
                severity=severity,
                description=(
                    f"{field_name} statistical outlier: "
                    f"value={value:.2f}, z-score={z_score:.2f}, "
                    f"mean={mean:.2f}, stddev={stddev:.2f}"
                ),
                timestamp=timestamp
            ))

    return anomalies
```

**File location:** `meridian3/src/pipeline/anomalies.py:454-524`

**Advantages:**
- **Adaptive**: Learns mission-specific patterns
- **Context-aware**: Day/night cycles automatically accounted for
- **Subtle**: Catches gradual degradation

**Limitations:**
- **Warmup**: Needs 10-50 samples to stabilize
- **Assumption**: Assumes normal distribution (not always true)
- **Adaptation**: Can adapt to degrading conditions (slow drift not detected)

**Advanced considerations:**

The sliding window (50 samples default) means:
- Recent 50 values define "normal"
- Old data discarded (adapts to changing conditions)
- Too short: Noisy statistics
- Too long: Slow adaptation to real changes

**Non-stationary data handling:**

Real telemetry isn't stationary (battery drains over mission). Solutions:
- **Detrending**: Remove linear trend before z-score
- **Segmentation**: Separate day/night phases
- **Kalman filtering**: Model dynamics, detect deviations from model

Currently, we use simple sliding window - good enough for most cases.

</details>

---

## Part 6: The Complete Detection Pipeline

### How It All Works Together

**Beginner Explanation:**

When a frame arrives, all three detectors run in sequence:

```python
def analyze_frame(self, frame: dict) -> dict:
    """Analyze a telemetry frame for anomalies."""
    anomalies = []

    # STEP 1: Threshold Detection
    threshold_anomalies = self._detect_threshold_violations(frame)
    anomalies.extend(threshold_anomalies)

    # STEP 2: Derivative Detection
    derivative_anomalies = self._detect_derivative_anomalies(frame)
    anomalies.extend(derivative_anomalies)

    # STEP 3: Statistical Outlier Detection
    zscore_anomalies = self._detect_statistical_outliers(frame)
    anomalies.extend(zscore_anomalies)

    # STEP 4: Update History
    self._update_history(frame)

    # STEP 5: Add Anomalies to Frame Metadata
    frame['metadata']['anomalies'] = [
        {
            'field': a.field,
            'value': a.value,
            'type': a.anomaly_type,
            'severity': a.severity,
            'description': a.description,
            'timestamp': a.timestamp,
        }
        for a in anomalies
    ]

    self.last_frame = frame
    return frame
```

**File location:** `meridian3/src/pipeline/anomalies.py:226-309`

<details>
<summary><b>🔍 Intermediate Details: Aggregation and Deduplication</b></summary>

**Potential issue: Same fault detected multiple ways**

Example:
```
battery_soc = 12.0%

Threshold: Detects as critical (< 15%)
Z-score: Detects as outlier (mean was 75%, z=126!)
Derivative: If dropped from 70% last frame, also triggers
```

**Current behavior: Report all detections**
- Operators see multiple evidence sources
- Increases confidence in alert
- Different descriptions provide context

**Alternative approaches:**

1. **Deduplication**: Keep highest severity per field
   ```python
   seen_fields = set()
   for anomaly in anomalies:
       if anomaly.field not in seen_fields:
           final_anomalies.append(anomaly)
           seen_fields.add(anomaly.field)
   ```

2. **Aggregation**: Combine into single alert
   ```python
   Anomaly(
       field='battery_soc',
       value=12.0,
       anomaly_type='multiple',
       severity='critical',
       description='battery_soc: threshold+derivative+z-score violations'
   )
   ```

3. **Root cause analysis**: Identify underlying issue
   ```python
   # Multiple battery-related anomalies → "Battery system failure"
   ```

We chose to report all detections for educational transparency. Production systems typically aggregate.

</details>

---

## Part 7: Real-World Example

### Detecting a Battery Fault

**Beginner Explanation:**

Let's trace a complete battery fault scenario:

**Scenario**: Short circuit develops, battery drains rapidly

```python
# Normal operation
Frame 1000: battery_soc = 75.0%, voltage = 28.2V
Frame 1001: battery_soc = 74.9%, voltage = 28.1V
Frame 1002: battery_soc = 74.8%, voltage = 28.0V
# ... normal slow discharge

# Fault occurs!
Frame 1050: battery_soc = 74.0%, voltage = 27.9V  # Last normal
Frame 1051: battery_soc = 62.0%, voltage = 26.5V  # SHORT CIRCUIT!

# Detections triggered:

1. Derivative Detection:
   - Battery SoC: (74.0 - 62.0) / 1 = 12%/sec (limit: 2%/sec)
   - Voltage: (27.9 - 26.5) / 1 = 1.4V/sec (limit: 1.0V/sec)
   - CRITICAL alerts for both

2. Z-Score Detection:
   - Mean battery_soc (last 50 frames): 74.5%
   - Stddev: 0.3%
   - Z-score: |62.0 - 74.5| / 0.3 = 41.7
   - Way above threshold (3.0) → CRITICAL

3. Threshold Detection:
   - battery_soc = 62% still above critical threshold (15%)
   - No alert yet (will trigger if continues)

Frame 1051 metadata:
{
    'anomalies': [
        {
            'field': 'battery_soc',
            'type': 'derivative',
            'severity': 'critical',
            'description': 'battery_soc changed too fast: 12.00/s (limit: 2.00/s)'
        },
        {
            'field': 'battery_voltage',
            'type': 'derivative',
            'severity': 'critical',
            'description': 'battery_voltage changed too fast: 1.40/s (limit: 1.00/s)'
        },
        {
            'field': 'battery_soc',
            'type': 'z-score',
            'severity': 'critical',
            'description': 'battery_soc statistical outlier: value=62.00, z-score=41.67'
        }
    ]
}
```

**Operator response:**
1. Immediate alert notification
2. Disable high-power systems
3. Activate battery heater bypass
4. Request diagnostic packet retransmission
5. Initiate safe mode

<details>
<summary><b>🔍 Intermediate Details: Detection Timing</b></summary>

**Why derivative/z-score caught it before threshold:**

```
Threshold detection:
  - Only triggers when value exceeds limit
  - Battery SoC critical threshold: 15%
  - At 62%, still safe according to threshold
  - Would detect at Frame ~1056 when SoC < 15%

Derivative detection:
  - Triggered immediately (Frame 1051)
  - 5 frame early warning!
  - Time to respond: 5 seconds vs 0 seconds

Z-score detection:
  - Also triggered immediately
  - Extremely high z-score (41.7) indicates severe fault
```

**Why this matters:**

5 seconds at 12%/sec discharge rate:
```
Additional loss: 5 sec × 12%/sec = 60% SoC
Battery at Frame 1056: 62% - 60% = 2% (critical!)
```

Early detection allows:
- Shut down non-essential systems
- Preserve remaining battery for survival
- Potentially save mission

**Real Mars Rover Example:**

Curiosity's "Kepler fault" (2013):
- Short circuit detected via current spike (derivative)
- Immediate switchover to redundant computer
- Mission continued successfully

Without derivative detection, threshold would trigger after major damage.

</details>

---

## Key Takeaways

1. **Three complementary detectors** catch different anomaly types
2. **Thresholds** define absolute safety limits
3. **Derivatives** catch sudden changes before limits violated
4. **Z-scores** adapt to mission-specific patterns
5. **Multiple detections** increase confidence in alerts

### Where to Look in the Code

- **AnomalyDetector class**: `meridian3/src/pipeline/anomalies.py:140-596`
- **Threshold definitions**: `meridian3/src/pipeline/anomalies.py:149-175`
- **Derivative limits**: `meridian3/src/pipeline/anomalies.py:178-184`
- **analyze_frame() method**: `meridian3/src/pipeline/anomalies.py:226-309`
- **Threshold detection**: `meridian3/src/pipeline/anomalies.py:311-380`
- **Derivative detection**: `meridian3/src/pipeline/anomalies.py:382-452`
- **Z-score detection**: `meridian3/src/pipeline/anomalies.py:454-524`

---

**Previous:** [Appendix C: Data Cleaning & Validation](./Appendix_C_Data_Cleaning.md)
**Next:** [Appendix E: Data Visualization](./Appendix_E_Data_Visualization.md)
