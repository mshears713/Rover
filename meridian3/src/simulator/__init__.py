"""
Simulator Subsystem

This subsystem generates realistic rover telemetry data by modeling:
    - Rover physical state (position, orientation, power, thermal)
    - Sensor behavior (cameras, IMU, power monitors, thermal sensors)
    - Environmental effects (terrain, dust, radiation, temperature cycles)
    - Time progression and orbital mechanics

Teaching Purpose:
    Shows how to build a deterministic simulation with controllable randomness.
    Demonstrates object-oriented modeling of physical systems.
    Illustrates the separation between state, sensors, environment, and orchestration.

Architecture Diagram:
    ┌─────────────┐
    │ Environment │  ← terrain, hazards, orbital position
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ RoverState  │  ← position, attitude, power, thermal
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   Sensors   │  ← read state, apply noise, produce readings
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Generator  │  ← orchestrates simulation loop
    └─────────────┘
"""
