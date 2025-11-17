"""
Simulation Generator - Main Orchestration Loop

PURPOSE:
    This module contains the main simulation loop that ties together the
    RoverState, Sensors, and Environment to generate realistic telemetry
    data streams. It's the "conductor" of the simulation orchestra.

THEORY:
    A simulation is fundamentally a loop that:
        1. Advances time by a small step (dt)
        2. Updates state based on commands and physics
        3. Applies environmental effects
        4. Reads sensors to produce telemetry
        5. Yields or stores the telemetry frame
        6. Repeats

    Key design decisions:
        - Fixed timestep vs variable timestep
        - Synchronous vs asynchronous execution
        - Real-time vs faster-than-real-time
        - Memory: generator pattern (yield) vs storing all frames

    This implementation uses a Python generator (yield) to produce frames
    on-demand, which is memory-efficient and allows streaming to the
    telemetry pipeline.

MERIDIAN-3 STORY SNIPPET:
    "The mission unfolds one tick at a time. Every second, we capture a
    snapshot: where is the rover? What do the sensors see? What just happened?
    String these snapshots together and you have a story - the story of
    Meridian-3's journey across the red planet."

ARCHITECTURE ROLE:
    The generator sits at the top of the simulation stack, orchestrating
    all other components.

COMPLETE SIGNAL FLOW DIAGRAM (Phase 2):

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                      SIMULATION GENERATOR LOOP                        ║
    ║                                                                       ║
    ║  ┌─────────────────────────────────────────────────────────────────┐ ║
    ║  │  ITERATION N                     Current Time: t + N*dt         │ ║
    ║  └─────────────────────────────────────────────────────────────────┘ ║
    ║                                                                       ║
    ║  ┌──────────────────────────────────────────────────────────┐        ║
    ║  │  STEP 1: Update Environment                              │        ║
    ║  │  ┌────────────────────────────────────────────────────┐  │        ║
    ║  │  │  Terrain Effects     →  Tilt, Power Multiplier    │  │        ║
    ║  │  │  Solar Calculation   →  Panel Voltage/Current     │  │        ║
    ║  │  │  Power Balance       →  Battery SoC, Charging     │  │        ║
    ║  │  │  Thermal Dynamics    →  All Temperatures          │  │        ║
    ║  │  │  Hazard Events       →  Dust/Radiation/Slip       │  │        ║
    ║  │  └────────────────────────────────────────────────────┘  │        ║
    ║  │                           │                               │        ║
    ║  │                           ▼                               │        ║
    ║  │                    [RoverState Updated]                   │        ║
    ║  └───────────────────────────┬───────────────────────────────┘        ║
    ║                              │                                        ║
    ║  ┌───────────────────────────▼───────────────────────────────┐        ║
    ║  │  STEP 2: Process Commands                                 │        ║
    ║  │  ┌────────────────────────────────────────────────────┐   │        ║
    ║  │  │  Low Battery Check  →  Stop if SoC < 20%          │   │        ║
    ║  │  │  Science Activation →  Enable during daytime      │   │        ║
    ║  │  │  Future: Command Queue Processing                 │   │        ║
    ║  │  └────────────────────────────────────────────────────┘   │        ║
    ║  │                           │                                │        ║
    ║  │                           ▼                                │        ║
    ║  │                    [Operational State Changed]             │        ║
    ║  └───────────────────────────┬───────────────────────────────┘        ║
    ║                              │                                        ║
    ║  ┌───────────────────────────▼───────────────────────────────┐        ║
    ║  │  STEP 3: Update Rover Physics                             │        ║
    ║  │  ┌────────────────────────────────────────────────────┐   │        ║
    ║  │  │  Motion Model   →  Update X, Y based on velocity │   │        ║
    ║  │  │  Friction       →  Decelerate over time          │   │        ║
    ║  │  │  Future: Advanced dynamics, collision detection  │   │        ║
    ║  │  └────────────────────────────────────────────────────┘   │        ║
    ║  │                           │                                │        ║
    ║  │                           ▼                                │        ║
    ║  │                    [Position & Motion Updated]             │        ║
    ║  └───────────────────────────┬───────────────────────────────┘        ║
    ║                              │                                        ║
    ║  ┌───────────────────────────▼───────────────────────────────┐        ║
    ║  │  STEP 4: Read All Sensors                                 │        ║
    ║  │  ┌────────────────────────────────────────────────────┐   │        ║
    ║  │  │  IMU Sensor      →  Roll, Pitch, Heading + Noise │   │        ║
    ║  │  │  Power Sensor    →  Voltages, Currents + Noise   │   │        ║
    ║  │  │  Thermal Sensor  →  Temperatures + Noise         │   │        ║
    ║  │  │  Add Drift & Bias to all readings               │   │        ║
    ║  │  └────────────────────────────────────────────────────┘   │        ║
    ║  │                           │                                │        ║
    ║  │                           ▼                                │        ║
    ║  │                 [Telemetry Frame Created]                  │        ║
    ║  └───────────────────────────┬───────────────────────────────┘        ║
    ║                              │                                        ║
    ║  ┌───────────────────────────▼───────────────────────────────┐        ║
    ║  │  STEP 5: Add Metadata                                     │        ║
    ║  │  ┌────────────────────────────────────────────────────┐   │        ║
    ║  │  │  Frame ID, Timestamp, Sol, Local Time             │   │        ║
    ║  │  │  Environment Info (terrain, solar, hazards)       │   │        ║
    ║  │  └────────────────────────────────────────────────────┘   │        ║
    ║  └───────────────────────────┬───────────────────────────────┘        ║
    ║                              │                                        ║
    ║  ┌───────────────────────────▼───────────────────────────────┐        ║
    ║  │  STEP 6: Yield Telemetry Frame                            │        ║
    ║  │                                                            │        ║
    ║  │      frame = {                                            │        ║
    ║  │          'timestamp': 123.4,                              │        ║
    ║  │          'roll': 2.3, 'pitch': -1.1, ...                  │        ║
    ║  │          'battery_soc': 87.3,  ...                        │        ║
    ║  │          'env_info': {...}                                │        ║
    ║  │      }                                                     │        ║
    ║  │                           │                                │        ║
    ║  │                           ▼                                │        ║
    ║  │                  [Downstream Pipeline]                     │        ║
    ║  │                  (Packetizer → Corruptor → ...)           │        ║
    ║  └───────────────────────────┬───────────────────────────────┘        ║
    ║                              │                                        ║
    ║  ┌───────────────────────────▼───────────────────────────────┐        ║
    ║  │  STEP 7: Advance Time                                     │        ║
    ║  │                                                            │        ║
    ║  │      current_time += dt                                   │        ║
    ║  │      frame_count  += 1                                    │        ║
    ║  │                                                            │        ║
    ║  │      Loop back to STEP 1 (until max_duration reached)     │        ║
    ║  └────────────────────────────────────────────────────────────┘        ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

    DATA FLOW SUMMARY:
        Ground Truth (RoverState)
             ↓ environment effects
        Modified State
             ↓ sensor noise
        Noisy Telemetry
             ↓ yield to consumer
        Pipeline Processing (Phase 3)


    KEY INSIGHT:
        The simulation maintains TWO parallel data streams:
        1. TRUE STATE:  Clean RoverState (what's actually happening)
        2. TELEMETRY:   Noisy sensor readings (what we observe)

        This separation is crucial for testing anomaly detection and
        data cleaning algorithms in later phases

TEACHING GOALS:
    - Generator pattern for memory efficiency
    - Simulation loop architecture
    - Timestep management and stability
    - State management across loop iterations
    - Yielding data to downstream consumers

DEBUGGING NOTES:
    - To inspect a single frame: next(generator)
    - To run N steps: list(itertools.islice(generator, N))
    - To verify determinism: run twice with same seed, compare outputs
    - To profile performance: measure time per iteration
    - Set dt small (0.1s) for smooth animations, large (1.0s) for fast testing

FUTURE EXTENSIONS:
    - Add command queue for user/scripted commands
    - Implement fast-forward / time-skip
    - Add pause/resume capability
    - Implement checkpointing (save/restore simulation state)
    - Add event logging for mission timeline
    - Support parallel simulation of multiple rovers
"""

from typing import Generator, Dict, Any, Optional
from .rover_state import RoverState
from .sensors import SensorSuite
from .environment import Environment


class SimulationGenerator:
    """
    Main simulation orchestrator - generates telemetry frames over time.

    Uses Python generator pattern to produce frames on-demand without
    storing entire mission history in memory.
    """

    def __init__(
        self,
        timestep: float = 1.0,
        max_duration: Optional[float] = None,
        random_seed: Optional[int] = None
    ):
        """
        Initialize simulation generator.

        Args:
            timestep: Time step in seconds (default 1.0 = 1 Hz sampling)
            max_duration: Maximum simulation time in seconds (None = unlimited)
            random_seed: Seed for reproducible simulations (None = random)
        """
        self.timestep = timestep
        self.max_duration = max_duration
        self.random_seed = random_seed

        # Initialize subsystems
        self.rover = RoverState()
        self.sensors = SensorSuite()
        self.environment = Environment()

        # Simulation state
        self.current_time = 0.0
        self.frame_count = 0

        # Set random seed for reproducibility
        if random_seed is not None:
            import random
            random.seed(random_seed)

    def generate_frames(self) -> Generator[Dict[str, Any], None, None]:
        """
        Main simulation loop - generates telemetry frames.

        Yields:
            Telemetry frame dictionary with all sensor readings and metadata

        Example usage:
            sim = SimulationGenerator(timestep=1.0, max_duration=3600)
            for frame in sim.generate_frames():
                print(f"Time {frame['timestamp']}: Battery {frame['battery_soc']}%")
        """
        while True:
            # Check termination condition
            if self.max_duration and self.current_time >= self.max_duration:
                break

            # ═══════════════════════════════════════════════════════
            # SIMULATION LOOP STEPS
            # ═══════════════════════════════════════════════════════

            # STEP 1: Update environment effects
            # (environment modifies rover state based on terrain, hazards, time)
            # This includes:
            # - Terrain effects (tilt, power consumption)
            # - Solar power generation
            # - Battery charge/discharge
            # - Thermal dynamics
            # - Hazard events
            env_info = self.environment.update(self.timestep, self.rover)

            # STEP 2: Process commands (if any)
            # In this phase, we implement basic automatic behaviors
            # Future phases will add command queue for scripted missions

            # Example automatic behavior: Stop moving if battery too low
            if self.rover.battery_soc < 20.0:
                self.rover.is_moving = False
                # In a real rover, this would trigger a safe mode

            # Example: Activate science during day when stationary
            if env_info['solar_angle'] > 30.0 and not self.rover.is_moving:
                self.rover.science_active = True
            else:
                self.rover.science_active = False

            # STEP 3: Update rover physics (motion model)
            # Environment.update() already handles power, thermal, and hazards
            # Here we handle simple motion physics

            if self.rover.is_moving:
                # Simple motion model: rover moves forward at velocity
                # Direction is determined by heading
                import math
                dx = self.rover.velocity * math.cos(math.radians(self.rover.heading)) * self.timestep
                dy = self.rover.velocity * math.sin(math.radians(self.rover.heading)) * self.timestep

                self.rover.x += dx
                self.rover.y += dy

                # Slowly reduce velocity due to friction (if not actively driving)
                # This is a simplification - real rovers have explicit drive commands
                self.rover.velocity *= 0.98  # 2% decay per timestep

                if self.rover.velocity < 0.001:  # Effectively stopped
                    self.rover.velocity = 0.0
                    self.rover.is_moving = False

            # Teaching Note:
            # The separation between environment effects (Step 1) and rover
            # dynamics (Step 3) demonstrates modular simulation design.
            # Environment provides external forces/conditions, rover physics
            # determines how the rover responds.

            # STEP 4: Read all sensors
            telemetry_frame = self.sensors.read_all(self.rover, self.current_time)

            # STEP 5: Add metadata and environment info
            telemetry_frame['frame_id'] = self.frame_count
            telemetry_frame['sol'] = self.rover.sol
            telemetry_frame['local_time'] = self.rover.local_time
            telemetry_frame['env_info'] = env_info

            # STEP 6: Yield frame to consumer
            yield telemetry_frame

            # STEP 7: Advance time
            self.current_time += self.timestep
            self.frame_count += 1

    def run_mission(self, duration: float) -> list:
        """
        Run a complete mission and return all frames.

        This is a convenience method that collects all frames into a list.
        Use with caution for long missions (memory intensive).

        Args:
            duration: Mission duration in seconds

        Returns:
            List of all telemetry frames
        """
        # Temporarily override max_duration
        original_max = self.max_duration
        self.max_duration = duration

        frames = list(self.generate_frames())

        # Restore original max_duration
        self.max_duration = original_max

        return frames

    def reset(self):
        """
        Reset simulation to initial state.

        Useful for running multiple missions or experiments.
        """
        self.rover = RoverState()
        self.sensors = SensorSuite()
        self.environment = Environment()
        self.current_time = 0.0
        self.frame_count = 0

        if self.random_seed is not None:
            import random
            random.seed(self.random_seed)


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def quick_simulation(duration: float = 3600, timestep: float = 1.0) -> list:
    """
    Quick helper to run a simple simulation.

    Args:
        duration: Simulation duration in seconds (default 1 hour)
        timestep: Time between frames in seconds (default 1 Hz)

    Returns:
        List of telemetry frames

    Example:
        frames = quick_simulation(duration=60, timestep=0.5)  # 1 min at 2 Hz
    """
    sim = SimulationGenerator(timestep=timestep, max_duration=duration)
    return list(sim.generate_frames())


# ═══════════════════════════════════════════════════════════════
# FUTURE EXTENSION IDEAS
# ═══════════════════════════════════════════════════════════════
# class CommandQueue:
#     """Manage scheduled commands (drive, science, power management)."""
#     pass
#
# class MissionScenario:
#     """Predefined mission profiles (traverse, science stop, emergency)."""
#     pass
#
# def save_checkpoint(sim: SimulationGenerator, filepath: str):
#     """Save simulation state for later resumption."""
#     pass
#
# def load_checkpoint(filepath: str) -> SimulationGenerator:
#     """Restore simulation from saved checkpoint."""
#     pass
#
# class ParallelSimulation:
#     """Run multiple simulations in parallel (Monte Carlo analysis)."""
#     pass
