"""
RoverState - Core State Management for the Meridian-3 Rover

PURPOSE:
    This module defines the RoverState class, which encapsulates all physical
    and operational state for the simulated rover. It serves as the "single
    source of truth" for the rover's condition at any moment in time.

THEORY:
    In simulation engineering, separating STATE from BEHAVIOR is crucial.
    The RoverState class holds only data - position, orientation, power levels,
    temperatures, etc. The logic that MODIFIES this state lives elsewhere
    (in sensors.py, environment.py, and generator.py).

    This separation enables:
        - Easy debugging (just inspect the state object)
        - Reproducible simulations (save/load state)
        - Modular testing (test state updates independently)

MERIDIAN-3 STORY SNIPPET:
    "The rover doesn't think. It simply IS. At every moment, it exists in a
    particular configuration: wheels at certain angles, solar panels generating
    certain power, CPU at a certain temperature. Our job is to faithfully
    represent that configuration."

ARCHITECTURE ROLE:
    RoverState sits at the heart of the simulator. Every simulation tick,
    the generator updates the state based on commands, environment effects,
    and time passage. Sensors then READ this state to produce telemetry.

                ┌──────────────────────┐
                │   RoverState         │
                │  ┌────────────────┐  │
                │  │ Position       │  │
                │  │ Orientation    │  │
                │  │ Power System   │  │
                │  │ Thermal State  │  │
                │  │ Command Queue  │  │
                │  └────────────────┘  │
                └──────────────────────┘
                         ▲     │
                         │     │
        ┌────────────────┘     └──────────────┐
        │                                      │
   [Environment]                          [Sensors]
    modifies state                      read state

TEACHING GOALS:
    - Data class design and encapsulation
    - Separation of state and behavior
    - Documentation of physical units and ranges
    - Initialization with sensible defaults

DEBUGGING NOTES:
    - To inspect state: print(rover_state) or use __repr__
    - To save state: consider adding to_dict() / from_dict() methods
    - To visualize: create plotting functions that read state fields

FUTURE EXTENSIONS:
    - Add state history buffer for trajectory analysis
    - Implement state validation (e.g., power can't be negative)
    - Add serialization for checkpoint/restore
    - Include command history for debugging maneuvers
"""


class RoverState:
    """
    Complete physical and operational state of the Meridian-3 rover.

    This class uses explicit fields rather than a dataclass to allow
    detailed inline documentation of each state variable.
    """

    def __init__(self):
        """
        Initialize rover state with default values representing a healthy rover
        at mission start (sol 0, just after landing).
        """

        # ═══════════════════════════════════════════════════════════
        # POSITION & ORIENTATION
        # ═══════════════════════════════════════════════════════════
        # Position in local coordinate frame (meters from landing site)
        self.x = 0.0          # East-West position (m)
        self.y = 0.0          # North-South position (m)
        self.z = 0.0          # Elevation relative to landing site (m)

        # Orientation (euler angles in degrees)
        self.roll = 0.0       # Rotation around forward axis (-180 to +180)
        self.pitch = 0.0      # Rotation around lateral axis (-90 to +90)
        self.heading = 0.0    # Compass heading (0=North, 90=East, etc.)

        # Velocity (meters per second)
        self.velocity = 0.0   # Forward speed (0.0 to ~0.05 m/s nominal)

        # ═══════════════════════════════════════════════════════════
        # POWER SYSTEM
        # ═══════════════════════════════════════════════════════════
        self.battery_voltage = 32.0      # Volts (28-36V nominal range)
        self.battery_current = 0.5       # Amperes (negative = charging)
        self.battery_soc = 85.0          # State of charge (0-100%)
        self.solar_panel_voltage = 34.0  # Volts (0-40V depending on sun angle)
        self.solar_panel_current = 1.2   # Amperes (0-3A depending on sun)

        # ═══════════════════════════════════════════════════════════
        # THERMAL STATE
        # ═══════════════════════════════════════════════════════════
        self.cpu_temp = 25.0             # Celsius (-40 to +85 operational)
        self.battery_temp = 20.0         # Celsius (-20 to +45 safe range)
        self.motor_temp = 30.0           # Celsius (ambient to +60)
        self.chassis_temp = 15.0         # Celsius (tracks ambient closely)

        # ═══════════════════════════════════════════════════════════
        # TIME & MISSION CONTEXT
        # ═══════════════════════════════════════════════════════════
        self.mission_time = 0.0          # Seconds since mission start
        self.sol = 0                     # Martian day number (1 sol ≈ 24.6 hours)
        self.local_time = 0.0            # Time of sol in seconds (0-88775)

        # ═══════════════════════════════════════════════════════════
        # OPERATIONAL FLAGS
        # ═══════════════════════════════════════════════════════════
        self.is_moving = False           # True when wheels are turning
        self.is_charging = True          # True when solar input > consumption
        self.heater_active = False       # True when battery heater is on
        self.science_active = False      # True when instruments are operating

    def __repr__(self):
        """
        Provide a readable summary of rover state for debugging.
        """
        return (
            f"RoverState(pos=({self.x:.2f}, {self.y:.2f}, {self.z:.2f}), "
            f"heading={self.heading:.1f}°, "
            f"battery={self.battery_soc:.1f}%, "
            f"cpu_temp={self.cpu_temp:.1f}°C, "
            f"sol={self.sol}, "
            f"moving={self.is_moving})"
        )

    # ═══════════════════════════════════════════════════════════════
    # FUTURE EXTENSION IDEAS
    # ═══════════════════════════════════════════════════════════════
    # def to_dict(self) -> dict:
    #     """Serialize state to dictionary for storage/transmission."""
    #     pass
    #
    # def from_dict(cls, data: dict) -> 'RoverState':
    #     """Restore state from serialized dictionary."""
    #     pass
    #
    # def validate(self) -> list:
    #     """Check state for physically impossible values, return warnings."""
    #     pass
    #
    # def update_derived_values(self):
    #     """Compute derived quantities like power consumption, thermal balance."""
    #     pass
