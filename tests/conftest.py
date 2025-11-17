"""
Pytest configuration and shared fixtures for Meridian-3 tests.

This file contains:
    - Common fixtures used across multiple test modules
    - Test configuration and setup
    - Utility functions for testing
"""

import pytest
import random
import tempfile
import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'meridian3' / 'src'))


# ═══════════════════════════════════════════════════════════════
# FIXTURES: Common Objects
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def rover_state():
    """Provide a fresh RoverState instance for each test."""
    from simulator.rover_state import RoverState
    return RoverState()


@pytest.fixture
def sensor_suite():
    """Provide a fresh SensorSuite instance for each test."""
    from simulator.sensors import SensorSuite
    return SensorSuite()


@pytest.fixture
def environment():
    """Provide a fresh Environment instance for each test."""
    from simulator.environment import Environment
    return Environment()


@pytest.fixture
def simulation_generator():
    """Provide a SimulationGenerator with fixed seed for reproducibility."""
    from simulator.generator import SimulationGenerator
    return SimulationGenerator(
        timestep=1.0,
        max_duration=10.0,
        random_seed=42
    )


@pytest.fixture
def packetizer():
    """Provide a fresh Packetizer instance for each test."""
    from pipeline.packetizer import Packetizer
    return Packetizer(encoding="raw")


@pytest.fixture
def corruptor():
    """Provide a Corruptor with fixed seed for reproducibility."""
    from pipeline.corruptor import Corruptor
    return Corruptor(
        packet_loss_rate=0.01,
        field_corruption_rate=0.05,
        jitter_stddev=0.1,
        random_seed=42
    )


@pytest.fixture
def cleaner():
    """Provide a fresh Cleaner instance for each test."""
    from pipeline.cleaner import Cleaner
    return Cleaner(history_size=10)


@pytest.fixture
def anomaly_detector():
    """Provide a fresh AnomalyDetector instance for each test."""
    from pipeline.anomalies import AnomalyDetector
    return AnomalyDetector(
        history_size=50,
        z_score_threshold=3.0
    )


@pytest.fixture
def temp_db_path():
    """Provide a temporary database path that is cleaned up after test."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    # Also remove WAL files if they exist
    wal_path = db_path + '-wal'
    shm_path = db_path + '-shm'
    if os.path.exists(wal_path):
        os.remove(wal_path)
    if os.path.exists(shm_path):
        os.remove(shm_path)


@pytest.fixture
def storage(temp_db_path):
    """Provide a MissionStorage instance with temporary database."""
    from pipeline.storage import MissionStorage
    storage = MissionStorage(temp_db_path, cache_size=100)
    yield storage
    storage.close()


# ═══════════════════════════════════════════════════════════════
# FIXTURES: Sample Data
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def sample_telemetry_frame():
    """Provide a sample telemetry frame for testing."""
    return {
        'timestamp': 100.5,
        'frame_id': 42,
        'roll': 1.2,
        'pitch': -0.5,
        'heading': 45.0,
        'battery_voltage': 28.4,
        'battery_current': 2.1,
        'battery_soc': 85.3,
        'battery_temp': 15.2,
        'solar_voltage': 32.0,
        'solar_current': 1.5,
        'cpu_temp': 30.0,
        'motor_temp': 35.0,
        'chassis_temp': 10.0,
        'x': 150.0,
        'y': 200.0,
        'z': 0.5,
        'velocity': 0.05,
        'sol': 1,
        'local_time': 12345.0,
        'env_info': {
            'solar_angle': 45.0,
            'available_solar': 70.0,
            'power_consumption': 50.0,
            'net_power': 20.0,
            'ambient_temp': -20.0,
            'new_hazards': []
        }
    }


@pytest.fixture
def sample_packet(sample_telemetry_frame, packetizer):
    """Provide a sample encoded packet for testing."""
    return packetizer.encode_frame(sample_telemetry_frame)


@pytest.fixture
def sample_clean_frame():
    """Provide a sample clean frame (output of Cleaner) for testing."""
    return {
        'timestamp': 100.0,
        'frame_id': 42,
        'data': {
            'battery_soc': 85.0,
            'battery_voltage': 28.0,
            'battery_temp': 20.0,
            'battery_current': 2.0,
            'roll': 1.0,
            'pitch': 0.5,
            'heading': 45.0,
        },
        'metadata': {
            'quality': 'high',
            'repairs': [],
            'warnings': [],
            'checksum_valid': True,
        }
    }


# ═══════════════════════════════════════════════════════════════
# FIXTURES: Random Number Control
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset_random_seed():
    """Reset random seed before each test for reproducibility."""
    random.seed(42)
    # Also reset numpy if used
    try:
        import numpy as np
        np.random.seed(42)
    except ImportError:
        pass
    yield
    # Test runs with fixed seed


# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def approximately_equal(a, b, tolerance=1e-6):
    """Check if two floats are approximately equal."""
    return abs(a - b) < tolerance


def generate_frames(generator, count):
    """Generate a specific number of frames from a generator."""
    frames = []
    for i, frame in enumerate(generator.generate_frames()):
        if i >= count:
            break
        frames.append(frame)
    return frames
