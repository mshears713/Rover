# Appendix A: How Sensor Data is Generated

This appendix explains how the Meridian-3 rover creates sensor data from scratch. You'll learn how the system maintains the rover's "state" (position, battery, temperature, etc.) and how sensors add realistic noise to simulate real hardware.

---

## Part 1: The Rover State - The "Source of Truth"

### What is RoverState?

**Beginner Explanation:**
Think of `RoverState` as a complete snapshot of the rover at any moment in time. It's like taking a photograph that captures *everything* about the rover: where it is, how much battery it has, what temperature its components are at, and more. This is the "perfect" or "true" state before sensors measure it.

<details>
<summary><b>🔍 Intermediate Details: The State Pattern</b></summary>

The `RoverState` class implements the **State Pattern** from software engineering. By separating *data* (what the rover IS) from *behavior* (what the rover DOES), we get:

- **Easy debugging**: Just inspect the state object to see everything
- **Reproducibility**: Save/load state for repeatable tests
- **Modularity**: State updates are independent from sensor reading

The state exists in `meridian3/src/simulator/rover_state.py:67-160`

</details>

### Code Example: RoverState Initialization

Here's how the rover state is created with default values at mission start:

```python
class RoverState:
    """Complete physical and operational state of the Meridian-3 rover."""

    def __init__(self):
        """Initialize rover state with default values representing a healthy
        rover at mission start (sol 0, just after landing)."""

        # ═══════════════════════════════════════════════════════════
        # POSITION & ORIENTATION
        # ═══════════════════════════════════════════════════════════
        self.x = 0.0          # East-West position (m)
        self.y = 0.0          # North-South position (m)
        self.z = 0.0          # Elevation relative to landing site (m)

        self.roll = 0.0       # Rotation around forward axis (-180 to +180°)
        self.pitch = 0.0      # Rotation around lateral axis (-90 to +90°)
        self.heading = 0.0    # Compass heading (0=North, 90=East)

        # ═══════════════════════════════════════════════════════════
        # POWER SYSTEM
        # ═══════════════════════════════════════════════════════════
        self.battery_voltage = 32.0      # Volts (28-36V nominal range)
        self.battery_current = 0.5       # Amperes (negative = charging)
        self.battery_soc = 85.0          # State of charge (0-100%)
        self.solar_panel_voltage = 34.0  # Volts (0-40V depending on sun)

        # ═══════════════════════════════════════════════════════════
        # THERMAL STATE
        # ═══════════════════════════════════════════════════════════
        self.cpu_temp = 25.0             # Celsius (-40 to +85 operational)
        self.battery_temp = 20.0         # Celsius (-20 to +45 safe range)
        self.motor_temp = 30.0           # Celsius (ambient to +60)
```

**File location:** `meridian3/src/simulator/rover_state.py:75-113`

<details>
<summary><b>🔍 Intermediate Details: Why These Specific Values?</b></summary>

Each default value is chosen based on real spacecraft hardware:

- **Battery Voltage (32.0V)**: Mars rovers use lithium-ion batteries. The nominal voltage of 8 cells in series is ~29-33V. We start at 32V to represent a fully charged, healthy battery.

- **Battery SoC (85.0%)**: Starting at 85% rather than 100% reflects operational reality - batteries are typically kept in the 20-80% range to maximize lifespan.

- **CPU Temp (25.0°C)**: Room temperature, representing a rover that just landed and hasn't experienced Mars's temperature extremes yet.

These values form a **safe, nominal operating point** that the simulation can deviate from.

</details>

---

## Part 2: Sensors - Adding Realistic Imperfections

### Why Do We Need Sensor Simulation?

**Beginner Explanation:**
Real sensors aren't perfect. When you measure something, the reading has small errors. A thermometer might say 25.3°C when it's actually 25.0°C. Our simulation adds these imperfections so the data looks like it came from real hardware.

<details>
<summary><b>🔍 Intermediate Details: Types of Sensor Errors</b></summary>

Real sensors exhibit several error types:

1. **Noise**: Random fluctuations (Gaussian distribution)
   - Caused by: Electronic noise, thermal noise, quantum effects
   - Example: Temperature reading varies ±0.5°C even when temperature is constant

2. **Bias**: Constant offset from true value
   - Caused by: Calibration errors, manufacturing tolerances
   - Example: Sensor always reads 0.3° higher than actual

3. **Drift**: Bias that changes slowly over time
   - Caused by: Component aging, temperature changes
   - Example: IMU drifts by 0.01° per hour of operation

4. **Quantization**: Limited precision
   - Caused by: Analog-to-Digital Converter (ADC) resolution
   - Example: 12-bit ADC can only represent 4096 distinct values

Our sensor classes implement all of these!

</details>

### Code Example: The IMU Sensor

The Inertial Measurement Unit (IMU) measures the rover's orientation (roll, pitch, heading). Here's how it works:

```python
class IMUSensor(SensorBase):
    """
    Inertial Measurement Unit - measures orientation and acceleration.

    Typical specs:
        - Gyro: ±0.1°/s noise, 0.01°/hour drift
        - Accelerometer: ±0.01 m/s² noise
        - Update rate: 10 Hz
    """

    def __init__(self):
        # Initialize with 0.1 degree standard deviation noise
        super().__init__(name="IMU", noise_stddev=0.1, bias=0.0)

    def read(self, rover_state) -> Dict[str, float]:
        """Read orientation from rover state with realistic noise."""
        return {
            'roll': self.apply_noise(rover_state.roll),
            'pitch': self.apply_noise(rover_state.pitch),
            'heading': self.apply_noise(rover_state.heading),
        }
```

**File location:** `meridian3/src/simulator/sensors.py:165-193`

<details>
<summary><b>🔍 Intermediate Details: The apply_noise() Method</b></summary>

The `apply_noise()` method combines multiple error sources:

```python
def apply_noise(self, true_value: float) -> float:
    """Apply noise, bias, and drift to a true state value."""
    # Add Gaussian random noise
    noisy_value = add_gaussian_noise(true_value, self.noise_stddev)

    # Add systematic errors
    measured = noisy_value + self.bias + self.drift

    return measured
```

**File location:** `meridian3/src/simulator/sensors.py:114-133`

This means:
- `true_value`: The perfect value from RoverState (e.g., roll = 0.0°)
- `+ noise`: Random fluctuation (e.g., ±0.1°)
- `+ bias`: Constant offset (e.g., +0.05° calibration error)
- `+ drift`: Time-varying error (e.g., +0.002° accumulated over 2 hours)

**Result**: `measured = 0.152°` instead of the true `0.0°`

The `drift` component grows over time using a random walk process:

```python
def update_drift(self, dt: float, drift_rate: float):
    """Update sensor drift based on elapsed time using random walk."""
    self.drift = random_walk_drift(self.drift, step_size=drift_rate, dt=dt)
```

This simulates how real IMUs "wander" over time and need periodic recalibration.

</details>

### Code Example: The Thermal Sensor

Temperature sensors have different characteristics than IMUs - they're noisier but don't drift as much:

```python
class ThermalSensor(SensorBase):
    """
    Temperature sensor array - monitors thermal state of subsystems.

    Typical specs:
        - Thermistor accuracy: ±0.5°C
        - Resolution: 0.1°C
        - Update rate: 1 Hz
    """

    def __init__(self):
        # Higher noise than IMU (±0.5°C)
        super().__init__(name="ThermalArray", noise_stddev=0.5, bias=0.0)

    def read(self, rover_state) -> Dict[str, float]:
        """Read temperature sensors with thermal noise."""
        return {
            'cpu_temp': self.quantize(self.apply_noise(rover_state.cpu_temp), 0.1),
            'battery_temp': self.quantize(self.apply_noise(rover_state.battery_temp), 0.1),
            'motor_temp': self.quantize(self.apply_noise(rover_state.motor_temp), 0.1),
            'chassis_temp': self.quantize(self.apply_noise(rover_state.chassis_temp), 0.1),
        }
```

**File location:** `meridian3/src/simulator/sensors.py:227-256`

<details>
<summary><b>🔍 Intermediate Details: Quantization</b></summary>

Notice the `quantize()` call? This simulates the ADC (Analog-to-Digital Converter) resolution:

```python
def quantize(self, value: float, resolution: float) -> float:
    """Simulate ADC quantization by rounding to nearest step."""
    return round(value / resolution) * resolution
```

**File location:** `meridian3/src/simulator/sensors.py:151-163`

Example:
- True temperature: `25.347°C`
- After noise: `25.812°C`
- After quantization (0.1°C resolution): `25.8°C`

This is realistic! A 12-bit ADC measuring 0-100°C has a resolution of ~0.024°C, which we approximate as 0.1°C.

</details>

---

## Part 3: Putting It Together - The Sensor Suite

### How All Sensors Work Together

**Beginner Explanation:**
The `SensorSuite` class coordinates all individual sensors. When you ask for telemetry, it reads the IMU, power sensors, and thermal sensors all at once, then packages everything into a single "frame" of data.

```python
class SensorSuite:
    """Complete sensor suite - orchestrates all individual sensors."""

    def __init__(self):
        """Initialize all sensors in the suite."""
        self.imu = IMUSensor()
        self.power = PowerSensor()
        self.thermal = ThermalSensor()

    def read_all(self, rover_state, mission_time: float) -> Dict[str, Any]:
        """Read all sensors and compile into a single telemetry frame."""

        # Update sensor drift based on elapsed time
        dt = 1.0  # 1 second between readings
        self.imu.update_drift(dt, drift_rate=0.01 / 3600)  # 0.01°/hour

        # Compile frame from all sensors
        frame = {
            'timestamp': mission_time,
            **self.imu.read(rover_state),      # Adds roll, pitch, heading
            **self.power.read(rover_state),    # Adds battery_voltage, battery_soc, etc.
            **self.thermal.read(rover_state),  # Adds cpu_temp, battery_temp, etc.
            'x': rover_state.x,
            'y': rover_state.y,
            'z': rover_state.z,
            'velocity': rover_state.velocity,
        }

        return frame
```

**File location:** `meridian3/src/simulator/sensors.py:258-300`

<details>
<summary><b>🔍 Intermediate Details: The Dictionary Unpacking Pattern</b></summary>

The `**` operator unpacks dictionaries in Python:

```python
frame = {
    'timestamp': mission_time,
    **self.imu.read(rover_state),  # Expands to: 'roll': X, 'pitch': Y, 'heading': Z
}
```

This is equivalent to:

```python
imu_data = self.imu.read(rover_state)
frame = {
    'timestamp': mission_time,
    'roll': imu_data['roll'],
    'pitch': imu_data['pitch'],
    'heading': imu_data['heading'],
}
```

**Why use unpacking?**
- More concise
- Automatically handles new fields added to sensor readings
- Common pattern in telemetry systems

</details>

### Example Telemetry Frame

Here's what a complete frame looks like after all sensors are read:

```python
{
    'timestamp': 123.4,           # Mission elapsed time (seconds)
    'roll': 2.347,                # IMU reading (with noise)
    'pitch': -1.089,              # IMU reading
    'heading': 45.231,            # IMU reading
    'battery_voltage': 28.432,    # Power sensor reading
    'battery_current': 2.134,     # Power sensor reading
    'battery_soc': 75.234,        # Power sensor reading
    'solar_voltage': 34.123,      # Power sensor reading
    'solar_current': 1.234,       # Power sensor reading
    'cpu_temp': 35.3,             # Thermal sensor (quantized)
    'battery_temp': 22.1,         # Thermal sensor
    'motor_temp': 31.4,           # Thermal sensor
    'chassis_temp': 18.7,         # Thermal sensor
    'x': 150.234,                 # Position (from state, minimal noise)
    'y': 200.567,
    'z': -2.345,
    'velocity': 0.523,
}
```

---

## Part 4: The Complete Data Generation Flow

### Step-by-Step Process

**Beginner Explanation:**
Every second of the mission, this sequence happens:

1. **Environment updates the rover state** (battery drains, temperature changes, position moves)
2. **Sensors read the state** and add realistic noise
3. **A telemetry frame is created** with all the sensor readings
4. **The frame is sent to the next stage** of the pipeline

<details>
<summary><b>🔍 Intermediate Details: The Generator Pattern</b></summary>

The simulation uses Python's generator pattern to produce frames on-demand:

```python
class SimulationGenerator:
    def generate_frames(self) -> Generator[Dict[str, Any], None, None]:
        """Main simulation loop - generates telemetry frames."""
        while True:
            # Check termination condition
            if self.max_duration and self.current_time >= self.max_duration:
                break

            # STEP 1: Update environment effects
            env_info = self.environment.update(self.timestep, self.rover)

            # STEP 2: Process commands (battery management, science activation)
            if self.rover.battery_soc < 20.0:
                self.rover.is_moving = False

            # STEP 3: Update rover physics (motion model)
            if self.rover.is_moving:
                import math
                dx = self.rover.velocity * math.cos(math.radians(self.rover.heading)) * self.timestep
                dy = self.rover.velocity * math.sin(math.radians(self.rover.heading)) * self.timestep
                self.rover.x += dx
                self.rover.y += dy

            # STEP 4: Read all sensors
            telemetry_frame = self.sensors.read_all(self.rover, self.current_time)

            # STEP 5: Add metadata
            telemetry_frame['frame_id'] = self.frame_count
            telemetry_frame['env_info'] = env_info

            # STEP 6: Yield frame to consumer
            yield telemetry_frame

            # STEP 7: Advance time
            self.current_time += self.timestep
            self.frame_count += 1
```

**File location:** `meridian3/src/simulator/generator.py:219-308`

**Why use a generator?**
- **Memory efficient**: Only one frame exists at a time, not the entire mission history
- **Streaming**: Frames can be processed as they're generated
- **Flexible**: Consumer can stop requesting frames at any time

**Usage example:**
```python
sim = SimulationGenerator(timestep=1.0, max_duration=3600)
for frame in sim.generate_frames():
    print(f"Time {frame['timestamp']}: Battery {frame['battery_soc']:.1f}%")
    # Process frame immediately, don't store entire mission in memory
```

</details>

---

## Key Takeaways

1. **RoverState** is the "ground truth" - perfect values before measurement
2. **Sensors** add realistic imperfections: noise, bias, drift, and quantization
3. **SensorSuite** coordinates all sensors to produce complete telemetry frames
4. **SimulationGenerator** orchestrates the entire process in a memory-efficient loop

### Where to Look in the Code

- **RoverState definition**: `meridian3/src/simulator/rover_state.py:67-160`
- **Sensor base class**: `meridian3/src/simulator/sensors.py:87-163`
- **IMU sensor**: `meridian3/src/simulator/sensors.py:165-193`
- **Thermal sensor**: `meridian3/src/simulator/sensors.py:227-256`
- **SensorSuite**: `meridian3/src/simulator/sensors.py:258-300`
- **Simulation loop**: `meridian3/src/simulator/generator.py:219-308`

---

**Next:** [Appendix B: Data Packetization & Transmission](./Appendix_B_Data_Packetization.md)
