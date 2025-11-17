"""
Anomaly Detection - Pattern Recognition and Event Labeling

PURPOSE:
    Identifies unusual patterns in telemetry that may indicate hardware issues,
    environmental hazards, or interesting science opportunities. Implements
    multiple detection strategies from simple thresholding to statistical methods.

THEORY:
    Anomaly detection is about finding "interesting" events - deviations from
    normal behavior that warrant attention. Approaches include:

        1. Threshold Detection: Simple bounds checking
            - Battery SoC < 20% → Low power alarm
            - Temperature > 50°C → Overheat warning
            - Fast, deterministic, easy to explain

        2. Derivative/Rate-of-Change: Detect sudden changes
            - Battery drops 10% in 1 minute → Fault
            - Temperature spikes 20°C instantly → Sensor glitch
            - Catches transient events, ignores slow drifts

        3. Z-Score (Standard Deviation): Statistical outliers
            - Calculate mean and stddev from history
            - Flag values > 3 sigma from mean
            - Adapts to data distribution, catches unusual patterns

        4. Multi-field Correlation: Cross-validate readings
            - High current but low velocity → Motor stall
            - Low solar power but high sun angle → Panel fault
            - Requires domain knowledge, powerful for diagnostics

MERIDIAN-3 STORY SNIPPET:
    "Sol 89: The anomaly detector flagged something odd. Battery discharge
    rate had tripled with no change in activity. Not a threshold violation -
    SoC was still at 60%. But the *rate* was wrong. Three standard deviations
    above normal. Investigation revealed a short circuit in the heater control.
    We caught it before it drained the battery completely. Derivative detection
    saved the mission."

ARCHITECTURE ROLE:
    The Anomaly Detector sits downstream of the Cleaner and upstream of Storage.
    It receives clean, validated data and adds semantic labels: "normal",
    "warning", "critical", "interesting". These labels help operators prioritize.

    Cleaner → Anomaly Detector → Storage → Mission Console

DETECTION PIPELINE DIAGRAM:

    ╔══════════════════════════════════════════════════════════════╗
    ║                 ANOMALY DETECTION PIPELINE                   ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  Clean Frame                                                 ║
    ║      │                                                       ║
    ║      ▼                                                       ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 1: Threshold Detection         │                   ║
    ║  │  Check each field against limits     │                   ║
    ║  │  → Generate threshold anomalies      │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 2: Derivative Detection        │                   ║
    ║  │  Calculate rate of change            │                   ║
    ║  │  → Flag sudden jumps/drops           │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 3: Statistical (Z-Score)       │                   ║
    ║  │  Compare to running statistics       │                   ║
    ║  │  → Detect statistical outliers       │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 4: Aggregate & Prioritize      │                   ║
    ║  │  Combine all detections              │                   ║
    ║  │  → Assign severity levels            │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  Labeled Frame (with anomalies list)                         ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

TEACHING GOALS:
    - Anomaly detection algorithms
    - Statistical process control
    - Pattern recognition
    - Alert generation and prioritization
    - Balancing false positives vs false negatives

DEBUGGING NOTES:
    - Too many alerts? Raise thresholds or z-score cutoff
    - Missing real anomalies? Lower thresholds, check history depth
    - False positives on startup? Detectors need warmup period
    - Test with synthetic anomalies to validate detection
    - Use verbose mode to see detection reasoning

FUTURE EXTENSIONS:
    1. Add machine learning-based anomaly detection (autoencoders)
    2. Implement time-series forecasting with anomaly on prediction error
    3. Add multi-variate anomaly detection (correlation analysis)
    4. Implement adaptive thresholds based on mission phase
    5. Add anomaly clustering (group related events)
    6. Support user-defined custom detectors
    7. Add confidence scores and uncertainty quantification
"""

import math
from typing import Dict, Any, List, Optional
from collections import deque
from dataclasses import dataclass


@dataclass
class Anomaly:
    """
    Represents a detected anomaly.

    Attributes:
        field: Name of telemetry field with anomaly
        value: Actual value observed
        anomaly_type: Type of detection (threshold/derivative/z-score)
        severity: Criticality level (info/warning/critical)
        description: Human-readable explanation
        timestamp: When anomaly occurred
    """
    field: str
    value: float
    anomaly_type: str
    severity: str
    description: str
    timestamp: float


class AnomalyDetector:
    """
    Detects and labels anomalous telemetry patterns.

    Implements multiple detection strategies to find interesting events
    in rover telemetry data.
    """

    # Threshold definitions
    # Format: field_name: (warning_threshold, critical_threshold)
    THRESHOLDS = {
        # Battery thresholds
        'battery_soc': {
            'low_warning': 30.0,
            'low_critical': 15.0,
        },
        'battery_temp': {
            'high_warning': 45.0,
            'high_critical': 55.0,
            'low_warning': -10.0,
            'low_critical': -20.0,
        },
        'battery_voltage': {
            'low_warning': 24.0,
            'low_critical': 22.0,
        },
        # Thermal thresholds
        'motor_temp': {
            'high_warning': 60.0,
            'high_critical': 75.0,
        },
        'electronics_temp': {
            'high_warning': 55.0,
            'high_critical': 65.0,
        },
    }

    # Derivative (rate of change) limits
    # Format: field_name: max_safe_rate_per_second
    DERIVATIVE_LIMITS = {
        'battery_soc': 2.0,          # 2%/sec is suspicious
        'battery_temp': 5.0,         # 5°C/sec is very fast
        'battery_voltage': 1.0,      # Voltage shouldn't jump quickly
    }

    def __init__(self, history_size: int = 50, z_score_threshold: float = 3.0):
        """
        Initialize anomaly detector with detection parameters.

        Args:
            history_size: Number of frames to keep for statistical analysis
                - Larger = better statistics, slower adaptation
                - Smaller = faster adaptation, more noise
                - Default: 50 frames

            z_score_threshold: Number of standard deviations for outlier
                - 3.0 = 99.7% confidence interval (typical)
                - 2.0 = 95% confidence (more sensitive)
                - 4.0 = 99.99% confidence (less sensitive)
                - Default: 3.0

        Teaching Note:
            Z-score threshold is a tradeoff:
                - High threshold: Miss subtle anomalies
                - Low threshold: Too many false alarms
                - Standard practice: 3.0 for automated systems
        """
        self.history_size = history_size
        self.z_score_threshold = z_score_threshold

        # History for statistical analysis
        # Format: field_name -> deque of (timestamp, value) tuples
        self.field_history: Dict[str, deque] = {}

        # Last frame for derivative calculations
        self.last_frame: Optional[Dict] = None

        # Statistics tracking
        self.stats = {
            'frames_analyzed': 0,
            'total_anomalies': 0,
            'threshold_anomalies': 0,
            'derivative_anomalies': 0,
            'zscore_anomalies': 0,
        }

    def analyze_frame(self, frame: dict) -> dict:
        """
        Analyze a telemetry frame for anomalies.

        This is the main entry point. It runs all detection algorithms
        and returns the frame with added anomaly labels.

        Args:
            frame: Cleaned telemetry frame from Cleaner
                Expected structure: {timestamp, frame_id, data, metadata}

        Returns:
            Frame with 'anomalies' list added to metadata

        Teaching Note:
            We run multiple detectors because different approaches
            catch different types of anomalies:
                - Thresholds: Catch absolute limit violations
                - Derivatives: Catch sudden changes
                - Z-score: Catch statistical outliers

            Combining them gives robust detection.

        Example:
            >>> detector = AnomalyDetector(history_size=50)
            >>> clean_frame = cleaner.clean_packet(packet)
            >>> labeled_frame = detector.analyze_frame(clean_frame)
            >>> if labeled_frame['metadata']['anomalies']:
            ...     print(f"Found {len(labeled_frame['metadata']['anomalies'])} anomalies")
        """
        self.stats['frames_analyzed'] += 1

        anomalies: List[Anomaly] = []

        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Threshold Detection
        # ═══════════════════════════════════════════════════════════════
        threshold_anomalies = self._detect_threshold_violations(frame)
        anomalies.extend(threshold_anomalies)
        self.stats['threshold_anomalies'] += len(threshold_anomalies)

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Derivative Detection (Rate of Change)
        # ═══════════════════════════════════════════════════════════════
        derivative_anomalies = self._detect_derivative_anomalies(frame)
        anomalies.extend(derivative_anomalies)
        self.stats['derivative_anomalies'] += len(derivative_anomalies)

        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Statistical Outlier Detection (Z-Score)
        # ═══════════════════════════════════════════════════════════════
        zscore_anomalies = self._detect_statistical_outliers(frame)
        anomalies.extend(zscore_anomalies)
        self.stats['zscore_anomalies'] += len(zscore_anomalies)

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Update History
        # ═══════════════════════════════════════════════════════════════
        self._update_history(frame)

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Add Anomalies to Frame Metadata
        # ═══════════════════════════════════════════════════════════════
        if 'anomalies' not in frame['metadata']:
            frame['metadata']['anomalies'] = []

        frame['metadata']['anomalies'] = [
            {
                'field': a.field,
                'value': a.value,
                'type': a.anomaly_type,
                'severity': a.severity,
                'description': a.description,
                'timestamp': a.timestamp,
            }
            for a in anomalies
        ]

        self.stats['total_anomalies'] += len(anomalies)

        # Store this frame for next iteration's derivative calculations
        self.last_frame = frame

        return frame

    def _detect_threshold_violations(self, frame: dict) -> List[Anomaly]:
        """
        Detect simple threshold violations.

        Checks if values exceed predefined warning/critical limits.

        Args:
            frame: Telemetry frame to analyze

        Returns:
            List of threshold anomalies detected

        Teaching Note:
            Thresholds are the simplest and most explainable detectors.
            They're defined by domain experts based on hardware specs
            and operational experience. Easy to debug and justify.
        """
        anomalies = []
        timestamp = frame['timestamp']

        for field_name, value in frame['data'].items():
            if field_name not in self.THRESHOLDS:
                continue  # No thresholds defined for this field

            if not isinstance(value, (int, float)):
                continue  # Can't check thresholds on non-numeric values

            thresholds = self.THRESHOLDS[field_name]

            # Check low thresholds (if defined)
            if 'low_critical' in thresholds and value < thresholds['low_critical']:
                anomalies.append(Anomaly(
                    field=field_name,
                    value=value,
                    anomaly_type='threshold',
                    severity='critical',
                    description=f"{field_name} critically low: {value:.2f}",
                    timestamp=timestamp
                ))
            elif 'low_warning' in thresholds and value < thresholds['low_warning']:
                anomalies.append(Anomaly(
                    field=field_name,
                    value=value,
                    anomaly_type='threshold',
                    severity='warning',
                    description=f"{field_name} low: {value:.2f}",
                    timestamp=timestamp
                ))

            # Check high thresholds (if defined)
            if 'high_critical' in thresholds and value > thresholds['high_critical']:
                anomalies.append(Anomaly(
                    field=field_name,
                    value=value,
                    anomaly_type='threshold',
                    severity='critical',
                    description=f"{field_name} critically high: {value:.2f}",
                    timestamp=timestamp
                ))
            elif 'high_warning' in thresholds and value > thresholds['high_warning']:
                anomalies.append(Anomaly(
                    field=field_name,
                    value=value,
                    anomaly_type='threshold',
                    severity='warning',
                    description=f"{field_name} high: {value:.2f}",
                    timestamp=timestamp
                ))

        return anomalies

    def _detect_derivative_anomalies(self, frame: dict) -> List[Anomaly]:
        """
        Detect anomalous rates of change.

        Compares current value to previous value and flags if change
        rate exceeds expected limits.

        Args:
            frame: Current telemetry frame

        Returns:
            List of derivative anomalies detected

        Teaching Note:
            Derivative detection catches transient events that threshold
            detection might miss. For example, battery at 50% is fine,
            but dropping from 70% to 50% in 10 seconds is not.
        """
        anomalies = []

        if self.last_frame is None:
            return anomalies  # Need previous frame for derivative

        timestamp = frame['timestamp']
        last_timestamp = self.last_frame['timestamp']
        dt = timestamp - last_timestamp

        if dt <= 0:
            return anomalies  # Invalid time delta

        for field_name, value in frame['data'].items():
            if field_name not in self.DERIVATIVE_LIMITS:
                continue

            if not isinstance(value, (int, float)):
                continue

            # Get previous value
            if field_name not in self.last_frame['data']:
                continue

            last_value = self.last_frame['data'][field_name]
            if not isinstance(last_value, (int, float)):
                continue

            # Calculate rate of change
            delta = abs(value - last_value)
            rate = delta / dt  # Units: value_units per second

            max_rate = self.DERIVATIVE_LIMITS[field_name]

            if rate > max_rate:
                # Determine severity based on how much limit was exceeded
                if rate > max_rate * 2.0:
                    severity = 'critical'
                else:
                    severity = 'warning'

                anomalies.append(Anomaly(
                    field=field_name,
                    value=value,
                    anomaly_type='derivative',
                    severity=severity,
                    description=(
                        f"{field_name} changed too fast: "
                        f"{rate:.2f}/s (limit: {max_rate:.2f}/s)"
                    ),
                    timestamp=timestamp
                ))

        return anomalies

    def _detect_statistical_outliers(self, frame: dict) -> List[Anomaly]:
        """
        Detect statistical outliers using z-score.

        Compares current value to historical mean and standard deviation.
        Flags values that are statistically unlikely.

        Args:
            frame: Current telemetry frame

        Returns:
            List of statistical anomalies detected

        Teaching Note:
            Z-score detection is adaptive - it learns from the data.
            Good for catching subtle anomalies that don't violate fixed
            thresholds but are unusual for this mission/rover/environment.

            Limitation: Needs warmup period (enough history) to work well.
        """
        anomalies = []
        timestamp = frame['timestamp']

        for field_name, value in frame['data'].items():
            if not isinstance(value, (int, float)):
                continue

            # Need sufficient history for statistics
            if field_name not in self.field_history:
                continue

            history = self.field_history[field_name]
            if len(history) < 10:  # Need at least 10 points
                continue

            # Calculate mean and standard deviation
            values = [v for (t, v) in history]
            mean = sum(values) / len(values)

            # Standard deviation calculation
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            stddev = math.sqrt(variance)

            # Avoid division by zero
            if stddev < 1e-6:
                continue  # No variation in data, can't detect outliers

            # Calculate z-score
            z_score = abs(value - mean) / stddev

            if z_score > self.z_score_threshold:
                # Determine severity based on z-score magnitude
                if z_score > self.z_score_threshold * 1.5:
                    severity = 'critical'
                else:
                    severity = 'warning'

                anomalies.append(Anomaly(
                    field=field_name,
                    value=value,
                    anomaly_type='z-score',
                    severity=severity,
                    description=(
                        f"{field_name} statistical outlier: "
                        f"value={value:.2f}, z-score={z_score:.2f}, "
                        f"mean={mean:.2f}, stddev={stddev:.2f}"
                    ),
                    timestamp=timestamp
                ))

        return anomalies

    def _update_history(self, frame: dict):
        """
        Update historical data for statistical analysis.

        Args:
            frame: Current telemetry frame

        Teaching Note:
            We maintain a sliding window of history. As new data arrives,
            old data is discarded. This allows the detector to adapt to
            changing conditions (e.g., day/night temperature differences).
        """
        timestamp = frame['timestamp']

        for field_name, value in frame['data'].items():
            if not isinstance(value, (int, float)):
                continue  # Only track numeric fields

            # Initialize history for this field if needed
            if field_name not in self.field_history:
                self.field_history[field_name] = deque(maxlen=self.history_size)

            # Add new value
            self.field_history[field_name].append((timestamp, value))

    def get_statistics(self) -> dict:
        """
        Get anomaly detection statistics.

        Returns:
            Dictionary with detection counts and rates

        Teaching Note:
            Statistics help tune detection parameters. High anomaly rates
            suggest thresholds are too tight. Very low rates might mean
            detectors aren't sensitive enough.
        """
        anomaly_rate = 0.0
        if self.stats['frames_analyzed'] > 0:
            anomaly_rate = (
                self.stats['total_anomalies'] / self.stats['frames_analyzed']
            )

        return {
            'frames_analyzed': self.stats['frames_analyzed'],
            'total_anomalies': self.stats['total_anomalies'],
            'threshold_anomalies': self.stats['threshold_anomalies'],
            'derivative_anomalies': self.stats['derivative_anomalies'],
            'zscore_anomalies': self.stats['zscore_anomalies'],
            'anomaly_rate': anomaly_rate,
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'frames_analyzed': 0,
            'total_anomalies': 0,
            'threshold_anomalies': 0,
            'derivative_anomalies': 0,
            'zscore_anomalies': 0,
        }

    def clear_history(self):
        """
        Clear all historical data.

        Useful when starting a new mission or after long gaps.
        """
        self.field_history.clear()
        self.last_frame = None


# ═══════════════════════════════════════════════════════════════
# DEBUGGING AND TESTING HELPERS
# ═══════════════════════════════════════════════════════════════

def test_anomaly_detector():
    """
    Test function to demonstrate anomaly detection.

    Shows:
        1. Threshold detection (low battery)
        2. Derivative detection (sudden change)
        3. Z-score detection (statistical outlier)
        4. Statistics tracking
    """
    print("Testing Anomaly Detector...")
    print()

    detector = AnomalyDetector(history_size=20, z_score_threshold=2.0)

    # Test Case 1: Normal frames (build history)
    print("Test 1: Building history with normal frames...")
    for i in range(15):
        normal_frame = {
            'timestamp': float(i),
            'frame_id': i,
            'data': {
                'battery_soc': 75.0 + (i * 0.1),  # Slowly increasing
                'battery_temp': 20.0,
                'battery_voltage': 28.0,
            },
            'metadata': {'quality': 'high'}
        }
        result = detector.analyze_frame(normal_frame)
        print(f"  Frame {i}: {len(result['metadata']['anomalies'])} anomalies")

    print()

    # Test Case 2: Threshold violation (low battery)
    print("Test 2: Threshold violation (low battery)")
    low_battery_frame = {
        'timestamp': 16.0,
        'frame_id': 16,
        'data': {
            'battery_soc': 10.0,  # Critical low!
            'battery_temp': 20.0,
            'battery_voltage': 28.0,
        },
        'metadata': {'quality': 'high'}
    }
    result = detector.analyze_frame(low_battery_frame)
    if result['metadata']['anomalies']:
        for anomaly in result['metadata']['anomalies']:
            print(f"  {anomaly['severity'].upper()}: {anomaly['description']}")
    print()

    # Test Case 3: Derivative anomaly (sudden temp change)
    print("Test 3: Derivative anomaly (sudden temperature change)")
    sudden_temp_frame = {
        'timestamp': 17.0,
        'frame_id': 17,
        'data': {
            'battery_soc': 75.0,
            'battery_temp': 40.0,  # Jumped from 20°C to 40°C in 1 sec!
            'battery_voltage': 28.0,
        },
        'metadata': {'quality': 'high'}
    }
    result = detector.analyze_frame(sudden_temp_frame)
    if result['metadata']['anomalies']:
        for anomaly in result['metadata']['anomalies']:
            print(f"  {anomaly['severity'].upper()}: {anomaly['description']}")
    print()

    # Test Case 4: Statistical outlier (unusual voltage)
    print("Test 4: Statistical outlier (unusual voltage)")
    outlier_frame = {
        'timestamp': 18.0,
        'frame_id': 18,
        'data': {
            'battery_soc': 75.0,
            'battery_temp': 40.0,
            'battery_voltage': 35.0,  # Much higher than historical mean of 28.0
        },
        'metadata': {'quality': 'high'}
    }
    result = detector.analyze_frame(outlier_frame)
    if result['metadata']['anomalies']:
        for anomaly in result['metadata']['anomalies']:
            print(f"  {anomaly['severity'].upper()}: {anomaly['description']}")
    print()

    # Show statistics
    stats = detector.get_statistics()
    print("Anomaly Detector Statistics:")
    for key, value in stats.items():
        if 'rate' in key:
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    print()

    print("Anomaly Detector test complete!")


if __name__ == "__main__":
    test_anomaly_detector()
