"""
Pipeline Subsystem

This subsystem processes raw sensor data through a realistic telemetry pipeline:
    - Packetizer: Encodes sensor frames into transmission packets
    - Corruptor: Simulates packet loss, corruption, and transmission errors
    - Cleaner: Validates and repairs degraded data
    - Anomaly Detector: Identifies unusual patterns and potential issues
    - Storage: Archives mission data for analysis

Teaching Purpose:
    Demonstrates real-world data engineering challenges.
    Shows how to handle incomplete, noisy, and corrupted data.
    Illustrates defensive programming and data validation strategies.

Pipeline Flow:
    Raw Frames → Packets → Corrupted Packets → Cleaned Frames → Labeled Frames → Storage
         ↓           ↓            ↓                  ↓               ↓            ↓
    [Sensor]   [Encode]    [Transmit]          [Validate]      [Analyze]     [Archive]
"""
