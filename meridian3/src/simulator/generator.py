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
    all other components:

    ┌────────────────────────────────────────────────┐
    │           SIMULATION GENERATOR                 │
    │                                                │
    │  ┌──────────────────────────────┐             │
    │  │  Simulation Loop             │             │
    │  │  ┌────────────────────────┐  │             │
    │  │  │ 1. Advance time        │  │             │
    │  │  │ 2. Update state        │  │             │
    │  │  │ 3. Apply environment   │  │             │
    │  │  │ 4. Read sensors        │  │             │
    │  │  │ 5. Yield frame         │  │             │
    │  │  └────────────────────────┘  │             │
    │  └──────────────────────────────┘             │
    │         │      │      │      │                 │
    │         │      │      │      └─────────────┐   │
    │         │      │      └────────────┐        │  │
    │         │      └───────────┐       │        │  │
    │         └──────┐            │       │        │  │
    │                │            │       │        │  │
    └────────────────┼────────────┼───────┼────────┼──┘
                     ▼            ▼       ▼        ▼
              [RoverState] [Environment] [Sensors] [Commands]

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
            env_info = self.environment.update(self.timestep, self.rover)

            # STEP 2: Process commands (if any)
            # TODO Phase 2: Implement command queue and processing
            # e.g., drive commands, science instrument activation, etc.

            # STEP 3: Update rover physics
            # TODO Phase 2: Implement rover dynamics (motion, power balance, thermal)
            # For now, rover stays stationary
            self.rover.mission_time = self.current_time

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
