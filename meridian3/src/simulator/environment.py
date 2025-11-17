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
            hazard: Hazard event dictionary with keys:
                    - 'type': hazard type (dust_devil, radiation_spike, slip)
                    - 'severity': 0.0 to 1.0 intensity
                    - 'duration': seconds
            rover_state: RoverState to modify

        Teaching Note:
            Hazards are discrete events that temporarily affect rover state.
            Effects can be immediate (slip) or sustained (dust storm).
            We apply effects probabilistically and proportional to severity.
        """
        hazard_type = hazard['type']
        severity = hazard['severity']

        if hazard_type == 'dust_devil':
            # Dust devil effects:
            # 1. Reduces solar panel efficiency (dust coating)
            # 2. Adds noise to IMU sensors (vibration)
            # 3. Slight temperature perturbation

            # Reduce solar efficiency temporarily
            # This is a simplification - real dust accumulates over time
            # Here we just add a transient effect
            # (The Environment.update() will recalculate solar power each tick)

            # Add IMU disturbance (affects orientation readings indirectly)
            # We don't modify state directly, sensors will add extra noise
            # But we can add some actual physical rotation
            rover_state.heading += random.gauss(0, severity * 2.0)  # Up to ±2° heading change

            # Slight temperature perturbation from wind
            temp_change = random.gauss(0, severity * 5.0)  # Up to ±5°C
            rover_state.chassis_temp += temp_change * 0.1  # Small instant change

        elif hazard_type == 'radiation_spike':
            # Radiation spike effects:
            # 1. Can cause CPU errors / resets (simulated as temp spike)
            # 2. Causes sensor glitches (handled by sensors layer)
            # 3. Drains battery slightly (radiation hardening circuits activate)

            # Simulate CPU stress from radiation
            rover_state.cpu_temp += severity * 10.0  # Up to +10°C spike

            # Small battery drain from SEU (Single Event Upset) recovery
            soc_loss = severity * 0.1  # Up to 0.1% SoC loss
            rover_state.battery_soc -= soc_loss
            rover_state.battery_soc = max(0.0, rover_state.battery_soc)

        elif hazard_type == 'slip':
            # Slip event effects:
            # 1. Sudden position change (rover slides)
            # 2. Orientation change (tilt from uneven surface)
            # 3. Possible damage (simulated as increased current draw)

            # Position slip (rover slides downhill/sideways)
            slip_distance = severity * 2.0  # Up to 2 meters
            slip_angle = random.uniform(0, 360)  # Random direction
            rover_state.x += slip_distance * math.cos(math.radians(slip_angle))
            rover_state.y += slip_distance * math.sin(math.radians(slip_angle))

            # Orientation change from slip
            rover_state.roll += random.gauss(0, severity * 10.0)  # Up to ±10°
            rover_state.pitch += random.gauss(0, severity * 10.0)

            # Clamp to safe limits
            rover_state.roll = max(-30, min(30, rover_state.roll))
            rover_state.pitch = max(-30, min(30, rover_state.pitch))

            # Motor strain from slip recovery
            rover_state.motor_temp += severity * 5.0  # Motors work harder

        # Log hazard for debugging (would normally go to mission log)
        # print(f"Hazard: {hazard_type} (severity={severity:.2f})")
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
        Applies terrain effects, solar power, thermal changes, and hazards.

        Teaching Note:
            This method demonstrates how multiple subsystems interact to
            modify rover state. Each effect is applied sequentially, though
            in reality many effects happen simultaneously. The order matters
            for some effects (e.g., calculate power before updating battery).
        """
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Update time-of-day and mission time
        # ═══════════════════════════════════════════════════════════
        rover_state.local_time += dt
        if rover_state.local_time >= self.orbit.mars_sol_length:
            rover_state.local_time -= self.orbit.mars_sol_length
            rover_state.sol += 1

        rover_state.mission_time += dt

        # ═══════════════════════════════════════════════════════════
        # STEP 2: Get current terrain properties
        # ═══════════════════════════════════════════════════════════
        terrain = self.terrain.get_terrain_at(rover_state.x, rover_state.y)

        # Apply terrain effects to rover orientation (tilt)
        # Slopes cause rover to tilt - affects roll and pitch
        if rover_state.is_moving and terrain['slope_angle'] > 5.0:
            # Significant slope: add some roll/pitch variation
            # This is simplified - real tilt depends on slope direction
            tilt_effect = terrain['slope_angle'] * 0.3  # 10° slope → 3° tilt
            rover_state.roll += random.gauss(0, tilt_effect * 0.1)
            rover_state.pitch += random.gauss(0, tilt_effect * 0.1)

            # Clamp to reasonable limits
            rover_state.roll = max(-30, min(30, rover_state.roll))
            rover_state.pitch = max(-30, min(30, rover_state.pitch))

        # ═══════════════════════════════════════════════════════════
        # STEP 3: Calculate and apply solar power
        # ═══════════════════════════════════════════════════════════
        solar_angle = self.orbit.get_solar_angle(rover_state.local_time)
        available_solar = self.orbit.calculate_solar_power(solar_angle, terrain['dust_level'])

        # Update solar panel state
        rover_state.solar_panel_voltage = 34.0 * (available_solar / 100.0)  # Scale to voltage
        rover_state.solar_panel_current = available_solar / 30.0  # P=VI, nominal 30V

        # ═══════════════════════════════════════════════════════════
        # STEP 4: Calculate power consumption
        # ═══════════════════════════════════════════════════════════
        # Base power consumption (CPU, housekeeping)
        base_power = 15.0  # Watts

        # Power for movement (if moving)
        movement_power = 0.0
        if rover_state.is_moving:
            # Terrain affects power consumption
            power_mult = self.terrain.calculate_power_multiplier(
                terrain['slope_angle'],
                terrain['surface_type']
            )
            movement_power = 40.0 * power_mult  # Base 40W, scaled by terrain

        # Heater power (if active)
        heater_power = 20.0 if rover_state.heater_active else 0.0

        # Science instruments (if active)
        science_power = 25.0 if rover_state.science_active else 0.0

        total_power_consumption = base_power + movement_power + heater_power + science_power

        # ═══════════════════════════════════════════════════════════
        # STEP 5: Update battery state
        # ═══════════════════════════════════════════════════════════
        # Net power = solar input - consumption
        net_power = available_solar - total_power_consumption

        # Update battery current (positive = charging, negative = discharging)
        rover_state.battery_current = net_power / rover_state.battery_voltage
        rover_state.is_charging = (net_power > 0)

        # Update state of charge (simplified battery model)
        # SoC change rate depends on current and battery capacity
        battery_capacity_wh = 1000.0  # Watt-hours
        soc_change_per_hour = (net_power / battery_capacity_wh) * 100.0  # Percent per hour
        soc_change = soc_change_per_hour * (dt / 3600.0)  # Convert to timestep

        rover_state.battery_soc += soc_change

        # Clamp SoC to [0, 100]
        rover_state.battery_soc = max(0.0, min(100.0, rover_state.battery_soc))

        # Battery voltage varies with SoC (simplified)
        # Nominal 32V, drops to 28V at low SoC, peaks at 36V when full
        rover_state.battery_voltage = 28.0 + (rover_state.battery_soc / 100.0) * 8.0

        # ═══════════════════════════════════════════════════════════
        # STEP 6: Update thermal state
        # ═══════════════════════════════════════════════════════════
        # Ambient temperature varies with time of day
        # Mars: -80°C at night, up to +20°C at noon (equator)
        ambient_temp = self._calculate_ambient_temperature(solar_angle)

        # CPU temperature depends on ambient and computational load
        cpu_load_factor = 1.0  # Could vary based on activity
        cpu_heat_above_ambient = 15.0 * cpu_load_factor  # CPU generates heat

        # Thermal time constant (heat transfer is not instantaneous)
        thermal_tc = 300.0  # seconds (5 minutes to equilibrate)
        alpha = dt / thermal_tc  # Exponential approach to target

        target_cpu_temp = ambient_temp + cpu_heat_above_ambient
        rover_state.cpu_temp += alpha * (target_cpu_temp - rover_state.cpu_temp)

        # Battery temperature tracks ambient (large thermal mass)
        rover_state.battery_temp += alpha * (ambient_temp - rover_state.battery_temp)

        # Motor temperature depends on movement
        motor_heat = 10.0 if rover_state.is_moving else 0.0
        target_motor_temp = ambient_temp + motor_heat
        rover_state.motor_temp += alpha * (target_motor_temp - rover_state.motor_temp)

        # Chassis tracks ambient closely
        rover_state.chassis_temp += alpha * (ambient_temp - rover_state.chassis_temp)

        # Heater logic: activate if battery too cold
        if rover_state.battery_temp < -10.0:
            rover_state.heater_active = True
        elif rover_state.battery_temp > 0.0:
            rover_state.heater_active = False

        # ═══════════════════════════════════════════════════════════
        # STEP 7: Apply hazard effects
        # ═══════════════════════════════════════════════════════════
        new_hazards = self.hazards.update(dt, rover_state)

        for hazard in new_hazards:
            self.hazards.apply_hazard_effects(hazard, rover_state)

        # ═══════════════════════════════════════════════════════════
        # STEP 8: Return environment info for telemetry
        # ═══════════════════════════════════════════════════════════
        return {
            'terrain': terrain,
            'solar_angle': solar_angle,
            'available_solar': available_solar,
            'power_consumption': total_power_consumption,
            'net_power': net_power,
            'ambient_temp': ambient_temp,
            'new_hazards': new_hazards,
        }

    def _calculate_ambient_temperature(self, solar_angle: float) -> float:
        """
        Calculate ambient temperature based on solar angle.

        Args:
            solar_angle: Solar elevation in degrees (0=horizon, 90=overhead)

        Returns:
            Ambient temperature in Celsius

        Teaching Note:
            Mars temperature swings are extreme due to thin atmosphere.
            At night: -80°C to -100°C
            At noon: -20°C to +20°C (equator, summer)
            We use a simplified model based on solar angle.
        """
        if solar_angle <= 0:
            # Night time - very cold
            return -80.0 + random.gauss(0, 5.0)  # -80°C ± some variation

        # Day time - temperature rises with sun angle
        # Maximum temp around +20°C at solar noon
        max_day_temp = 20.0
        min_night_temp = -80.0

        # Sinusoidal variation
        temp_range = max_day_temp - min_night_temp
        temp = min_night_temp + temp_range * (solar_angle / 90.0)

        # Add some random variation
        temp += random.gauss(0, 3.0)

        return temp


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
