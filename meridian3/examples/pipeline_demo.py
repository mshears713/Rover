"""
Complete Telemetry Pipeline Demonstration

This script demonstrates the full telemetry pipeline from simulation
to storage, showing how all Phase 3 components work together.

PIPELINE FLOW:
    Simulator → Packetizer → Corruptor → Cleaner → Anomaly Detector → Storage

TEACHING PURPOSE:
    This end-to-end example shows:
        1. How components integrate
        2. Data transformations at each stage
        3. Error handling and recovery
        4. Statistics and monitoring
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simulator.generator import SimulationGenerator
from pipeline.packetizer import Packetizer
from pipeline.corruptor import Corruptor
from pipeline.cleaner import Cleaner
from pipeline.anomalies import AnomalyDetector
from pipeline.storage import MissionStorage
from utils.pipeline_debug import PipelineDebugger


def run_pipeline_demo(
    duration: float = 60.0,
    corruption_rate: float = 0.05,
    show_debug: bool = True
):
    """
    Run complete pipeline demonstration.

    Args:
        duration: Simulation duration in seconds
        corruption_rate: Packet corruption rate (0.0-1.0)
        show_debug: If True, show detailed debugging output
    """
    print("=" * 70)
    print("MERIDIAN-3 TELEMETRY PIPELINE DEMONSTRATION")
    print("=" * 70)
    print()

    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Initialize Pipeline Components
    # ═══════════════════════════════════════════════════════════════
    print("Initializing pipeline components...")

    # Simulator: Generates realistic rover telemetry
    simulator = SimulationGenerator(
        timestep=1.0,          # 1 second per frame
        max_duration=duration,
        random_seed=42         # Reproducible results
    )

    # Packetizer: Wraps frames in transmission packets
    packetizer = Packetizer(encoding="raw")

    # Corruptor: Simulates transmission errors
    corruptor = Corruptor(
        packet_loss_rate=0.01,               # 1% packet loss
        field_corruption_rate=corruption_rate,
        jitter_stddev=0.1,
        random_seed=42
    )

    # Cleaner: Repairs corrupted data
    cleaner = Cleaner(history_size=10)

    # Anomaly Detector: Identifies unusual patterns
    detector = AnomalyDetector(
        history_size=50,
        z_score_threshold=3.0
    )

    # Storage: Persists telemetry to database
    db_path = os.path.join(os.path.dirname(__file__), '../data/demo_mission.db')
    storage = MissionStorage(db_path, cache_size=100)

    # Debugger: Traces pipeline execution
    debugger = PipelineDebugger(verbose=False)

    print("✓ All components initialized")
    print()

    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Run Pipeline
    # ═══════════════════════════════════════════════════════════════
    print(f"Running simulation for {duration} seconds...")
    print()

    frame_count = 0
    traces_to_show = 3  # Show first 3 traces in detail

    for raw_frame in simulator.generate_frames():
        frame_count += 1

        # Stage 1: Packetize
        packet = packetizer.encode_frame(raw_frame)

        # Stage 2: Corrupt
        corrupted_packet = corruptor.corrupt_packet(packet)

        # Stage 3: Clean
        clean_frame = cleaner.clean_packet(corrupted_packet)

        # Skip if unrecoverable
        if clean_frame is None:
            continue

        # Stage 4: Detect Anomalies
        labeled_frame = detector.analyze_frame(clean_frame)

        # Stage 5: Store
        storage.store_frame(labeled_frame, mission_id="demo_2025")

        # Debug trace
        if show_debug and frame_count <= traces_to_show:
            trace = debugger.trace_pipeline(
                raw_frame=raw_frame,
                packet=packet,
                corrupted_packet=corrupted_packet,
                clean_frame=clean_frame,
                labeled_frame=labeled_frame
            )
            debugger.print_trace(trace)

        # Progress indicator
        if frame_count % 10 == 0:
            print(f"Processed {frame_count} frames...")

    print()
    print(f"✓ Simulation complete: {frame_count} frames processed")
    print()

    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Display Statistics
    # ═══════════════════════════════════════════════════════════════
    print("=" * 70)
    print("PIPELINE STATISTICS")
    print("=" * 70)
    print()

    # Packetizer stats
    print("┌─ Packetizer:")
    pack_stats = packetizer.get_statistics()
    for key, value in pack_stats.items():
        if isinstance(value, float):
            print(f"│  {key}: {value:.2f}")
        else:
            print(f"│  {key}: {value}")
    print()

    # Corruptor stats
    print("┌─ Corruptor:")
    corr_stats = corruptor.get_statistics()
    for key, value in corr_stats.items():
        if 'rate' in key:
            print(f"│  {key}: {value:.2%}")
        else:
            print(f"│  {key}: {value}")
    print()

    # Cleaner stats
    print("┌─ Cleaner:")
    clean_stats = cleaner.get_statistics()
    for key, value in clean_stats.items():
        if 'rate' in key:
            print(f"│  {key}: {value:.2%}")
        else:
            print(f"│  {key}: {value}")
    print()

    # Detector stats
    print("┌─ Anomaly Detector:")
    detect_stats = detector.get_statistics()
    for key, value in detect_stats.items():
        if 'rate' in key:
            print(f"│  {key}: {value:.4f}")
        else:
            print(f"│  {key}: {value}")
    print()

    # Storage stats
    print("┌─ Storage:")
    storage_stats = storage.get_statistics()
    for key, value in storage_stats.items():
        if 'rate' in key:
            print(f"│  {key}: {value:.2%}")
        elif 'mb' in key:
            print(f"│  {key}: {value:.2f}")
        elif 'bytes' in key:
            print(f"│  {key}: {value:,}")
        else:
            print(f"│  {key}: {value}")
    print()

    # ═══════════════════════════════════════════════════════════════
    # STEP 4: Query and Display Results
    # ═══════════════════════════════════════════════════════════════
    print("=" * 70)
    print("SAMPLE QUERIES")
    print("=" * 70)
    print()

    # Query 1: Latest frames
    print("┌─ Latest 5 Frames:")
    latest = storage.get_latest(5, mission_id="demo_2025")
    for frame in latest:
        timestamp = frame.get('timestamp', 'N/A')
        quality = frame.get('metadata', {}).get('quality', 'unknown')
        anomaly_count = len(frame.get('metadata', {}).get('anomalies', []))
        print(f"│  t={timestamp:6.1f}s  quality={quality:12}  anomalies={anomaly_count}")
    print()

    # Query 2: Anomalies
    print("┌─ Critical Anomalies:")
    critical = storage.get_anomalies(severity='critical', limit=5, mission_id="demo_2025")
    if critical:
        for anomaly in critical:
            print(f"│  t={anomaly['timestamp']:6.1f}s  {anomaly['description']}")
    else:
        print("│  No critical anomalies found")
    print()

    # Query 3: Time range query
    print("┌─ Frames from t=10-20 seconds:")
    frames_10_20 = storage.query_frames(10.0, 20.0, mission_id="demo_2025")
    print(f"│  Found {len(frames_10_20)} frames in this range")
    print()

    # ═══════════════════════════════════════════════════════════════
    # STEP 5: Cleanup
    # ═══════════════════════════════════════════════════════════════
    storage.close()

    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Database saved to: {db_path}")
    print()


if __name__ == "__main__":
    # Run demo with default parameters
    run_pipeline_demo(
        duration=60.0,      # 1 minute of simulated time
        corruption_rate=0.10,  # 10% field corruption (higher for demo visibility)
        show_debug=True     # Show detailed traces for first few frames
    )
