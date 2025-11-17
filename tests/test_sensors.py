"""
Unit tests for Sensor classes.

Tests cover:
    - SensorBase: noise, bias, drift, quantization
    - IMUSensor: orientation measurements
    - PowerSensor: power system measurements
    - ThermalSensor: temperature measurements
    - SensorSuite: complete telemetry frame generation
"""

import pytest
import random
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'meridian3' / 'src'))

from simulator.rover_state import RoverState
from simulator.sensors import SensorBase, IMUSensor, PowerSensor, ThermalSensor, SensorSuite


class TestSensorBase:
    """Test SensorBase functionality."""

    def test_creates_sensor_with_name(self):
        """SensorBase should store sensor name."""
        sensor = SensorBase(name="TestSensor")
        assert sensor.name == "TestSensor"

    def test_creates_sensor_with_noise_params(self):
        """SensorBase should store noise and bias parameters."""
        sensor = SensorBase(name="Test", noise_stddev=0.5, bias=1.0)
        assert sensor.noise_stddev == 0.5
        assert sensor.bias == 1.0

    def test_drift_initializes_to_zero(self):
        """Drift should start at zero."""
        sensor = SensorBase(name="Test")
        assert sensor.drift == 0.0

    def test_apply_noise_adds_variation(self):
        """apply_noise should add random variation to values."""
        random.seed(42)  # For reproducibility
        sensor = SensorBase(name="Test", noise_stddev=1.0, bias=0.0)

        true_value = 100.0
        readings = [sensor.apply_noise(true_value) for _ in range(100)]

        # Readings should vary
        assert len(set(readings)) > 50  # Most readings should be unique

        # Mean should be close to true value
        mean = sum(readings) / len(readings)
        assert abs(mean - true_value) < 0.5  # Within 0.5 with 100 samples

    def test_apply_noise_with_zero_stddev(self):
        """Zero noise should return exact value."""
        sensor = SensorBase(name="Test", noise_stddev=0.0, bias=0.0)
        true_value = 100.0
        reading = sensor.apply_noise(true_value)
        assert reading == true_value

    def test_apply_noise_with_bias(self):
        """Bias should add constant offset."""
        sensor = SensorBase(name="Test", noise_stddev=0.0, bias=5.0)
        true_value = 100.0
        reading = sensor.apply_noise(true_value)
        assert reading == 105.0

    def test_update_drift_changes_drift(self):
        """update_drift should modify drift value."""
        random.seed(42)
        sensor = SensorBase(name="Test")

        initial_drift = sensor.drift
        sensor.update_drift(dt=1.0, drift_rate=0.1)

        # Drift should have changed
        assert sensor.drift != initial_drift

    def test_drift_accumulates_over_time(self):
        """Drift should accumulate over multiple updates."""
        random.seed(42)
        sensor = SensorBase(name="Test")

        for _ in range(10):
            sensor.update_drift(dt=1.0, drift_rate=0.1)

        # Drift should be non-zero after 10 steps
        assert abs(sensor.drift) > 0.01

    def test_quantize_rounds_to_resolution(self):
        """quantize should round to resolution steps."""
        sensor = SensorBase(name="Test")

        # Test quantization to 0.1
        assert sensor.quantize(5.14, 0.1) == pytest.approx(5.1)
        assert sensor.quantize(5.16, 0.1) == pytest.approx(5.2)

        # Test quantization to 1.0
        assert sensor.quantize(5.4, 1.0) == pytest.approx(5.0)
        assert sensor.quantize(5.6, 1.0) == pytest.approx(6.0)


class TestIMUSensor:
    """Test IMU sensor."""

    def test_creates_imu_sensor(self):
        """IMUSensor should create successfully."""
        imu = IMUSensor()
        assert imu.name == "IMU"

    def test_reads_orientation_from_rover_state(self):
        """IMU should read roll, pitch, heading."""
        imu = IMUSensor()
        rover = RoverState()
        rover.roll = 10.0
        rover.pitch = -5.0
        rover.heading = 270.0

        reading = imu.read(rover)

        assert 'roll' in reading
        assert 'pitch' in reading
        assert 'heading' in reading

    def test_reading_has_noise(self):
        """IMU readings should have noise applied."""
        random.seed(42)
        imu = IMUSensor()
        rover = RoverState()
        rover.roll = 0.0

        readings = [imu.read(rover)['roll'] for _ in range(50)]

        # Readings should vary due to noise
        assert len(set(readings)) > 25

    def test_reading_close_to_true_value(self):
        """IMU readings should be statistically close to true value."""
        random.seed(42)
        imu = IMUSensor()
        rover = RoverState()
        rover.roll = 10.0
        rover.pitch = 5.0
        rover.heading = 45.0

        rolls = [imu.read(rover)['roll'] for _ in range(100)]
        pitches = [imu.read(rover)['pitch'] for _ in range(100)]
        headings = [imu.read(rover)['heading'] for _ in range(100)]

        # Mean should be close to true values
        assert abs(sum(rolls) / len(rolls) - 10.0) < 1.0
        assert abs(sum(pitches) / len(pitches) - 5.0) < 1.0
        assert abs(sum(headings) / len(headings) - 45.0) < 1.0


class TestPowerSensor:
    """Test Power sensor."""

    def test_creates_power_sensor(self):
        """PowerSensor should create successfully."""
        power = PowerSensor()
        assert power.name == "PowerMonitor"

    def test_reads_power_from_rover_state(self):
        """Power sensor should read battery and solar values."""
        power = PowerSensor()
        rover = RoverState()

        reading = power.read(rover)

        assert 'battery_voltage' in reading
        assert 'battery_current' in reading
        assert 'battery_soc' in reading
        assert 'solar_voltage' in reading
        assert 'solar_current' in reading

    def test_all_power_readings_are_numeric(self):
        """All power readings should be numeric."""
        power = PowerSensor()
        rover = RoverState()

        reading = power.read(rover)

        for key, value in reading.items():
            assert isinstance(value, (int, float)), f"{key} should be numeric"


class TestThermalSensor:
    """Test Thermal sensor."""

    def test_creates_thermal_sensor(self):
        """ThermalSensor should create successfully."""
        thermal = ThermalSensor()
        assert thermal.name == "ThermalArray"

    def test_reads_temperatures_from_rover_state(self):
        """Thermal sensor should read all temperatures."""
        thermal = ThermalSensor()
        rover = RoverState()

        reading = thermal.read(rover)

        assert 'cpu_temp' in reading
        assert 'battery_temp' in reading
        assert 'motor_temp' in reading
        assert 'chassis_temp' in reading

    def test_temperatures_are_quantized(self):
        """Temperature readings should be quantized to 0.1°C."""
        thermal = ThermalSensor()
        rover = RoverState()
        rover.cpu_temp = 25.14  # Should round to 25.1

        reading = thermal.read(rover)

        # Check that value is a multiple of 0.1
        temp = reading['cpu_temp']
        assert abs(temp - round(temp, 1)) < 1e-6


class TestSensorSuite:
    """Test complete sensor suite."""

    def test_creates_sensor_suite(self):
        """SensorSuite should create successfully."""
        suite = SensorSuite()
        assert suite.imu is not None
        assert suite.power is not None
        assert suite.thermal is not None

    def test_read_all_returns_complete_frame(self):
        """read_all should return complete telemetry frame."""
        suite = SensorSuite()
        rover = RoverState()
        mission_time = 100.0

        frame = suite.read_all(rover, mission_time)

        # Check for timestamp
        assert 'timestamp' in frame
        assert frame['timestamp'] == mission_time

        # Check for IMU readings
        assert 'roll' in frame
        assert 'pitch' in frame
        assert 'heading' in frame

        # Check for power readings
        assert 'battery_voltage' in frame
        assert 'battery_current' in frame
        assert 'battery_soc' in frame
        assert 'solar_voltage' in frame
        assert 'solar_current' in frame

        # Check for thermal readings
        assert 'cpu_temp' in frame
        assert 'battery_temp' in frame
        assert 'motor_temp' in frame
        assert 'chassis_temp' in frame

        # Check for position (from rover state directly)
        assert 'x' in frame
        assert 'y' in frame
        assert 'z' in frame
        assert 'velocity' in frame

    def test_read_all_includes_position_data(self):
        """read_all should include position data from rover state."""
        suite = SensorSuite()
        rover = RoverState()
        rover.x = 100.0
        rover.y = 200.0
        rover.z = 5.0
        rover.velocity = 0.05

        frame = suite.read_all(rover, 50.0)

        assert frame['x'] == 100.0
        assert frame['y'] == 200.0
        assert frame['z'] == 5.0
        assert frame['velocity'] == 0.05

    def test_read_all_updates_drift(self):
        """read_all should update sensor drift over time."""
        random.seed(42)
        suite = SensorSuite()
        rover = RoverState()

        # Read multiple times
        for i in range(10):
            frame = suite.read_all(rover, float(i))

        # IMU drift should have accumulated
        assert suite.imu.drift != 0.0

    def test_multiple_reads_produce_different_results(self):
        """Multiple reads should produce different values due to noise."""
        random.seed(42)
        suite = SensorSuite()
        rover = RoverState()
        rover.roll = 0.0

        frame1 = suite.read_all(rover, 0.0)
        frame2 = suite.read_all(rover, 1.0)

        # Noise should make readings different
        assert frame1['roll'] != frame2['roll']


class TestSensorEdgeCases:
    """Test edge cases and unusual conditions."""

    def test_sensor_with_extreme_rover_state(self):
        """Sensors should handle extreme rover state values."""
        suite = SensorSuite()
        rover = RoverState()

        # Extreme values
        rover.battery_voltage = 50.0  # Way above normal
        rover.cpu_temp = -100.0  # Very cold
        rover.roll = 180.0  # Upside down

        frame = suite.read_all(rover, 1000.0)

        # Should still produce a frame
        assert 'battery_voltage' in frame
        assert 'cpu_temp' in frame
        assert 'roll' in frame

    def test_sensor_with_zero_mission_time(self):
        """Sensors should work at mission start (t=0)."""
        suite = SensorSuite()
        rover = RoverState()

        frame = suite.read_all(rover, 0.0)

        assert frame['timestamp'] == 0.0
        assert 'roll' in frame

    def test_sensor_with_very_large_mission_time(self):
        """Sensors should work with large mission times."""
        suite = SensorSuite()
        rover = RoverState()

        large_time = 1e6  # ~11.5 days
        frame = suite.read_all(rover, large_time)

        assert frame['timestamp'] == large_time
