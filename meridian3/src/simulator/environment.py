"""
Environment System - Terrain, Hazards, and Orbital Mechanics

PURPOSE:
    This module models the Martian environment and its effects on the rover.
    It includes terrain characteristics, hazardous events (dust storms,
    radiation spikes), and orbital mechanics (day/night cycles, solar angles).

THEORY:
    A rover doesn't operate in a vacuum - it interacts with a complex,
    dynamic environment. Key environmental factors:

        - Terrain: Slope affects power consumption and stability
        - Surface properties: Dust, rocks, ice affect traction and sensors
        - Atmospheric conditions: Dust storms reduce solar power
        - Radiation: Solar particle events can cause sensor glitches
        - Thermal cycles: Day/night temperature swings affect battery and CPU
        - Orbital position: Determines solar illumination angle

    By modeling these factors, we create realistic simulation scenarios
    that stress-test our telemetry pipeline and anomaly detection.

MERIDIAN-3 STORY SNIPPET:
    "Mars is not kind. A dust devil can appear in minutes, coating our solar
    panels. A slip on loose regolith can tilt us 15 degrees. At night, the
    temperature drops to -80°C. Our CPU heater draws precious battery power.
    The environment is not just scenery - it's an active adversary we must
    monitor and adapt to."

ARCHITECTURE ROLE:
    The Environment modifies RoverState based on:
        - Current terrain under the rover
        - Random hazard events
        - Time of day (orbital position)
        - Historical effects (e.g., accumulated dust on panels)

    ┌──────────────┐
    │ Environment  │
    │              │
    │  ┌────────┐  │       ┌─────────────┐
    │  │Terrain │──┼──────→│ RoverState  │
    │  ├────────┤  │       └─────────────┘
    │  │Hazards │──┤            ▲
    │  ├────────┤  │            │
    │  │ Orbit  │──┘            │
    │  └────────┘           [Generator]
    └──────────────┘        applies effects

TEACHING GOALS:
    - Modeling complex system interactions
    - Stochastic event generation (Poisson processes for hazards)
    - Physical modeling (orbital mechanics, thermal balance)
    - State machine patterns for environment states

DEBUGGING NOTES:
    - To test terrain effects: place rover on steep slope, verify power increase
    - To test hazards: force-trigger events, check state changes
    - To test orbital: fast-forward time, verify day/night transitions
    - Use visualization to plot terrain maps and hazard distributions

FUTURE EXTENSIONS:
    - Implement 2D/3D terrain heightmaps
    - Add weather system (pressure, wind, temperature)
    - Model dust accumulation on solar panels over time
    - Include seasonal variations (Mars has seasons!)
    - Add radiation exposure tracking for hardware degradation
"""

import random
import math
from typing import Dict, Optional, Tuple


class TerrainModel:
    """
    Represents the terrain at the rover's current location.

    Terrain affects:
        - Power consumption (slopes require more motor power)
        - Stability (steep slopes increase roll/pitch)
        - Traction (loose regolith causes slippage)
        - Dust exposure (dusty areas degrade solar panels)
    """

    def __init__(self):
        """Initialize terrain model with default flat, firm surface."""
        self.slope_angle = 0.0       # Degrees (0-30 typical, >20 is risky)
        self.surface_type = "firm"   # firm, loose, dusty, rocky, icy
        self.roughness = 0.0         # 0.0 (smooth) to 1.0 (very rough)
        self.dust_level = 0.0        # 0.0 (clean) to 1.0 (heavy dust)

    def get_terrain_at(self, x: float, y: float) -> Dict[str, float]:
        """
        Get terrain properties at a given position.

        In Phase 1, this returns uniform terrain. In Phase 2, we'll add
        spatial variation using noise functions or heightmaps.

        Args:
            x: East-West position (meters)
            y: North-South position (meters)

        Returns:
            Dictionary of terrain properties at that location
        """
        # Placeholder: uniform terrain everywhere
        # TODO Phase 2: Add Perlin noise for realistic terrain variation
        return {
            'slope_angle': self.slope_angle,
            'surface_type': self.surface_type,
            'roughness': self.roughness,
            'dust_level': self.dust_level,
        }

    def calculate_power_multiplier(self, slope: float, surface: str) -> float:
        """
        Calculate how terrain affects power consumption.

        Args:
            slope: Terrain slope in degrees
            surface: Surface type string

        Returns:
            Power multiplier (1.0 = normal, >1.0 = more power needed)
        """
        # Base multiplier from slope
        slope_mult = 1.0 + (abs(slope) / 10.0) * 0.5  # 10° slope = 50% more power

        # Surface type multiplier
        surface_multipliers = {
            'firm': 1.0,
            'loose': 1.3,
            'dusty': 1.2,
            'rocky': 1.4,
            'icy': 0.9,  # Slippery but less resistance
        }
        surface_mult = surface_multipliers.get(surface, 1.0)

        return slope_mult * surface_mult


class HazardSystem:
    """
    Generates and manages environmental hazards.

    Hazards are discrete events that temporarily affect rover state:
        - Dust devils: Reduce solar power, add noise to sensors
        - Radiation spikes: Cause sensor glitches, increase CPU errors
        - Thermal spikes/drops: Rapid temperature changes
        - Slip events: Sudden position/orientation changes

    Uses Poisson process for realistic random timing.
    """

    def __init__(self):
        """Initialize hazard system with default probabilities."""
        self.active_hazards = []  # List of currently active hazards

        # Mean time between events (seconds)
        self.dust_devil_mtbe = 3600 * 24  # Once per day on average
        self.radiation_spike_mtbe = 3600 * 72  # Once per 3 sols
        self.slip_event_mtbe = 3600 * 12  # Twice per sol when moving

    def update(self, dt: float, rover_state) -> list:
        """
        Check for new hazard events and update active ones.

        Args:
            dt: Time step in seconds
            rover_state: Current RoverState (some hazards only occur when moving)

        Returns:
            List of new hazard events that occurred this timestep
        """
        new_events = []

        # Check for dust devil (Poisson process)
        if random.random() < dt / self.dust_devil_mtbe:
            new_events.append({
                'type': 'dust_devil',
                'severity': random.uniform(0.3, 1.0),
                'duration': random.uniform(60, 300),  # 1-5 minutes
            })

        # Check for radiation spike
        if random.random() < dt / self.radiation_spike_mtbe:
            new_events.append({
                'type': 'radiation_spike',
                'severity': random.uniform(0.5, 1.0),
                'duration': random.uniform(10, 60),  # 10-60 seconds
            })

        # Check for slip event (only when moving)
        if rover_state.is_moving and random.random() < dt / self.slip_event_mtbe:
            new_events.append({
                'type': 'slip',
                'severity': random.uniform(0.2, 0.8),
                'duration': 1.0,  # Instantaneous
            })

        return new_events

    def apply_hazard_effects(self, hazard: dict, rover_state):
        """
        Modify rover state based on active hazard.

        Args:
            hazard: Hazard event dictionary
            rover_state: RoverState to modify

        This will be fully implemented in Phase 2.
        """
        # Placeholder for Phase 2 implementation
        # TODO: Implement specific effects for each hazard type
        pass


class OrbitalMechanics:
    """
    Models Mars orbital position and its effects.

    Key factors:
        - Solar angle: Determines solar panel efficiency
        - Day/night cycle: Affects temperature and power availability
        - Seasonal variation: Mars has seasons like Earth
        - Eclipse prediction: When Phobos/Deimos block sun
    """

    def __init__(self):
        """Initialize orbital model."""
        self.mars_sol_length = 88775.0  # Martian sol in seconds (24h 39m 35s)
        self.season = "summer"  # summer, winter (simplified)
        self.latitude = -4.5  # Degrees (negative = south)

    def get_solar_angle(self, local_time: float) -> float:
        """
        Calculate solar elevation angle based on time of sol.

        Args:
            local_time: Time of sol in seconds (0 to mars_sol_length)

        Returns:
            Solar elevation angle in degrees (0=horizon, 90=overhead)
        """
        # Simplified model: sinusoidal variation through the day
        # Peak at local noon (halfway through sol)
        fraction_of_sol = local_time / self.mars_sol_length
        angle = math.sin(fraction_of_sol * 2 * math.pi) * 90

        # Clamp to 0 (below horizon = night)
        return max(0, angle)

    def calculate_solar_power(self, solar_angle: float, dust_level: float) -> float:
        """
        Calculate available solar power based on sun angle and dust.

        Args:
            solar_angle: Solar elevation in degrees
            dust_level: Atmospheric/panel dust (0.0 to 1.0)

        Returns:
            Solar power in watts (0 to ~100W for typical rover panels)
        """
        # Base power from sun angle (cosine law)
        max_power = 100.0  # Watts at optimal angle
        angle_factor = math.sin(math.radians(solar_angle))

        # Dust reduces efficiency
        dust_factor = 1.0 - (dust_level * 0.5)  # Up to 50% reduction

        return max_power * angle_factor * dust_factor


class Environment:
    """
    Complete environment system - integrates terrain, hazards, and orbital mechanics.

    This is the main interface used by the simulation generator to apply
    environmental effects to the rover state.
    """

    def __init__(self):
        """Initialize all environment subsystems."""
        self.terrain = TerrainModel()
        self.hazards = HazardSystem()
        self.orbit = OrbitalMechanics()

    def update(self, dt: float, rover_state):
        """
        Update environment and apply effects to rover state.

        Args:
            dt: Time step in seconds
            rover_state: RoverState to modify based on environment

        This orchestrates all environmental updates each simulation tick.
        Full implementation in Phase 2.
        """
        # Update time-of-day
        rover_state.local_time += dt
        if rover_state.local_time >= self.orbit.mars_sol_length:
            rover_state.local_time -= self.orbit.mars_sol_length
            rover_state.sol += 1

        # Get current terrain
        terrain = self.terrain.get_terrain_at(rover_state.x, rover_state.y)

        # Update hazards and get new events
        new_hazards = self.hazards.update(dt, rover_state)

        # Calculate solar power availability
        solar_angle = self.orbit.get_solar_angle(rover_state.local_time)
        available_solar = self.orbit.calculate_solar_power(solar_angle, terrain['dust_level'])

        # TODO Phase 2: Apply effects to rover state
        # - Update solar panel output based on available_solar
        # - Modify power consumption based on terrain
        # - Apply hazard effects
        # - Update thermal state based on day/night cycle

        return {
            'terrain': terrain,
            'solar_angle': solar_angle,
            'available_solar': available_solar,
            'new_hazards': new_hazards,
        }


# ═══════════════════════════════════════════════════════════════
# FUTURE EXTENSION IDEAS
# ═══════════════════════════════════════════════════════════════
# class WeatherSystem:
#     """Models Martian weather: pressure, wind, dust storms."""
#     pass
#
# class TerrainHeightmap:
#     """2D heightmap for realistic terrain modeling."""
#     pass
#
# def generate_mission_scenario(difficulty: str) -> Environment:
#     """Create predefined environment configurations for testing."""
#     pass
#
# class RadiationDoseTracker:
#     """Track cumulative radiation exposure for hardware degradation."""
#     pass
