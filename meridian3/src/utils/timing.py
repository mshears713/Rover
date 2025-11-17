"""
Timing Utilities - Mission Time Management

PURPOSE:
    Provides utilities for managing mission time, converting between different
    time representations (Earth time, Mars sols, local solar time), and
    handling timestep logic for simulation. Essential for coordinating all
    time-dependent simulation aspects.

THEORY:
    Time in space missions is complex! Multiple coordinate systems exist:

    - MISSION ELAPSED TIME (MET): Seconds since mission start
      * Monotonic, never jumps backward
      * Easy for engineering (simple counter)
      * Used internally for all simulation timesteps

    - SOL NUMBER: Martian days since landing (Sol 0, Sol 1, ...)
      * One sol = 24 hours, 39 minutes, 35 seconds (88,775 seconds)
      * Mars rotates slower than Earth
      * Used for mission planning and operations

    - LOCAL SOLAR TIME (LST): Time of day on Mars
      * 00:00:00 at midnight, 12:00:00 at noon
      * Determines solar angle (power generation)
      * Affects thermal environment

    - EARTH TIME (UTC): Wall-clock time on Earth
      * Used for communication scheduling
      * Time delay for radio signals (4-24 minutes each way!)

    TIMESTEP SELECTION:
        Timestep (dt) is a critical simulation parameter:

        - Too small: Simulation runs slowly, wastes computation
        - Too large: Miss important events, numerical instability

        Typical choices:
          * dt = 0.1s: High fidelity, smooth animations
          * dt = 1.0s: Good balance for rover telemetry (1 Hz)
          * dt = 10.0s: Fast simulation, skip details

        Timestep should be smaller than:
          * Fastest dynamics (e.g., sensor response time)
          * Shortest event duration (e.g., radiation spike)
          * Desired output resolution

ARCHITECTURE ROLE:
    Timing utilities are used by:
        - SimulationGenerator: Main loop timestep management
        - Environment: Day/night cycles, seasonal effects
        - Sensors: Drift accumulation over time
        - Storage: Timestamp formatting and indexing

TEACHING GOALS:
    - Understanding multiple time coordinate systems
    - Timestep selection trade-offs
    - Time conversion algorithms
    - Handling edge cases (leap seconds, time zones)
    - Monotonic vs wall-clock time

DEBUGGING NOTES:
    - Always use MET for simulation - don't rely on wall-clock time
    - To verify sol calculation: 1 sol should = 88775 seconds exactly
    - To test LST: Check that it wraps at sol boundaries
    - Watch for floating-point errors in long simulations
    - Use integer frame counters for exact indexing

FUTURE EXTENSIONS:
    - Add Earth-Mars light-time delay calculator
    - Implement Mars calendar (Darian calendar)
    - Add seasonal effects (Mars year = 687 Earth days)
    - Support multiple time zones (different landing sites)
    - Add real-time synchronization for hardware-in-the-loop testing
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Mars sol length in seconds
# One Martian day (sol) = 24 hours, 39 minutes, 35 seconds
MARS_SOL_SECONDS = 88775.244  # seconds

# Earth day length for comparison
EARTH_DAY_SECONDS = 86400.0  # seconds

# Ratio of sol to Earth day (sol is ~2.7% longer)
SOL_TO_EARTH_DAY_RATIO = MARS_SOL_SECONDS / EARTH_DAY_SECONDS


# ═══════════════════════════════════════════════════════════════
# TIME CONVERSION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def mission_time_to_sol(mission_seconds: float) -> int:
    """
    Convert mission elapsed time to sol number.

    Args:
        mission_seconds: Seconds since mission start (MET)

    Returns:
        Sol number (integer day count)

    Example:
        met = 88775.0  # Exactly one sol
        sol = mission_time_to_sol(met)  # Returns 1

        met = 200000.0  # ~2.25 sols
        sol = mission_time_to_sol(met)  # Returns 2

    Teaching Note:
        Simple integer division. Sol 0 is landing day (MET 0-88774),
        Sol 1 is first full day (MET 88775-177549), etc.
    """
    return int(mission_seconds // MARS_SOL_SECONDS)


def mission_time_to_local_time(mission_seconds: float) -> float:
    """
    Convert mission elapsed time to local solar time within current sol.

    Args:
        mission_seconds: Seconds since mission start (MET)

    Returns:
        Local time in seconds (0 to MARS_SOL_SECONDS)

    Example:
        met = 88775.0  # Start of Sol 1
        lst_sec = mission_time_to_local_time(met)  # Returns 0.0

        met = 44387.5  # Midpoint of Sol 0 (noon)
        lst_sec = mission_time_to_local_time(met)  # Returns 44387.5

    Teaching Note:
        Uses modulo operation to "wrap" time within a sol.
        LST resets to 0 at start of each new sol.
    """
    return mission_seconds % MARS_SOL_SECONDS


def local_time_to_hms(local_time_seconds: float) -> Tuple[int, int, int]:
    """
    Convert local solar time to hours:minutes:seconds format.

    Args:
        local_time_seconds: Local time in seconds (0 to MARS_SOL_SECONDS)

    Returns:
        Tuple of (hours, minutes, seconds) in 24-hour format

    Example:
        lst = 44387.5  # Noon on Mars
        h, m, s = local_time_to_hms(lst)  # Returns (12, 19, 47)
        # Note: "12:19:47" because Mars noon ≠ Earth 12:00:00

    Teaching Note:
        Mars hours/minutes/seconds are same duration as Earth.
        A Mars day just has more of them (24h 39m 35s total).
        We use Earth units for consistency with clocks/tools.
    """
    total_seconds = int(local_time_seconds)

    hours = total_seconds // 3600
    remainder = total_seconds % 3600

    minutes = remainder // 60
    seconds = remainder % 60

    return (hours, minutes, seconds)


def format_mission_time(mission_seconds: float) -> str:
    """
    Format mission time as "Sol X, HH:MM:SS" string.

    Args:
        mission_seconds: Seconds since mission start

    Returns:
        Human-readable time string

    Example:
        met = 100000.0
        formatted = format_mission_time(met)
        # Returns: "Sol 1, 03:10:25"

    Teaching Note:
        This is the standard format used in rover operations.
        Operators think in "sols" not seconds - more intuitive
        for planning daily activities.
    """
    sol_num = mission_time_to_sol(mission_seconds)
    local_sec = mission_time_to_local_time(mission_seconds)
    h, m, s = local_time_to_hms(local_sec)

    return f"Sol {sol_num}, {h:02d}:{m:02d}:{s:02d}"


# ═══════════════════════════════════════════════════════════════
# TIMESTEP MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@dataclass
class TimestepInfo:
    """
    Information about simulation timestep selection.

    Helps document why a particular timestep was chosen and
    what constraints it satisfies.
    """
    dt: float  # Timestep in seconds
    sample_rate: float  # Samples per second (1/dt)
    nyquist_freq: float  # Maximum frequency that can be captured
    reason: str  # Why this timestep was chosen


def recommend_timestep(
    fastest_dynamic_sec: float = 1.0,
    shortest_event_sec: float = 1.0,
    desired_resolution_sec: float = 1.0
) -> TimestepInfo:
    """
    Recommend an appropriate simulation timestep based on requirements.

    Args:
        fastest_dynamic_sec: Time constant of fastest system dynamics
                             (e.g., sensor response time)
        shortest_event_sec: Duration of shortest event to capture
                            (e.g., radiation spike duration)
        desired_resolution_sec: Desired output time resolution

    Returns:
        TimestepInfo with recommended dt and explanation

    Example:
        # Rover with 0.1s sensor response, 10s minimum events, 1s output
        info = recommend_timestep(
            fastest_dynamic_sec=0.1,
            shortest_event_sec=10.0,
            desired_resolution_sec=1.0
        )
        # Recommends dt=0.1s to capture fastest dynamics

    Teaching Note:
        Rule of thumb: timestep should be ≤ 1/10th of fastest timescale.
        This ensures numerical stability and accurate event capture.
        Nyquist theorem: sample rate ≥ 2× highest frequency to avoid aliasing.
    """
    # Choose timestep as minimum of constraints, divided by safety factor
    safety_factor = 5  # Sample 5× faster than minimum requirement

    constraints = [
        fastest_dynamic_sec / safety_factor,
        shortest_event_sec / safety_factor,
        desired_resolution_sec
    ]

    dt = min(constraints)
    sample_rate = 1.0 / dt
    nyquist_freq = sample_rate / 2.0

    # Determine which constraint was limiting
    if dt == fastest_dynamic_sec / safety_factor:
        reason = f"Limited by fastest dynamic ({fastest_dynamic_sec}s)"
    elif dt == shortest_event_sec / safety_factor:
        reason = f"Limited by shortest event ({shortest_event_sec}s)"
    else:
        reason = f"Limited by desired resolution ({desired_resolution_sec}s)"

    return TimestepInfo(
        dt=dt,
        sample_rate=sample_rate,
        nyquist_freq=nyquist_freq,
        reason=reason
    )


def validate_timestep(dt: float, total_duration: float) -> Tuple[bool, str]:
    """
    Validate that a timestep is reasonable for the simulation.

    Args:
        dt: Proposed timestep in seconds
        total_duration: Total simulation duration in seconds

    Returns:
        Tuple of (is_valid, warning_message)

    Example:
        valid, msg = validate_timestep(dt=0.01, total_duration=86400)
        # Returns (False, "Too many steps: 8640000 frames!")

    Teaching Note:
        Common pitfalls:
        - Timestep too small → simulation takes forever
        - Timestep too large → miss important dynamics
        - Non-uniform timesteps → numerical errors accumulate

        A good simulation has 100-100,000 timesteps.
        <100: probably too coarse
        >1,000,000: probably too fine (or duration too long)
    """
    if dt <= 0:
        return (False, "Timestep must be positive!")

    num_steps = int(total_duration / dt)

    if num_steps < 10:
        return (False, f"Too few steps ({num_steps}). Increase duration or decrease dt.")

    if num_steps > 10_000_000:
        return (False, f"Too many steps ({num_steps}). This will be very slow!")

    if num_steps > 1_000_000:
        return (True, f"Warning: {num_steps} steps will take significant time.")

    if dt > 60.0:
        return (True, f"Warning: dt={dt}s is quite large. May miss events.")

    return (True, "Timestep looks reasonable.")


# ═══════════════════════════════════════════════════════════════
# MISSION CLOCK CLASS
# ═══════════════════════════════════════════════════════════════

class MissionClock:
    """
    Manages mission time and conversions.

    Maintains current mission elapsed time and provides convenient
    accessors for sol number, local time, and formatted strings.
    """

    def __init__(self, start_met: float = 0.0):
        """
        Initialize mission clock.

        Args:
            start_met: Starting mission elapsed time in seconds
                       (normally 0, but can resume from checkpoint)
        """
        self.met = start_met  # Mission Elapsed Time in seconds
        self.dt = 1.0  # Default timestep
        self.frame_count = 0  # Number of timesteps executed

    def tick(self, dt: Optional[float] = None):
        """
        Advance time by one timestep.

        Args:
            dt: Timestep duration (uses default if not specified)

        Example:
            clock = MissionClock()
            clock.tick(1.0)  # Advance by 1 second
            clock.tick(1.0)  # Advance by another 1 second
            # clock.met is now 2.0
        """
        if dt is None:
            dt = self.dt

        self.met += dt
        self.frame_count += 1

    @property
    def sol(self) -> int:
        """Get current sol number."""
        return mission_time_to_sol(self.met)

    @property
    def local_time(self) -> float:
        """Get current local solar time in seconds."""
        return mission_time_to_local_time(self.met)

    @property
    def local_time_hms(self) -> Tuple[int, int, int]:
        """Get current local solar time as (hours, minutes, seconds)."""
        return local_time_to_hms(self.local_time)

    def format_time(self) -> str:
        """Get formatted time string."""
        return format_mission_time(self.met)

    def reset(self):
        """Reset clock to mission start."""
        self.met = 0.0
        self.frame_count = 0

    def __repr__(self):
        """String representation of clock state."""
        return f"MissionClock(MET={self.met:.1f}s, {self.format_time()}, frames={self.frame_count})"


# ═══════════════════════════════════════════════════════════════
# SOLAR ANGLE CALCULATION
# ═══════════════════════════════════════════════════════════════

def calculate_solar_elevation(local_time_seconds: float, latitude: float = 0.0) -> float:
    """
    Calculate solar elevation angle based on local time and latitude.

    Args:
        local_time_seconds: Local solar time in seconds (0 to MARS_SOL_SECONDS)
        latitude: Landing site latitude in degrees (-90 to +90)
                  Default 0 = equator (simplified model)

    Returns:
        Solar elevation angle in degrees (0=horizon, 90=overhead, <0=night)

    Example:
        # Calculate sun angle at Mars noon
        noon_time = MARS_SOL_SECONDS / 2  # Midpoint of sol
        angle = calculate_solar_elevation(noon_time, latitude=0)
        # Returns ~90 degrees (sun overhead at equator)

    Teaching Note:
        This is a simplified model! Real solar position depends on:
        - Season (Mars orbital position)
        - Latitude and longitude
        - Axial tilt (25.2° for Mars, similar to Earth's 23.5°)
        - Equation of time (orbit eccentricity effects)

        For educational purposes, we use a sinusoidal approximation
        that captures the basic day/night cycle.
    """
    # Fraction through the sol (0 at midnight, 0.5 at noon, 1.0 at next midnight)
    fraction_of_sol = local_time_seconds / MARS_SOL_SECONDS

    # Solar elevation peaks at local noon
    # Using sinusoidal model: angle = max_elevation * sin(2π * (t - 0.25))
    # The -0.25 shift makes minimum occur at t=0 (midnight)
    angle_rad = math.sin(2 * math.pi * (fraction_of_sol - 0.25))

    # Maximum elevation depends on latitude and season
    # Simplified: use 90° - latitude as maximum elevation
    # (This approximates equinox conditions at solar noon)
    max_elevation = 90.0 - abs(latitude)

    # Scale sinusoid to range from -max_elevation (midnight) to +max_elevation (noon)
    solar_elevation = angle_rad * max_elevation

    return solar_elevation


# ═══════════════════════════════════════════════════════════════
# FUTURE EXTENSION IDEAS
# ═══════════════════════════════════════════════════════════════
# def calculate_light_time_delay(earth_mars_distance_km: float) -> float:
#     """Calculate radio signal delay between Earth and Mars."""
#     pass
#
# def mars_to_earth_time(mars_time: float, landing_datetime: str) -> str:
#     """Convert Mars mission time to Earth UTC."""
#     pass
#
# def seasonal_solar_declination(sol: int, mars_year: int) -> float:
#     """Calculate solar declination accounting for Mars seasons."""
#     pass
#
# def is_eclipse(local_time: float, moon: str) -> bool:
#     """Check if Phobos or Deimos is eclipsing the sun."""
#     pass
