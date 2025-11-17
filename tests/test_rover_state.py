"""
Unit tests for RoverState class.

Tests cover:
    - Initialization with default values
    - String representation (__repr__)
    - State field types and ranges
    - Boolean flags
"""

import pytest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'meridian3' / 'src'))

from simulator.rover_state import RoverState


class TestRoverStateInitialization:
    """Test RoverState initialization."""

    def test_creates_valid_instance(self):
        """RoverState should create a valid instance."""
        rover = RoverState()
        assert rover is not None

    def test_position_defaults_to_zero(self):
        """Position should default to origin (0, 0, 0)."""
        rover = RoverState()
        assert rover.x == 0.0
        assert rover.y == 0.0
        assert rover.z == 0.0

    def test_orientation_defaults_to_zero(self):
        """Orientation should default to zero (level, facing north)."""
        rover = RoverState()
        assert rover.roll == 0.0
        assert rover.pitch == 0.0
        assert rover.heading == 0.0

    def test_velocity_defaults_to_zero(self):
        """Velocity should default to zero (stationary)."""
        rover = RoverState()
        assert rover.velocity == 0.0

    def test_battery_has_valid_initial_values(self):
        """Battery should have healthy initial values."""
        rover = RoverState()
        assert 28.0 <= rover.battery_voltage <= 36.0
        assert 0.0 <= rover.battery_soc <= 100.0
        assert rover.battery_soc > 50.0  # Should start reasonably charged
        assert rover.battery_current is not None

    def test_solar_panel_has_valid_initial_values(self):
        """Solar panel should have valid initial values."""
        rover = RoverState()
        assert rover.solar_panel_voltage >= 0.0
        assert rover.solar_panel_current >= 0.0

    def test_temperatures_have_valid_initial_values(self):
        """All temperatures should be within valid ranges."""
        rover = RoverState()
        assert -100.0 <= rover.cpu_temp <= 100.0
        assert -100.0 <= rover.battery_temp <= 100.0
        assert -100.0 <= rover.motor_temp <= 100.0
        assert -100.0 <= rover.chassis_temp <= 100.0

    def test_mission_time_defaults_to_zero(self):
        """Mission time should start at zero."""
        rover = RoverState()
        assert rover.mission_time == 0.0
        assert rover.sol == 0
        assert rover.local_time == 0.0

    def test_operational_flags_have_default_values(self):
        """Operational flags should have sensible defaults."""
        rover = RoverState()
        assert isinstance(rover.is_moving, bool)
        assert isinstance(rover.is_charging, bool)
        assert isinstance(rover.heater_active, bool)
        assert isinstance(rover.science_active, bool)


class TestRoverStateRepresentation:
    """Test RoverState string representation."""

    def test_repr_returns_string(self):
        """__repr__ should return a string."""
        rover = RoverState()
        repr_str = repr(rover)
        assert isinstance(repr_str, str)

    def test_repr_contains_key_info(self):
        """__repr__ should contain key state information."""
        rover = RoverState()
        repr_str = repr(rover)
        assert "RoverState" in repr_str
        assert "pos=" in repr_str
        assert "heading=" in repr_str
        assert "battery=" in repr_str

    def test_repr_with_custom_values(self):
        """__repr__ should reflect custom state values."""
        rover = RoverState()
        rover.x = 100.0
        rover.y = 200.0
        rover.heading = 45.0
        rover.battery_soc = 75.0

        repr_str = repr(rover)
        assert "100.00" in repr_str
        assert "200.00" in repr_str
        assert "45.0" in repr_str or "45.00" in repr_str
        assert "75.0" in repr_str or "75.00" in repr_str


class TestRoverStateFieldTypes:
    """Test that RoverState fields have correct types."""

    def test_numeric_fields_are_floats(self):
        """All numeric fields should be floats."""
        rover = RoverState()

        # Position
        assert isinstance(rover.x, float)
        assert isinstance(rover.y, float)
        assert isinstance(rover.z, float)

        # Orientation
        assert isinstance(rover.roll, float)
        assert isinstance(rover.pitch, float)
        assert isinstance(rover.heading, float)

        # Velocity
        assert isinstance(rover.velocity, float)

        # Battery
        assert isinstance(rover.battery_voltage, float)
        assert isinstance(rover.battery_current, float)
        assert isinstance(rover.battery_soc, float)

        # Temperatures
        assert isinstance(rover.cpu_temp, float)
        assert isinstance(rover.battery_temp, float)
        assert isinstance(rover.motor_temp, float)
        assert isinstance(rover.chassis_temp, float)

    def test_time_fields_are_numeric(self):
        """Time fields should be numeric."""
        rover = RoverState()
        assert isinstance(rover.mission_time, float)
        assert isinstance(rover.sol, int)
        assert isinstance(rover.local_time, float)

    def test_boolean_flags_are_bools(self):
        """Operational flags should be booleans."""
        rover = RoverState()
        assert isinstance(rover.is_moving, bool)
        assert isinstance(rover.is_charging, bool)
        assert isinstance(rover.heater_active, bool)
        assert isinstance(rover.science_active, bool)


class TestRoverStateModification:
    """Test that RoverState fields can be modified."""

    def test_can_modify_position(self):
        """Position fields should be modifiable."""
        rover = RoverState()
        rover.x = 100.5
        rover.y = 200.3
        rover.z = -5.0

        assert rover.x == 100.5
        assert rover.y == 200.3
        assert rover.z == -5.0

    def test_can_modify_orientation(self):
        """Orientation fields should be modifiable."""
        rover = RoverState()
        rover.roll = 10.0
        rover.pitch = -5.0
        rover.heading = 270.0

        assert rover.roll == 10.0
        assert rover.pitch == -5.0
        assert rover.heading == 270.0

    def test_can_modify_battery_state(self):
        """Battery fields should be modifiable."""
        rover = RoverState()
        rover.battery_soc = 50.0
        rover.battery_voltage = 30.0
        rover.battery_current = -2.0  # Discharging

        assert rover.battery_soc == 50.0
        assert rover.battery_voltage == 30.0
        assert rover.battery_current == -2.0

    def test_can_toggle_flags(self):
        """Boolean flags should be togglable."""
        rover = RoverState()

        original_moving = rover.is_moving
        rover.is_moving = not original_moving
        assert rover.is_moving != original_moving

        original_charging = rover.is_charging
        rover.is_charging = not original_charging
        assert rover.is_charging != original_charging


class TestRoverStateEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_position_values(self):
        """RoverState should accept extreme position values."""
        rover = RoverState()
        rover.x = -10000.0
        rover.y = 10000.0
        rover.z = -1000.0

        assert rover.x == -10000.0
        assert rover.y == 10000.0
        assert rover.z == -1000.0

    def test_extreme_temperature_values(self):
        """RoverState should accept extreme temperature values."""
        rover = RoverState()
        rover.cpu_temp = -100.0
        rover.battery_temp = 100.0

        assert rover.cpu_temp == -100.0
        assert rover.battery_temp == 100.0

    def test_battery_soc_boundaries(self):
        """RoverState should accept battery SoC at boundaries."""
        rover = RoverState()

        rover.battery_soc = 0.0
        assert rover.battery_soc == 0.0

        rover.battery_soc = 100.0
        assert rover.battery_soc == 100.0

    def test_heading_wraparound(self):
        """Heading values should be storable (wraparound handled elsewhere)."""
        rover = RoverState()

        rover.heading = 359.0
        assert rover.heading == 359.0

        rover.heading = 0.0
        assert rover.heading == 0.0

        # Note: RoverState doesn't enforce wraparound, that's Environment's job
        rover.heading = 370.0
        assert rover.heading == 370.0
