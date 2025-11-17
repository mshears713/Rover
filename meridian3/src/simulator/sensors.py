"""
Sensor System - Realistic Telemetry Generation

PURPOSE:
    This module defines sensor classes that convert RoverState into realistic
    telemetry readings. Each sensor reads the true state and applies appropriate
    noise, drift, quantization, and failure modes to simulate real hardware.

THEORY:
    Real sensors are not perfect. They have:
        - Noise: Random fluctuations in readings
        - Bias: Systematic offset from true value
        - Drift: Bias that changes slowly over time
        - Quantization: Limited precision (e.g., 12-bit ADC)
        - Latency: Delay between state change and measurement
        - Failure modes: Stuck values, dropouts, saturation

    By modeling these imperfections, we create realistic training data for
    anomaly detection and give students insight into real sensor behavior.

MERIDIAN-3 STORY SNIPPET:
    "We don't measure the rover directly - we measure what the sensors tell us.
    The thermistor in the battery pack has a 0.5°C uncertainty. The IMU drifts
    by 0.1° per hour. The current sensor has 10mA resolution. These aren't bugs -
    they're the reality of spaceflight hardware. Our ground software must
    account for this."

ARCHITECTURE ROLE:
    Sensors sit between RoverState and the telemetry pipeline. They read
    clean state values and produce noisy measurements that flow into the
    packetizer.

    RoverState → Sensors → Telemetry Frames → Pipeline

    Each sensor is independent and can be tested/calibrated separately.

SENSOR SUITE DIAGRAM:

    ┌─────────────────────────────────────────────────┐
    │              SENSOR SUITE                       │
    │                                                 │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
    │  │   IMU    │  │  Power   │  │ Thermal  │     │
    │  │ (gyro+   │  │ Monitor  │  │ Sensors  │     │
    │  │  accel)  │  │          │  │          │     │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
    │       │             │             │            │
    │       └─────────────┴─────────────┘            │
    │                     │                          │
    │                     ▼                          │
    │            ┌────────────────┐                  │
    │            │ Sensor Frame   │                  │
    │            │ (combined data)│                  │
    │            └────────────────┘                  │
    └─────────────────────────────────────────────────┘

TEACHING GOALS:
    - Object-oriented sensor modeling
    - Realistic noise and error simulation
    - Base class / derived class patterns
    - Documentation of sensor specifications

DEBUGGING NOTES:
    - To test a sensor: create a stable RoverState, read repeatedly, check stats
    - To verify noise model: collect 1000 samples, plot histogram
    - To check bias/drift: read over simulated time, plot trend
    - Set noise=0 for testing other components with clean data

FUTURE EXTENSIONS:
    - Add camera sensor (image generation)
    - Add LIDAR/radar for terrain mapping
    - Implement sensor warmup periods (accuracy improves after boot)
    - Add cross-sensor correlations (vibration affects all sensors)
    - Implement sensor health degradation over mission lifetime
"""

import random
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.math_helpers import add_gaussian_noise, random_walk_drift, clamp


class SensorBase:
    """
    Base class for all rover sensors.

    Provides common functionality:
        - Noise generation
        - Bias and drift simulation
        - Quantization
        - Failure mode injection

    Derived classes implement read() method for specific sensor types.
    """

    def __init__(self, name: str, noise_stddev: float = 0.0, bias: float = 0.0):
        """
        Initialize sensor with noise and bias parameters.

        Args:
            name: Human-readable sensor identifier
            noise_stddev: Standard deviation of Gaussian noise
            bias: Constant offset added to all readings
        """
        self.name = name
        self.noise_stddev = noise_stddev
        self.bias = bias
        self.drift = 0.0  # Accumulated drift over time

    def apply_noise(self, true_value: float) -> float:
        """
        Apply noise, bias, and drift to a true state value.

        Args:
            true_value: The actual physical quantity

        Returns:
            Measured value with imperfections applied

        Teaching Note:
            Real sensors combine multiple error sources:
            - Gaussian noise: Random fluctuations from electronics
            - Bias: Constant offset (calibration error)
            - Drift: Time-varying bias (thermal effects, aging)
        """
        # Use math_helpers for consistent noise generation
        noisy_value = add_gaussian_noise(true_value, self.noise_stddev)
        measured = noisy_value + self.bias + self.drift
        return measured

    def update_drift(self, dt: float, drift_rate: float):
        """
        Update sensor drift based on elapsed time.

        Args:
            dt: Time step in seconds
            drift_rate: Drift per second (e.g., 0.001 degrees/sec for IMU)

        Teaching Note:
            Sensor drift is modeled as a random walk process.
            This captures the slow, unpredictable changes in sensor bias
            due to temperature variations, component aging, and other factors.
        """
        # Use random_walk_drift from math_helpers for realistic drift modeling
        self.drift = random_walk_drift(self.drift, step_size=drift_rate, dt=dt)

    def quantize(self, value: float, resolution: float) -> float:
        """
        Simulate ADC quantization.

        Args:
            value: Continuous input value
            resolution: Quantization step size

        Returns:
            Quantized value (rounded to nearest multiple of resolution)
        """
        return round(value / resolution) * resolution


class IMUSensor(SensorBase):
    """
    Inertial Measurement Unit - measures orientation and acceleration.

    Typical specs:
        - Gyro: ±0.1°/s noise, 0.01°/hour drift
        - Accelerometer: ±0.01 m/s² noise
        - Update rate: 10 Hz
    """

    def __init__(self):
        super().__init__(name="IMU", noise_stddev=0.1, bias=0.0)

    def read(self, rover_state) -> Dict[str, float]:
        """
        Read orientation from rover state with realistic noise.

        Args:
            rover_state: Current RoverState object

        Returns:
            Dictionary with roll, pitch, heading measurements
        """
        return {
            'roll': self.apply_noise(rover_state.roll),
            'pitch': self.apply_noise(rover_state.pitch),
            'heading': self.apply_noise(rover_state.heading),
        }


class PowerSensor(SensorBase):
    """
    Power monitoring sensor - measures voltage, current, state of charge.

    Typical specs:
        - Voltage: ±0.05V accuracy
        - Current: ±10mA resolution
        - SoC: ±2% accuracy
    """

    def __init__(self):
        super().__init__(name="PowerMonitor", noise_stddev=0.05, bias=0.0)

    def read(self, rover_state) -> Dict[str, float]:
        """
        Read power system state with measurement noise.

        Args:
            rover_state: Current RoverState object

        Returns:
            Dictionary with voltage, current, SoC measurements
        """
        return {
            'battery_voltage': self.apply_noise(rover_state.battery_voltage),
            'battery_current': self.apply_noise(rover_state.battery_current),
            'battery_soc': self.apply_noise(rover_state.battery_soc),
            'solar_voltage': self.apply_noise(rover_state.solar_panel_voltage),
            'solar_current': self.apply_noise(rover_state.solar_panel_current),
        }


class ThermalSensor(SensorBase):
    """
    Temperature sensor array - monitors thermal state of subsystems.

    Typical specs:
        - Thermistor accuracy: ±0.5°C
        - Resolution: 0.1°C
        - Update rate: 1 Hz
    """

    def __init__(self):
        super().__init__(name="ThermalArray", noise_stddev=0.5, bias=0.0)

    def read(self, rover_state) -> Dict[str, float]:
        """
        Read temperature sensors with thermal noise.

        Args:
            rover_state: Current RoverState object

        Returns:
            Dictionary with temperature measurements
        """
        return {
            'cpu_temp': self.quantize(self.apply_noise(rover_state.cpu_temp), 0.1),
            'battery_temp': self.quantize(self.apply_noise(rover_state.battery_temp), 0.1),
            'motor_temp': self.quantize(self.apply_noise(rover_state.motor_temp), 0.1),
            'chassis_temp': self.quantize(self.apply_noise(rover_state.chassis_temp), 0.1),
        }


class SensorSuite:
    """
    Complete sensor suite - orchestrates all individual sensors.

    Provides a single interface to read all telemetry at once.
    """

    def __init__(self):
        """Initialize all sensors in the suite."""
        self.imu = IMUSensor()
        self.power = PowerSensor()
        self.thermal = ThermalSensor()

    def read_all(self, rover_state, mission_time: float) -> Dict[str, Any]:
        """
        Read all sensors and compile into a single telemetry frame.

        Args:
            rover_state: Current RoverState object
            mission_time: Current mission elapsed time (seconds)

        Returns:
            Complete telemetry frame with all sensor readings
        """
        # Update sensor drift based on elapsed time
        dt = 1.0  # Assume 1 second between readings (will be parameterized later)
        self.imu.update_drift(dt, drift_rate=0.01 / 3600)  # 0.01°/hour

        # Compile frame from all sensors
        frame = {
            'timestamp': mission_time,
            **self.imu.read(rover_state),
            **self.power.read(rover_state),
            **self.thermal.read(rover_state),
            # Position is typically from GPS/odometry, less noisy than IMU
            'x': rover_state.x,
            'y': rover_state.y,
            'z': rover_state.z,
            'velocity': rover_state.velocity,
        }

        return frame


# ═══════════════════════════════════════════════════════════════
# FUTURE EXTENSION IDEAS
# ═══════════════════════════════════════════════════════════════
# class CameraSensor(SensorBase):
#     """Simulates image capture with exposure, focus, compression artifacts."""
#     pass
#
# class LIDARSensor(SensorBase):
#     """Generates point cloud data with occlusion and noise."""
#     pass
#
# def inject_fault(sensor: SensorBase, fault_type: str, duration: float):
#     """Temporarily inject sensor faults for testing anomaly detection."""
#     pass
#
# class SensorCalibration:
#     """Stores and applies calibration parameters to correct sensor bias."""
#     pass
