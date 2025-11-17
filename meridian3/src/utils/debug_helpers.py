"""
Debug Helpers - Visualization and Inspection Tools for Simulation

PURPOSE:
    Provides debugging and visualization utilities for inspecting simulation
    state, sensor outputs, and system behavior. Essential for development,
    testing, and educational demonstrations.

THEORY:
    Debugging complex simulations requires visibility into:
        - Current state snapshots (what's happening now?)
        - Time series trends (how did we get here?)
        - Sensor accuracy (how noisy are readings?)
        - Anomaly detection (what went wrong?)

    Good debugging tools should:
        - Be easy to invoke (simple function calls)
        - Provide clear, readable output
        - Support both text and visual inspection
        - Help identify root causes quickly

TEACHING GOALS:
    - Importance of observability in complex systems
    - Debugging strategies for multi-component systems
    - Data visualization for time series
    - Statistical analysis of sensor data

DEBUGGING NOTES:
    - These tools are meant for development, not production
    - They may slow down simulation (lots of printing/plotting)
    - Use selectively - don't leave debug prints in tight loops
    - Consider logging to files for long simulations

FUTURE EXTENSIONS:
    - Add real-time plotting with matplotlib
    - Implement interactive debugging console
    - Add performance profiling tools
    - Create automatic anomaly reports
"""

from typing import Dict, List, Any, Optional
import sys


# ═══════════════════════════════════════════════════════════════
# STATE INSPECTION
# ═══════════════════════════════════════════════════════════════

def print_rover_state(rover_state, title: str = "Rover State Snapshot"):
    """
    Print a formatted snapshot of rover state.

    Args:
        rover_state: RoverState object to inspect
        title: Header title for the output

    Example:
        from src.simulator.rover_state import RoverState
        from src.utils.debug_helpers import print_rover_state

        rover = RoverState()
        print_rover_state(rover, "Initial State")
    """
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

    print("\n📍 POSITION & ORIENTATION:")
    print(f"   Location: ({rover_state.x:.2f}, {rover_state.y:.2f}, {rover_state.z:.2f}) m")
    print(f"   Heading:  {rover_state.heading:.1f}°")
    print(f"   Roll:     {rover_state.roll:.1f}°")
    print(f"   Pitch:    {rover_state.pitch:.1f}°")
    print(f"   Velocity: {rover_state.velocity:.3f} m/s")

    print("\n🔋 POWER SYSTEM:")
    print(f"   Battery SoC:     {rover_state.battery_soc:.1f}%")
    print(f"   Battery Voltage: {rover_state.battery_voltage:.2f}V")
    print(f"   Battery Current: {rover_state.battery_current:+.2f}A  {'⚡ Charging' if rover_state.is_charging else '⚠  Discharging'}")
    print(f"   Solar Voltage:   {rover_state.solar_panel_voltage:.2f}V")
    print(f"   Solar Current:   {rover_state.solar_panel_current:.2f}A")

    print("\n🌡️  THERMAL STATE:")
    print(f"   CPU Temp:     {rover_state.cpu_temp:.1f}°C")
    print(f"   Battery Temp: {rover_state.battery_temp:.1f}°C")
    print(f"   Motor Temp:   {rover_state.motor_temp:.1f}°C")
    print(f"   Chassis Temp: {rover_state.chassis_temp:.1f}°C")
    print(f"   Heater:       {'🔥 ACTIVE' if rover_state.heater_active else '   off'}")

    print("\n🕒 MISSION TIME:")
    print(f"   Mission Time: {rover_state.mission_time:.1f}s")
    print(f"   Sol:          {rover_state.sol}")
    print(f"   Local Time:   {rover_state.local_time:.1f}s")

    print("\n🚀 STATUS FLAGS:")
    print(f"   Moving:          {'✓' if rover_state.is_moving else '✗'}")
    print(f"   Charging:        {'✓' if rover_state.is_charging else '✗'}")
    print(f"   Heater Active:   {'✓' if rover_state.heater_active else '✗'}")
    print(f"   Science Active:  {'✓' if rover_state.science_active else '✗'}")

    print("=" * 60 + "\n")


def print_telemetry_frame(frame: Dict[str, Any], title: str = "Telemetry Frame"):
    """
    Print a formatted telemetry frame.

    Args:
        frame: Telemetry frame dictionary
        title: Header title

    Example:
        # After reading sensors
        telemetry = sensors.read_all(rover, mission_time)
        print_telemetry_frame(telemetry)
    """
    print("\n" + "-" * 60)
    print(f"  {title}")
    print("-" * 60)

    print(f"\n📊 Frame #{frame.get('frame_id', '?')}")
    print(f"   Timestamp: {frame.get('timestamp', 0):.2f}s")

    if 'roll' in frame:
        print("\n   IMU Readings:")
        print(f"      Roll:    {frame['roll']:.2f}°")
        print(f"      Pitch:   {frame['pitch']:.2f}°")
        print(f"      Heading: {frame['heading']:.2f}°")

    if 'battery_voltage' in frame:
        print("\n   Power Readings:")
        print(f"      Battery V: {frame['battery_voltage']:.2f}V")
        print(f"      Battery I: {frame['battery_current']:+.2f}A")
        print(f"      Battery SoC: {frame['battery_soc']:.1f}%")

    if 'cpu_temp' in frame:
        print("\n   Thermal Readings:")
        print(f"      CPU:     {frame['cpu_temp']:.1f}°C")
        print(f"      Battery: {frame['battery_temp']:.1f}°C")
        print(f"      Motor:   {frame['motor_temp']:.1f}°C")

    print("-" * 60 + "\n")


def compare_state_vs_sensors(rover_state, telemetry_frame):
    """
    Compare true rover state vs noisy sensor readings.

    Helps visualize sensor noise and drift.

    Args:
        rover_state: True RoverState
        telemetry_frame: Noisy sensor readings

    Example:
        compare_state_vs_sensors(rover, telemetry)
    """
    print("\n" + "=" * 70)
    print("  TRUE STATE vs SENSOR READINGS (Error Analysis)")
    print("=" * 70)

    def format_comparison(name: str, true_val: float, measured_val: float, unit: str):
        error = measured_val - true_val
        percent_error = (abs(error) / abs(true_val)) * 100 if true_val != 0 else 0
        print(f"   {name:15s}:  True={true_val:8.2f}{unit}  "
              f"Measured={measured_val:8.2f}{unit}  "
              f"Error={error:+6.2f}{unit} ({percent_error:5.2f}%)")

    print("\n📐 Orientation:")
    format_comparison("Roll", rover_state.roll, telemetry_frame['roll'], "°")
    format_comparison("Pitch", rover_state.pitch, telemetry_frame['pitch'], "°")
    format_comparison("Heading", rover_state.heading, telemetry_frame['heading'], "°")

    print("\n🔋 Power:")
    format_comparison("Battery V", rover_state.battery_voltage,
                      telemetry_frame['battery_voltage'], "V")
    format_comparison("Battery SoC", rover_state.battery_soc,
                      telemetry_frame['battery_soc'], "%")

    print("\n🌡️  Temperature:")
    format_comparison("CPU Temp", rover_state.cpu_temp,
                      telemetry_frame['cpu_temp'], "°C")
    format_comparison("Battery Temp", rover_state.battery_temp,
                      telemetry_frame['battery_temp'], "°C")

    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════
# TIME SERIES ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_sensor_noise(frames: List[Dict[str, Any]], sensor_name: str):
    """
    Analyze noise characteristics of a sensor over time.

    Args:
        frames: List of telemetry frames
        sensor_name: Name of sensor field to analyze (e.g., 'cpu_temp')

    Prints statistics: mean, std deviation, min, max, range

    Example:
        # After running simulation
        frames = sim.run_mission(duration=3600)
        analyze_sensor_noise(frames, 'cpu_temp')
    """
    if not frames:
        print("No frames to analyze!")
        return

    # Extract sensor values
    values = [frame[sensor_name] for frame in frames if sensor_name in frame]

    if not values:
        print(f"Sensor '{sensor_name}' not found in frames!")
        return

    # Calculate statistics
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = variance ** 0.5
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val

    print("\n" + "=" * 60)
    print(f"  SENSOR NOISE ANALYSIS: {sensor_name}")
    print("=" * 60)
    print(f"\n   Sample Count: {n}")
    print(f"   Mean:         {mean:.4f}")
    print(f"   Std Dev:      {std_dev:.4f}")
    print(f"   Min:          {min_val:.4f}")
    print(f"   Max:          {max_val:.4f}")
    print(f"   Range:        {range_val:.4f}")
    print(f"   SNR:          {abs(mean/std_dev):.2f} (signal-to-noise ratio)")

    # Histogram (text-based)
    print("\n   Distribution (histogram):")
    n_bins = 10
    bin_width = range_val / n_bins
    bins = [0] * n_bins

    for v in values:
        bin_idx = int((v - min_val) / bin_width)
        bin_idx = min(bin_idx, n_bins - 1)  # Clamp to last bin
        bins[bin_idx] += 1

    max_count = max(bins)
    bar_width = 40
    for i, count in enumerate(bins):
        bin_start = min_val + i * bin_width
        bin_end = bin_start + bin_width
        bar_len = int((count / max_count) * bar_width) if max_count > 0 else 0
        bar = "█" * bar_len
        print(f"   [{bin_start:7.2f}-{bin_end:7.2f}]: {bar} ({count})")

    print("=" * 60 + "\n")


def print_mission_summary(frames: List[Dict[str, Any]]):
    """
    Print summary statistics for an entire mission.

    Args:
        frames: List of all telemetry frames from mission

    Example:
        frames = sim.run_mission(duration=3600)
        print_mission_summary(frames)
    """
    if not frames:
        print("No frames to summarize!")
        return

    n_frames = len(frames)
    duration = frames[-1]['timestamp'] - frames[0]['timestamp'] if n_frames > 1 else 0

    print("\n" + "=" * 70)
    print("  MISSION SUMMARY")
    print("=" * 70)

    print(f"\n📊 Mission Statistics:")
    print(f"   Total Frames:  {n_frames}")
    print(f"   Duration:      {duration:.1f} seconds ({duration/3600:.2f} hours)")
    print(f"   Sample Rate:   {n_frames/duration:.2f} Hz" if duration > 0 else "   Sample Rate: N/A")

    # Battery analysis
    if 'battery_soc' in frames[0]:
        initial_soc = frames[0]['battery_soc']
        final_soc = frames[-1]['battery_soc']
        min_soc = min(f['battery_soc'] for f in frames)
        max_soc = max(f['battery_soc'] for f in frames)

        print(f"\n🔋 Battery Performance:")
        print(f"   Initial SoC: {initial_soc:.1f}%")
        print(f"   Final SoC:   {final_soc:.1f}%")
        print(f"   Change:      {final_soc - initial_soc:+.1f}%")
        print(f"   Min SoC:     {min_soc:.1f}%")
        print(f"   Max SoC:     {max_soc:.1f}%")

    # Thermal analysis
    if 'cpu_temp' in frames[0]:
        cpu_temps = [f['cpu_temp'] for f in frames]
        min_cpu = min(cpu_temps)
        max_cpu = max(cpu_temps)
        avg_cpu = sum(cpu_temps) / len(cpu_temps)

        print(f"\n🌡️  Temperature Range:")
        print(f"   CPU:  Min={min_cpu:.1f}°C  Max={max_cpu:.1f}°C  Avg={avg_cpu:.1f}°C")

    # Hazards
    if 'env_info' in frames[0] and 'new_hazards' in frames[0]['env_info']:
        hazard_count = sum(len(f['env_info']['new_hazards']) for f in frames)
        print(f"\n⚠️  Hazard Events:")
        print(f"   Total Events: {hazard_count}")

    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════
# QUICK TESTS
# ═══════════════════════════════════════════════════════════════

def quick_sensor_test(num_samples: int = 100):
    """
    Quick test to verify sensors are producing reasonable values.

    Creates a rover, reads sensors multiple times, checks for anomalies.

    Args:
        num_samples: Number of sensor readings to test

    Returns:
        True if test passed, False if anomalies detected
    """
    # Import here to avoid circular dependencies
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    from simulator.rover_state import RoverState
    from simulator.sensors import SensorSuite

    print("\n🧪 Running Quick Sensor Test...")
    print(f"   Taking {num_samples} samples...\n")

    rover = RoverState()
    sensors = SensorSuite()
    anomalies = []

    for i in range(num_samples):
        frame = sensors.read_all(rover, mission_time=i * 1.0)

        # Check for obviously bad values
        if not (-180 <= frame['roll'] <= 180):
            anomalies.append(f"Sample {i}: Roll out of range ({frame['roll']}°)")

        if not (0 <= frame['battery_soc'] <= 100):
            anomalies.append(f"Sample {i}: SoC out of range ({frame['battery_soc']}%)")

        if not (-100 <= frame['cpu_temp'] <= 100):
            anomalies.append(f"Sample {i}: CPU temp unrealistic ({frame['cpu_temp']}°C)")

    if anomalies:
        print("❌ TEST FAILED - Anomalies detected:")
        for anomaly in anomalies[:10]:  # Show first 10
            print(f"   - {anomaly}")
        if len(anomalies) > 10:
            print(f"   ... and {len(anomalies) - 10} more")
        return False
    else:
        print("✅ TEST PASSED - All sensor readings within expected ranges")
        print(f"   {num_samples} samples checked, no anomalies found\n")
        return True


# ═══════════════════════════════════════════════════════════════
# FUTURE EXTENSION IDEAS
# ═══════════════════════════════════════════════════════════════
# def plot_timeseries(frames: List[Dict], fields: List[str]):
#     """Plot multiple sensor values over time using matplotlib."""
#     pass
#
# def interactive_debug_console():
#     """Launch interactive console to inspect simulation state."""
#     pass
#
# def generate_debug_report(frames: List[Dict], filepath: str):
#     """Generate comprehensive HTML debug report."""
#     pass
#
# def profile_simulation_performance():
#     """Measure which parts of simulation are slowest."""
#     pass
