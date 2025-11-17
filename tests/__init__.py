"""
Meridian-3 Rover Simulation Test Suite

This package contains comprehensive tests for all components of the
Meridian-3 rover simulation system.

Test Structure:
    - test_simulator/: Tests for simulator components (RoverState, Sensors, Environment, Generator)
    - test_pipeline/: Tests for pipeline components (Packetizer, Corruptor, Cleaner, Anomalies, Storage)
    - test_utils/: Tests for utility modules (math_helpers, timing)
    - test_integration/: Integration and end-to-end tests

Testing Philosophy:
    - Each component is tested in isolation with mocked dependencies
    - Integration tests verify components work together correctly
    - Edge cases are explicitly tested
    - Random seeds are used for reproducibility
"""
