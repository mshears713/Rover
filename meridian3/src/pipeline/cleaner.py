"""
Cleaner - Data Validation and Repair

PURPOSE:
    Validates incoming telemetry, detects corruption, and attempts repair
    through interpolation, extrapolation, and sanity checking. This is
    the "data quality" layer that ensures downstream systems receive
    usable information.

THEORY:
    Data cleaning is a critical part of any telemetry pipeline. Strategies include:

        1. Range Checking: Validate values are physically possible
            - Battery voltage: 20-35V (cell chemistry limits)
            - Temperature: -100°C to +60°C (Mars environment)
            - Roll/Pitch: -180° to +180° (geometric bounds)

        2. Interpolation: Fill gaps from missing data
            - Linear: Assume straight-line change between points
            - Last-value: Hold previous value until new one arrives
            - Zero/Default: Use conservative fallback value

        3. Checksum Validation: Detect corrupted packets
            - Compare calculated vs transmitted checksum
            - Mark packets as suspect if mismatch detected

        4. Statistical Outlier Detection: Find impossible jumps
            - Battery can't change 50% in 1 second
            - Position can't teleport 1000m instantly
            - Temperature changes are bounded by heat capacity

        5. Fallback Strategies: When repair fails
            - Mark field as "unknown" with confidence=0
            - Use model predictions (physics-based estimates)
            - Request retransmission (if possible)

MERIDIAN-3 STORY SNIPPET:
    "Sol 47: We received a temperature reading of -999°C. Impossible. The
    sensor must have glitched. Our cleaner flagged it, checked the previous
    ten readings (all around -15°C), and interpolated: probably -14.8°C.
    Not perfect, but good enough to keep the mission going. The alternative?
    Shut down and wait for fresh data. In space, waiting can be fatal."

ARCHITECTURE ROLE:
    The Cleaner sits downstream of the Corruptor and upstream of the
    Anomaly Detector. Its job: make messy data usable while preserving
    truth. It's a balance between correction and over-correction.

    Corruptor → Cleaner → Anomaly Detector → Storage

CLEANING PIPELINE DIAGRAM:

    ╔══════════════════════════════════════════════════════════════╗
    ║                    CLEANING PIPELINE                         ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  Corrupted Packet                                            ║
    ║      │                                                       ║
    ║      ▼                                                       ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 1: Checksum Validation         │                   ║
    ║  │  Valid? Mark packet quality          │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 2: Extract Telemetry           │                   ║
    ║  │  Pull data from packet payload       │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 3: Field-by-Field Validation   │                   ║
    ║  │  For each field:                     │                   ║
    ║  │    - Check if None/missing           │                   ║
    ║  │    - Check data type                 │                   ║
    ║  │    - Check range bounds              │                   ║
    ║  │    - Check rate of change            │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 4: Repair Attempts             │                   ║
    ║  │  - Interpolate from history          │                   ║
    ║  │  - Clamp to valid range              │                   ║
    ║  │  - Use last known good value         │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 5: Add Quality Metadata        │                   ║
    ║  │  Tag repaired fields & confidence    │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  Clean Telemetry Frame                                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

TEACHING GOALS:
    - Data validation strategies
    - Interpolation and gap-filling
    - Range checking and outlier detection
    - Defensive data engineering
    - Quality metadata and confidence tracking

DEBUGGING NOTES:
    - To test cleaning: Feed in corrupted data and check repairs
    - To verify interpolation: Remove fields and check filled values
    - To check range validation: Send extreme values (999999)
    - Common issue: Over-aggressive cleaning masks real anomalies
    - Balance: Clean enough to be usable, but preserve truth

FUTURE EXTENSIONS:
    1. Implement Kalman filtering for smoothing noisy data
    2. Add physics-based prediction models for validation
    3. Implement multi-field cross-validation (battery current vs voltage)
    4. Add adaptive thresholds based on mission phase
    5. Support multiple interpolation strategies (spline, polynomial)
    6. Add machine learning anomaly detection
    7. Implement confidence scoring for repaired values
"""

import copy
from typing import Dict, Any, Optional, List
from collections import deque


class Cleaner:
    """
    Validates and repairs corrupted telemetry.

    Implements range checking, interpolation, and sanity validation
    to produce clean, usable data from degraded packets.
    """

    # Define valid ranges for telemetry fields
    # Format: field_name: (min_value, max_value)
    VALID_RANGES = {
        # Power system ranges
        'battery_voltage': (20.0, 35.0),     # Lithium-ion cell limits
        'battery_current': (-10.0, 10.0),    # Charge/discharge range
        'battery_soc': (0.0, 100.0),         # State of charge percentage
        'battery_temp': (-40.0, 60.0),       # Safe operating temperature
        'solar_voltage': (0.0, 50.0),        # Panel output range
        'solar_current': (0.0, 5.0),         # Panel current limit

        # IMU ranges
        'roll': (-180.0, 180.0),             # Rotation about x-axis
        'pitch': (-180.0, 180.0),            # Rotation about y-axis
        'heading': (0.0, 360.0),             # Compass bearing

        # Thermal ranges
        'motor_temp': (-100.0, 80.0),        # Motor operating range
        'electronics_temp': (-100.0, 70.0),  # Electronics range
        'power_board_temp': (-100.0, 70.0),  # Power board range

        # Position (example bounds - depends on mission area)
        'x': (-10000.0, 10000.0),            # Position in meters
        'y': (-10000.0, 10000.0),
        'z': (-1000.0, 1000.0),              # Elevation range
        'velocity': (0.0, 2.0),              # Max rover speed m/s
    }

    # Maximum allowed rate of change per second
    # Format: field_name: max_change_per_second
    RATE_LIMITS = {
        'battery_soc': 5.0,          # Can't change more than 5%/sec
        'battery_voltage': 2.0,      # Voltage changes slowly
        'battery_temp': 1.0,         # Thermal inertia limits rate
        'x': 2.0,                    # Max velocity constraint
        'y': 2.0,
        'velocity': 0.5,             # Acceleration limit
    }

    def __init__(self, history_size: int = 10):
        """
        Initialize cleaner with validation rules.

        Args:
            history_size: Number of past frames to keep for interpolation
                - Larger = better interpolation, more memory
                - Smaller = less memory, poorer gap filling
                - Default: 10 frames

        Teaching Note:
            History is essential for:
                1. Linear interpolation across gaps
                2. Rate-of-change validation
                3. Detecting gradual drifts vs sudden jumps
                4. Providing context for anomaly detection
        """
        self.history_size = history_size
        self.frame_history = deque(maxlen=history_size)

        # Statistics tracking
        self.stats = {
            'frames_processed': 0,
            'frames_with_repairs': 0,
            'fields_repaired': 0,
            'checksum_failures': 0,
        }

    def clean_packet(self, packet: Optional[dict]) -> Optional[dict]:
        """
        Validate and repair a telemetry packet.

        This is the main entry point for the cleaning pipeline. It takes
        a potentially corrupted packet and produces a clean telemetry frame.

        Args:
            packet: Potentially corrupted packet (or None if lost)
                Expected structure: {header, payload, footer}

        Returns:
            Cleaned telemetry frame with repairs and quality metadata
            Returns None if packet is completely unrecoverable

        Teaching Note:
            The cleaner must handle several cases:
                1. Packet lost (None) → Try interpolation from history
                2. Checksum failed → Attempt field-by-field validation
                3. Fields missing → Interpolate from neighbors
                4. Fields corrupted → Clamp to range or interpolate
                5. Packet clean → Pass through with quality=high

        Example:
            >>> cleaner = Cleaner(history_size=10)
            >>> packet = corruptor.corrupt_packet(original_packet)
            >>> clean_frame = cleaner.clean_packet(packet)
            >>> if clean_frame['metadata']['quality'] == 'high':
            ...     print("Data is trustworthy")
        """
        self.stats['frames_processed'] += 1

        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Handle completely lost packets
        # ═══════════════════════════════════════════════════════════════
        if packet is None:
            # Packet was lost during transmission
            # Try to interpolate from history if we have enough data
            if len(self.frame_history) >= 2:
                interpolated = self._interpolate_lost_frame()
                interpolated['metadata']['quality'] = 'interpolated'
                interpolated['metadata']['source'] = 'history_interpolation'
                return interpolated
            else:
                # Not enough history - can't recover
                return None

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Validate checksum
        # ═══════════════════════════════════════════════════════════════
        # Check if packet was corrupted during transmission
        # Note: We don't have access to Packetizer here, so we check
        # the corruption_detected flag that Corruptor added

        checksum_valid = not packet['footer'].get('corruption_detected', False)
        if not checksum_valid:
            self.stats['checksum_failures'] += 1

        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Extract telemetry from packet payload
        # ═══════════════════════════════════════════════════════════════
        telemetry = packet['payload']['telemetry'].copy()
        timestamp = packet['header']['timestamp']

        # Create clean frame structure
        clean_frame = {
            'timestamp': timestamp,
            'frame_id': packet['header']['frame_id'],
            'data': {},  # Will hold cleaned telemetry
            'metadata': {
                'quality': 'high' if checksum_valid else 'degraded',
                'repairs': [],  # List of fields that were repaired
                'warnings': [],  # List of validation warnings
                'checksum_valid': checksum_valid,
            }
        }

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Clean each telemetry field
        # ═══════════════════════════════════════════════════════════════
        repair_count = 0

        for field_name, value in telemetry.items():
            cleaned_value, was_repaired, repair_method = self._clean_field(
                field_name, value, timestamp
            )

            clean_frame['data'][field_name] = cleaned_value

            if was_repaired:
                repair_count += 1
                self.stats['fields_repaired'] += 1
                clean_frame['metadata']['repairs'].append({
                    'field': field_name,
                    'method': repair_method,
                    'original': value,
                    'repaired': cleaned_value,
                })

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Update quality assessment
        # ═══════════════════════════════════════════════════════════════
        if repair_count > 0:
            self.stats['frames_with_repairs'] += 1
            if repair_count > 3:
                clean_frame['metadata']['quality'] = 'low'
            elif repair_count > 0:
                clean_frame['metadata']['quality'] = 'medium'

        # ═══════════════════════════════════════════════════════════════
        # STEP 6: Add to history for future interpolation
        # ═══════════════════════════════════════════════════════════════
        self.frame_history.append(clean_frame)

        return clean_frame

    def _clean_field(
        self, field_name: str, value: Any, timestamp: float
    ) -> tuple[Any, bool, str]:
        """
        Clean a single telemetry field.

        Args:
            field_name: Name of the field (e.g., 'battery_soc')
            value: Current value (may be corrupted, None, or wrong type)
            timestamp: Frame timestamp (for rate-of-change checks)

        Returns:
            Tuple of (cleaned_value, was_repaired, repair_method)

        Teaching Note:
            Field cleaning is a multi-stage process:
                1. Check if value exists (handle None)
                2. Check data type (numeric vs string)
                3. Check range bounds (physical limits)
                4. Check rate of change (impossible jumps)
                5. Attempt repair if validation fails
        """
        # Default: no repair needed
        was_repaired = False
        repair_method = "none"

        # ───────────────────────────────────────────────────────────
        # Case 1: Value is None or missing
        # ───────────────────────────────────────────────────────────
        if value is None:
            # Try to interpolate from history
            interpolated = self._interpolate_field(field_name, timestamp)
            if interpolated is not None:
                return interpolated, True, "interpolation_none"
            else:
                # No history available - use safe default
                default = self._get_default_value(field_name)
                return default, True, "default_value"

        # ───────────────────────────────────────────────────────────
        # Case 2: Value is wrong type (string corruption)
        # ───────────────────────────────────────────────────────────
        if not isinstance(value, (int, float)):
            # String like "CORRUPTED" - try interpolation
            interpolated = self._interpolate_field(field_name, timestamp)
            if interpolated is not None:
                return interpolated, True, "interpolation_type_error"
            else:
                default = self._get_default_value(field_name)
                return default, True, "default_type_error"

        # ───────────────────────────────────────────────────────────
        # Case 3: Value is extreme (infinity, NaN)
        # ───────────────────────────────────────────────────────────
        if not (-1e6 < value < 1e6):  # Arbitrary large bound
            interpolated = self._interpolate_field(field_name, timestamp)
            if interpolated is not None:
                return interpolated, True, "interpolation_extreme"
            else:
                default = self._get_default_value(field_name)
                return default, True, "default_extreme"

        # ───────────────────────────────────────────────────────────
        # Case 4: Value violates range constraints
        # ───────────────────────────────────────────────────────────
        if field_name in self.VALID_RANGES:
            min_val, max_val = self.VALID_RANGES[field_name]
            if not (min_val <= value <= max_val):
                # Out of range - clamp to bounds
                clamped = max(min_val, min(max_val, value))
                return clamped, True, "range_clamp"

        # ───────────────────────────────────────────────────────────
        # Case 5: Value has impossible rate of change
        # ───────────────────────────────────────────────────────────
        if field_name in self.RATE_LIMITS and len(self.frame_history) > 0:
            # Get last known good value for this field
            last_frame = self.frame_history[-1]
            if field_name in last_frame['data']:
                last_value = last_frame['data'][field_name]
                last_time = last_frame['timestamp']
                dt = timestamp - last_time

                if dt > 0:
                    rate = abs(value - last_value) / dt
                    max_rate = self.RATE_LIMITS[field_name]

                    if rate > max_rate:
                        # Rate too high - likely corrupted
                        # Use interpolation or last value
                        interpolated = self._interpolate_field(field_name, timestamp)
                        if interpolated is not None:
                            return interpolated, True, "interpolation_rate_limit"
                        else:
                            return last_value, True, "last_value_rate_limit"

        # ───────────────────────────────────────────────────────────
        # Value is clean - pass through unchanged
        # ───────────────────────────────────────────────────────────
        return value, False, "none"

    def _interpolate_field(self, field_name: str, timestamp: float) -> Optional[float]:
        """
        Interpolate missing field value from history.

        Uses linear interpolation between surrounding good values.

        Args:
            field_name: Field to interpolate
            timestamp: Time point for interpolation

        Returns:
            Interpolated value, or None if insufficient history

        Teaching Note:
            Linear interpolation assumes values change smoothly.
            Good for: battery SoC, temperature, position
            Bad for: discrete states, boolean flags, event counters
        """
        if len(self.frame_history) < 2:
            return None  # Need at least 2 points for interpolation

        # Find two surrounding points with valid data for this field
        # For simplicity, use first and last available values
        # (A full implementation would find closest neighbors)

        values_with_time = []
        for frame in self.frame_history:
            if field_name in frame['data']:
                val = frame['data'][field_name]
                if isinstance(val, (int, float)):
                    values_with_time.append((frame['timestamp'], val))

        if len(values_with_time) < 2:
            return None

        # Use last two points for linear interpolation
        t1, v1 = values_with_time[-2]
        t2, v2 = values_with_time[-1]

        # Linear interpolation: v = v1 + (v2-v1) * (t-t1)/(t2-t1)
        if t2 != t1:
            slope = (v2 - v1) / (t2 - t1)
            interpolated = v1 + slope * (timestamp - t1)
            return interpolated
        else:
            # Same timestamp - use last value
            return v2

    def _interpolate_lost_frame(self) -> dict:
        """
        Interpolate entire frame when packet is lost.

        Returns:
            Interpolated frame based on recent history

        Teaching Note:
            When a packet is completely lost, we estimate all fields
            from surrounding data. This provides continuity but introduces
            uncertainty. Mark as low-quality data.
        """
        if len(self.frame_history) < 2:
            return None

        # Get last two frames
        frame1 = self.frame_history[-2]
        frame2 = self.frame_history[-1]

        # Estimate timestamp (assume regular spacing)
        t1 = frame1['timestamp']
        t2 = frame2['timestamp']
        dt = t2 - t1
        estimated_timestamp = t2 + dt

        # Interpolate all fields
        interpolated_frame = {
            'timestamp': estimated_timestamp,
            'frame_id': -1,  # Unknown frame ID
            'data': {},
            'metadata': {
                'quality': 'interpolated',
                'repairs': [],
                'warnings': ['Entire frame interpolated due to packet loss'],
                'checksum_valid': False,
            }
        }

        # For each field in last frame, interpolate forward
        for field_name in frame2['data'].keys():
            if field_name in frame1['data'] and field_name in frame2['data']:
                v1 = frame1['data'][field_name]
                v2 = frame2['data'][field_name]

                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    # Linear extrapolation
                    interpolated_frame['data'][field_name] = v2 + (v2 - v1)
                else:
                    # Non-numeric - use last value
                    interpolated_frame['data'][field_name] = v2
            else:
                # Field not in history - use last available
                interpolated_frame['data'][field_name] = frame2['data'].get(field_name)

        return interpolated_frame

    def _get_default_value(self, field_name: str) -> float:
        """
        Get safe default value for a field.

        Args:
            field_name: Name of field

        Returns:
            Conservative default value

        Teaching Note:
            Defaults should be "safe" values that won't trigger
            false alarms or unsafe behavior. For example:
                - Battery SoC → 50% (mid-range, not critical)
                - Temperature → 0°C (neutral)
                - Position → 0.0 (origin)
        """
        # Use midpoint of valid range if available
        if field_name in self.VALID_RANGES:
            min_val, max_val = self.VALID_RANGES[field_name]
            return (min_val + max_val) / 2.0

        # Generic default for unknown fields
        return 0.0

    def get_statistics(self) -> dict:
        """
        Get cleaning statistics.

        Returns:
            Dictionary with cleaning metrics

        Teaching Note:
            High repair rates indicate:
                - Poor communication link
                - Sensor failures
                - Environmental interference
            Monitor these metrics to assess data quality.
        """
        repair_rate = 0.0
        if self.stats['frames_processed'] > 0:
            repair_rate = (
                self.stats['frames_with_repairs'] / self.stats['frames_processed']
            )

        return {
            'frames_processed': self.stats['frames_processed'],
            'frames_with_repairs': self.stats['frames_with_repairs'],
            'fields_repaired': self.stats['fields_repaired'],
            'checksum_failures': self.stats['checksum_failures'],
            'repair_rate': repair_rate,
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'frames_processed': 0,
            'frames_with_repairs': 0,
            'fields_repaired': 0,
            'checksum_failures': 0,
        }

    def clear_history(self):
        """
        Clear frame history.

        Useful when starting a new mission or after long gaps.
        """
        self.frame_history.clear()


# ═══════════════════════════════════════════════════════════════
# DEBUGGING AND TESTING HELPERS
# ═══════════════════════════════════════════════════════════════

def test_cleaner():
    """
    Test function to demonstrate cleaner behavior.

    Shows:
        1. Range validation and clamping
        2. Interpolation for missing values
        3. Type error handling
        4. Statistics tracking
    """
    print("Testing Cleaner...")
    print()

    cleaner = Cleaner(history_size=5)

    # Test Case 1: Clean packet (no repairs needed)
    print("Test 1: Clean packet")
    clean_packet = {
        'header': {'timestamp': 100.0, 'frame_id': 1},
        'payload': {'telemetry': {
            'battery_soc': 75.0,
            'battery_voltage': 28.0,
            'roll': 5.0,
        }},
        'footer': {'corruption_detected': False}
    }
    result = cleaner.clean_packet(clean_packet)
    print(f"  Quality: {result['metadata']['quality']}")
    print(f"  Repairs: {len(result['metadata']['repairs'])}")
    print()

    # Test Case 2: Out-of-range value
    print("Test 2: Out-of-range battery SoC (150%)")
    corrupt_packet = {
        'header': {'timestamp': 101.0, 'frame_id': 2},
        'payload': {'telemetry': {
            'battery_soc': 150.0,  # Invalid: > 100%
            'battery_voltage': 28.0,
            'roll': 5.0,
        }},
        'footer': {'corruption_detected': True}
    }
    result = cleaner.clean_packet(corrupt_packet)
    print(f"  Quality: {result['metadata']['quality']}")
    print(f"  Repaired battery_soc: {result['data']['battery_soc']}")
    print(f"  Repair method: {result['metadata']['repairs'][0]['method']}")
    print()

    # Test Case 3: Missing field (None)
    print("Test 3: Missing battery_voltage field")
    missing_packet = {
        'header': {'timestamp': 102.0, 'frame_id': 3},
        'payload': {'telemetry': {
            'battery_soc': 74.0,
            'battery_voltage': None,  # Missing!
            'roll': 5.0,
        }},
        'footer': {'corruption_detected': True}
    }
    result = cleaner.clean_packet(missing_packet)
    print(f"  Quality: {result['metadata']['quality']}")
    print(f"  Interpolated battery_voltage: {result['data']['battery_voltage']}")
    print()

    # Test Case 4: Lost packet (None)
    print("Test 4: Completely lost packet")
    result = cleaner.clean_packet(None)
    if result:
        print(f"  Quality: {result['metadata']['quality']}")
        print(f"  Source: {result['metadata']['source']}")
        print(f"  Interpolated timestamp: {result['timestamp']}")
    else:
        print("  Could not recover (insufficient history)")
    print()

    # Show statistics
    stats = cleaner.get_statistics()
    print("Cleaner Statistics:")
    for key, value in stats.items():
        if 'rate' in key:
            print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")
    print()

    print("Cleaner test complete!")


if __name__ == "__main__":
    test_cleaner()
