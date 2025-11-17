"""
Corruptor - Transmission Degradation Simulation

PURPOSE:
    Simulates realistic transmission errors including packet loss, bit flips,
    field corruption, timing jitter, and communication dropouts. This creates
    the messy, real-world data that our cleaning pipeline must handle.

THEORY:
    Communication channels are never perfect. Real spacecraft experience:
        - Packet Loss: Entire packets fail to arrive
            * Caused by: Weak signal, interference, buffer overflows
            * Rate: 0.1% - 10% depending on link quality

        - Timing Jitter: Packets arrive at irregular intervals
            * Caused by: Variable propagation delays, queuing
            * Effect: Out-of-order arrival, variable latency

        - Field Corruption: Individual values become invalid
            * Caused by: Bit flips from cosmic rays, noise
            * Rate: Rare but catastrophic (one bad value ruins calculations)

        - Sequence Gaps: Missing packet IDs in sequence
            * Caused by: Dropped packets, transmission windows
            * Effect: Discontinuous data, interpolation required

    These errors are probabilistic - we model them with random distributions
    to simulate realistic degradation patterns.

MERIDIAN-3 STORY SNIPPET:
    "The dust storm lasted three sols. For 72 hours, we lost contact. When the
    sky cleared and the rover called home, packets arrived corrupted. Battery
    voltage readings showing impossible 500V spikes. Temperature values missing
    entirely. Sequence numbers jumping from 4523 to 4891 - 368 packets lost to
    the Martian wind. Our pipeline must handle this chaos."

ARCHITECTURE ROLE:
    The Corruptor sits between the Packetizer and Cleaner. It's the "adversary"
    that makes our data pipeline earn its keep. Without corruption, we wouldn't
    need cleaning, validation, or anomaly detection.

    Packetizer → Corruptor → Cleaner → Anomaly Detector

CORRUPTION FLOW DIAGRAM:

    ╔══════════════════════════════════════════════════════════════╗
    ║                    CORRUPTION PIPELINE                       ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  Clean Packet                                                ║
    ║      │                                                       ║
    ║      ▼                                                       ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 1: Packet Loss Check           │                   ║
    ║  │  Random drop? → None (packet lost)   │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │ [if packet survives]                      ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 2: Add Timing Jitter           │                   ║
    ║  │  Randomize transmission delay        │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 3: Field Corruption            │                   ║
    ║  │  - Random field removal (None)       │                   ║
    ║  │  - Value distortion (bit flips)      │                   ║
    ║  │  - Type corruption (str→float)       │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 4: Checksum Invalidation       │                   ║
    ║  │  Mark corrupted packets              │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  Degraded Packet                                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

TEACHING GOALS:
    - Understanding communication channel imperfections
    - Statistical error modeling
    - Failure mode simulation
    - Defensive programming preparation
    - Probabilistic system behavior

DEBUGGING NOTES:
    - Set all corruption rates to 0.0 to test pipeline with clean data
    - Set packet_loss_rate to 1.0 to test handling of complete data loss
    - Use fixed random seed for reproducible corruption patterns
    - Track corruption statistics to verify rates match expectations
    - Common issue: Corruption breaking downstream assumptions about data types

FUTURE EXTENSIONS:
    1. Add burst errors (correlated failures) during "dust storms"
    2. Implement signal-to-noise ratio model affecting corruption rates
    3. Add checksum errors (separate from payload corruption)
    4. Model distance-dependent error rates (farther = more errors)
    5. Implement retry logic simulation
    6. Add out-of-order packet delivery
    7. Model bandwidth throttling and queuing delays
"""

import random
import copy
from typing import Dict, Any, Optional


class Corruptor:
    """
    Applies transmission degradation to packets.

    Models realistic communication errors to test data pipeline robustness.
    """

    def __init__(
        self,
        packet_loss_rate: float = 0.01,
        field_corruption_rate: float = 0.05,
        jitter_stddev: float = 0.1,
        random_seed: Optional[int] = None
    ):
        """
        Initialize corruptor with error probability settings.

        Args:
            packet_loss_rate: Probability of complete packet loss (0.0-1.0)
                - 0.01 = 1% packet loss (good link)
                - 0.10 = 10% packet loss (poor link)
                - Default: 0.01 (1%)

            field_corruption_rate: Probability of individual field corruption (0.0-1.0)
                - 0.05 = 5% of fields corrupted (typical)
                - 0.20 = 20% corruption (severe degradation)
                - Default: 0.05 (5%)

            jitter_stddev: Standard deviation of timing jitter in seconds
                - 0.1 = ±0.1s typical variation
                - 1.0 = ±1s severe jitter
                - Default: 0.1 (100ms)

            random_seed: Seed for reproducible corruption (for testing)

        Teaching Note:
            Error rates are configurable to simulate different link conditions:
                - Deep space (Mars): ~1% loss, 5% corruption
                - Dust storm: ~20% loss, 30% corruption
                - Perfect (testing): 0% loss, 0% corruption
        """
        self.packet_loss_rate = packet_loss_rate
        self.field_corruption_rate = field_corruption_rate
        self.jitter_stddev = jitter_stddev

        # Set random seed for reproducibility (useful for testing)
        if random_seed is not None:
            random.seed(random_seed)

        # Statistics tracking
        self.stats = {
            'packets_received': 0,
            'packets_lost': 0,
            'packets_corrupted': 0,
            'fields_corrupted': 0,
        }

    def corrupt_packet(self, packet: dict) -> Optional[dict]:
        """
        Apply transmission errors to a packet.

        This method simulates the journey of a packet through an imperfect
        communication channel. The packet may be lost entirely, arrive with
        timing jitter, or have fields corrupted.

        Args:
            packet: Clean packet from packetizer
                Expected structure: {header, payload, footer}

        Returns:
            Corrupted packet with errors applied, or None if packet is lost

        Teaching Note:
            Packet loss (returning None) is handled differently than corruption.
            Receivers must handle both missing packets and bad data packets.

        Example:
            >>> corruptor = Corruptor(packet_loss_rate=0.1, field_corruption_rate=0.2)
            >>> packet = packetizer.encode_frame(frame)
            >>> degraded = corruptor.corrupt_packet(packet)
            >>> if degraded is None:
            ...     print("Packet lost!")
            >>> elif 'battery_soc' not in degraded['payload']['telemetry']:
            ...     print("Battery field corrupted!")
        """
        self.stats['packets_received'] += 1

        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Packet Loss Simulation
        # ═══════════════════════════════════════════════════════════════
        # Some packets never arrive. This could be due to:
        #   - Signal fading below detection threshold
        #   - Collision with other transmissions
        #   - Buffer overflow at receiver
        #   - Interruption of communication window

        if random.random() < self.packet_loss_rate:
            self.stats['packets_lost'] += 1
            return None  # Packet completely lost

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Deep Copy Packet (Don't Modify Original)
        # ═══════════════════════════════════════════════════════════════
        # We make a deep copy so corruption doesn't affect the original
        # packet object (simulating one-way transmission).

        corrupted_packet = copy.deepcopy(packet)

        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Apply Timing Jitter
        # ═══════════════════════════════════════════════════════════════
        # Packets don't arrive at perfectly regular intervals. Propagation
        # delays vary due to queuing, retransmissions, and path changes.

        jitter = random.gauss(0, self.jitter_stddev)
        corrupted_packet['footer']['transmission_time'] += jitter

        # Teaching Note:
        # Jitter affects timestamp-based analysis. If you're measuring
        # rates of change (derivatives), jitter creates artificial spikes.

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Field Corruption
        # ═══════════════════════════════════════════════════════════════
        # Individual telemetry fields may be corrupted due to bit flips,
        # quantization errors, or sensor glitches.

        telemetry = corrupted_packet['payload']['telemetry']
        corruption_occurred = False

        # Iterate through all telemetry fields and corrupt some randomly
        corrupted_fields = []
        for field_name in list(telemetry.keys()):
            if random.random() < self.field_corruption_rate:
                # This field will be corrupted
                corruption_occurred = True
                corrupted_fields.append(field_name)
                self.stats['fields_corrupted'] += 1

                # Choose corruption type randomly
                corruption_type = random.choice([
                    'remove',      # Field missing entirely
                    'distort',     # Value altered
                    'type_error',  # Wrong data type
                ])

                if corruption_type == 'remove':
                    # Field is missing (None or deleted)
                    # This simulates incomplete packet reconstruction
                    telemetry[field_name] = None

                elif corruption_type == 'distort':
                    # Value is distorted (bit flip, noise)
                    # This simulates transmission errors in the value itself
                    original_value = telemetry[field_name]
                    telemetry[field_name] = self._distort_value(original_value)

                elif corruption_type == 'type_error':
                    # Type is wrong (string instead of number)
                    # This simulates parsing errors or protocol violations
                    telemetry[field_name] = "CORRUPTED"

        # Record if any corruption occurred
        if corruption_occurred:
            self.stats['packets_corrupted'] += 1

            # Add corruption metadata to footer
            corrupted_packet['footer']['corruption_detected'] = True
            corrupted_packet['footer']['corrupted_fields'] = corrupted_fields
        else:
            corrupted_packet['footer']['corruption_detected'] = False
            corrupted_packet['footer']['corrupted_fields'] = []

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Invalidate Checksum (If Corrupted)
        # ═══════════════════════════════════════════════════════════════
        # If we corrupted the payload, the checksum should no longer match.
        # We don't recalculate - we leave it mismatched to simulate
        # detection of corruption by the receiver.

        # The checksum remains the original (now invalid) value
        # Receivers will detect this mismatch and know packet is bad

        return corrupted_packet

    def _distort_value(self, value: Any) -> Any:
        """
        Distort a value to simulate bit flips or noise.

        Args:
            value: Original value (any type)

        Returns:
            Distorted value (same type, different value)

        Teaching Note:
            Different data types require different distortion strategies:
                - Floats: Add noise or multiply by factor
                - Ints: Add offset or flip bits
                - Strings: Usually just marked as corrupted
                - Dicts/Lists: Typically don't distort, just remove
        """
        if isinstance(value, (int, float)):
            # Numeric distortion: Add significant noise or multiply by factor
            distortion_type = random.choice(['noise', 'scale', 'extreme'])

            if distortion_type == 'noise':
                # Add Gaussian noise (could make value unrealistic)
                noise = random.gauss(0, abs(value) * 0.5 + 1.0)
                return value + noise

            elif distortion_type == 'scale':
                # Multiply by random factor (simulates bit flip in exponent)
                scale = random.choice([0.01, 0.1, 10, 100, 1000])
                return value * scale

            elif distortion_type == 'extreme':
                # Replace with extreme value (overflow, underflow)
                return random.choice([999999, -999999, float('inf'), float('-inf')])

        elif isinstance(value, str):
            # String corruption: Replace with error marker
            return "CORRUPTED"

        elif isinstance(value, (dict, list)):
            # Complex types: Usually just return None (removed)
            return None

        else:
            # Unknown type: Return None
            return None

    def get_statistics(self) -> dict:
        """
        Get corruption statistics.

        Returns:
            Dictionary with packet and field corruption counts/rates

        Teaching Note:
            Statistics help verify that simulation parameters are correct.
            Actual rates should approximately match configured rates
            (within statistical variation).
        """
        total = self.stats['packets_received']
        loss_rate = self.stats['packets_lost'] / total if total > 0 else 0
        corruption_rate = self.stats['packets_corrupted'] / total if total > 0 else 0

        return {
            'packets_received': self.stats['packets_received'],
            'packets_lost': self.stats['packets_lost'],
            'packets_corrupted': self.stats['packets_corrupted'],
            'fields_corrupted': self.stats['fields_corrupted'],
            'effective_loss_rate': loss_rate,
            'effective_corruption_rate': corruption_rate,
        }

    def reset_statistics(self):
        """
        Reset statistics counters.

        Useful for measuring specific scenarios or missions.
        """
        self.stats = {
            'packets_received': 0,
            'packets_lost': 0,
            'packets_corrupted': 0,
            'fields_corrupted': 0,
        }


# ═══════════════════════════════════════════════════════════════
# DEBUGGING AND TESTING HELPERS
# ═══════════════════════════════════════════════════════════════

def test_corruptor():
    """
    Test function to demonstrate corruptor behavior.

    Shows:
        1. Packet loss simulation
        2. Field corruption types
        3. Statistics tracking
        4. Checksum invalidation
    """
    print("Testing Corruptor...")
    print()

    # Create corruptor with moderate corruption
    # (Higher rates than typical for testing visibility)
    corruptor = Corruptor(
        packet_loss_rate=0.2,      # 20% loss
        field_corruption_rate=0.3,  # 30% field corruption
        jitter_stddev=0.5,          # 500ms jitter
        random_seed=42              # Reproducible results
    )

    # Create sample packet (simulating packetizer output)
    sample_packet = {
        'header': {
            'packet_id': 100,
            'timestamp': 500.0,
            'frame_id': 100,
            'encoding': 'raw',
            'priority': 5,
            'packet_size': 1024,
        },
        'payload': {
            'telemetry': {
                'battery_soc': 75.5,
                'battery_voltage': 28.2,
                'battery_temp': 15.3,
                'roll': 1.2,
                'pitch': -0.5,
                'heading': 45.0,
                'x': 100.0,
                'y': 200.0,
            }
        },
        'footer': {
            'checksum': 'abc123def456',
            'transmission_time': 1000.0,
        }
    }

    # Test corruption on multiple packets
    print("Sending 10 packets through corruptor...")
    print()

    for i in range(10):
        # Create unique packet
        test_packet = copy.deepcopy(sample_packet)
        test_packet['header']['packet_id'] = i

        # Corrupt it
        result = corruptor.corrupt_packet(test_packet)

        if result is None:
            print(f"Packet {i}: LOST")
        else:
            corrupted = result['footer'].get('corruption_detected', False)
            if corrupted:
                fields = result['footer']['corrupted_fields']
                print(f"Packet {i}: CORRUPTED (fields: {', '.join(fields)})")
            else:
                print(f"Packet {i}: Clean")

    print()

    # Show statistics
    stats = corruptor.get_statistics()
    print("Corruption Statistics:")
    for key, value in stats.items():
        if 'rate' in key:
            print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")
    print()

    print("Corruptor test complete!")


if __name__ == "__main__":
    # Run test when script is executed directly
    test_corruptor()
