"""
Packetizer - Telemetry Frame Encoding and Transmission Simulation

PURPOSE:
    Converts raw telemetry frames into transmission packets with encoding,
    timestamps, checksums, and metadata. Simulates the real process of
    packaging data for transmission over a bandwidth-limited radio link.

THEORY:
    Real spacecraft communicate over constrained radio links with:
        - Limited bandwidth (often just a few kilobits/second)
        - High latency (minutes to hours for deep space)
        - Intermittent connectivity (orbital passes, terrain occlusion)
        - Power constraints (every bit transmitted costs energy)

    To maximize efficiency and reliability, telemetry is:
        1. Structured into fixed-format packets
        2. Compressed or downsampled when possible
        3. Tagged with timestamps and sequence numbers
        4. Protected with checksums for error detection
        5. Prioritized (critical data sent first)

MERIDIAN-3 STORY SNIPPET:
    "Every packet we transmit costs power, and power is life. The Deep Space
    Network only gives us a 4-hour window every sol. In that window, we must
    send the most important data: Did the rover survive? What did it discover?
    What went wrong? We package telemetry into 1024-byte packets, add checksums,
    sequence numbers, timestamps. Ground operators reassemble the story from
    these fragments."

ARCHITECTURE ROLE:
    The Packetizer is the first stage of the telemetry pipeline. It sits
    between the simulator (which produces perfect frames) and the communication
    channel (which introduces errors).

    Simulator → Packetizer → Corruptor → Cleaner → Anomaly Detector → Storage

PACKET STRUCTURE DIAGRAM:

    ╔══════════════════════════════════════════════════════════════╗
    ║                    TELEMETRY PACKET                          ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  HEADER (metadata)                                           ║
    ║  ┌────────────────────────────────────────────────────────┐  ║
    ║  │ packet_id: Unique sequence number                      │  ║
    ║  │ timestamp: Mission elapsed time (s)                    │  ║
    ║  │ frame_id: Original frame identifier                    │  ║
    ║  │ encoding: "raw" or "compressed"                        │  ║
    ║  │ priority: 0 (low) to 10 (critical)                     │  ║
    ║  │ packet_size: Size in bytes                             │  ║
    ║  └────────────────────────────────────────────────────────┘  ║
    ║                                                              ║
    ║  PAYLOAD (sensor data)                                       ║
    ║  ┌────────────────────────────────────────────────────────┐  ║
    ║  │ telemetry: All sensor readings (dict)                  │  ║
    ║  │   - IMU (roll, pitch, heading)                         │  ║
    ║  │   - Power (battery, solar)                             │  ║
    ║  │   - Thermal (temperatures)                             │  ║
    ║  │   - Position (x, y, z, velocity)                       │  ║
    ║  │   - Environmental info                                 │  ║
    ║  └────────────────────────────────────────────────────────┘  ║
    ║                                                              ║
    ║  FOOTER (validation)                                         ║
    ║  ┌────────────────────────────────────────────────────────┐  ║
    ║  │ checksum: Simple hash for error detection              │  ║
    ║  │ transmission_time: When packet was "sent"              │  ║
    ║  └────────────────────────────────────────────────────────┘  ║
    ╚══════════════════════════════════════════════════════════════╝

TEACHING GOALS:
    - Data serialization and encoding
    - Packet structure design
    - Metadata and checksums
    - Transmission protocols
    - Understanding communication constraints

DEBUGGING NOTES:
    - To inspect packets: Use print_packet() helper method
    - To verify checksums: Compare against recalculated hash
    - To test priority logic: Create frames with different criticality
    - Common issue: Timestamp mismatch between frame and packet
    - Validation: packet_size should be consistent with payload

FUTURE EXTENSIONS:
    1. Add real compression algorithms (gzip, delta encoding)
    2. Implement adaptive downsampling (reduce resolution when bandwidth limited)
    3. Add packet fragmentation for large data (images)
    4. Implement priority queuing and bandwidth allocation
    5. Add encryption/authentication for secure telemetry
    6. Support multiple encoding formats (binary, JSON, protobuf)
    7. Implement packet batching for efficiency
"""

from typing import Dict, Any
import hashlib
import json
import time


class Packetizer:
    """
    Encodes telemetry frames into transmission packets.

    This class simulates the packetization process on a real spacecraft,
    where raw telemetry data is structured, tagged with metadata, and
    prepared for transmission over a constrained communication link.
    """

    def __init__(self, encoding: str = "raw"):
        """
        Initialize packetizer with encoding settings.

        Args:
            encoding: Encoding scheme to use
                - "raw": No compression, full precision (default)
                - "compressed": Future implementation - reduce data size

        Teaching Note:
            In real spacecraft, encoding choice is a tradeoff:
                - Raw: Full fidelity, but uses more bandwidth
                - Compressed: Saves bandwidth, but loses precision/adds latency
                - Adaptive: Switch based on data criticality and bandwidth availability
        """
        self.encoding = encoding
        self.packet_counter = 0  # Monotonic sequence number for all packets

        # Packet statistics (useful for debugging and monitoring)
        self.stats = {
            'total_packets': 0,
            'total_bytes': 0,
            'encoding_time_ms': 0.0,
        }

    def encode_frame(self, frame: dict) -> dict:
        """
        Encode a telemetry frame into a transmission packet.

        This method takes a raw telemetry frame (from the simulator) and
        wraps it with transmission metadata, calculates checksums, and
        assigns priority.

        Args:
            frame: Raw telemetry frame dictionary from simulator
                Expected keys: timestamp, frame_id, sensor readings, etc.

        Returns:
            Encoded packet with header, payload, and footer

        Teaching Note:
            The packet structure mirrors real spacecraft telemetry protocols
            like CCSDS (Consultative Committee for Space Data Systems).
            We simplify but maintain the key concepts: headers, payload,
            checksums, and sequence numbers.

        Example:
            >>> packetizer = Packetizer()
            >>> frame = {'timestamp': 100.5, 'frame_id': 42, 'battery_soc': 85.3, ...}
            >>> packet = packetizer.encode_frame(frame)
            >>> print(packet['header']['packet_id'])  # Sequential number
            0
        """
        start_time = time.time()

        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Determine packet priority based on frame contents
        # ═══════════════════════════════════════════════════════════════
        # Priority helps ground operators sort packets when bandwidth
        # is limited. Critical events (low battery, faults) go first.

        priority = self._calculate_priority(frame)

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Build packet header with metadata
        # ═══════════════════════════════════════════════════════════════
        # Headers allow receivers to:
        #   - Detect missing packets (via sequence numbers)
        #   - Reconstruct timeline (via timestamps)
        #   - Route data appropriately (via encoding/priority)

        header = {
            'packet_id': self.packet_counter,  # Monotonic sequence number
            'timestamp': frame.get('timestamp', 0.0),  # Mission elapsed time
            'frame_id': frame.get('frame_id', -1),  # Original frame ID
            'encoding': self.encoding,  # How payload is encoded
            'priority': priority,  # 0=low, 10=critical
        }

        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Encode payload
        # ═══════════════════════════════════════════════════════════════
        # For now, we just pass through the frame data. Future implementations
        # could add compression, downsampling, or selective field inclusion.

        payload = self._encode_payload(frame)

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Calculate packet size
        # ═══════════════════════════════════════════════════════════════
        # In real systems, size affects transmission time and power cost.
        # We estimate size via JSON serialization (not exact, but representative).

        packet_size = self._estimate_size(header, payload)
        header['packet_size'] = packet_size

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Calculate checksum for error detection
        # ═══════════════════════════════════════════════════════════════
        # Checksums help receivers detect if packet was corrupted during
        # transmission. Real systems use CRC or stronger algorithms.

        checksum = self._calculate_checksum(header, payload)

        # ═══════════════════════════════════════════════════════════════
        # STEP 6: Build footer with validation data
        # ═══════════════════════════════════════════════════════════════

        footer = {
            'checksum': checksum,
            'transmission_time': time.time(),  # Simulated "send time"
        }

        # ═══════════════════════════════════════════════════════════════
        # STEP 7: Assemble complete packet
        # ═══════════════════════════════════════════════════════════════

        packet = {
            'header': header,
            'payload': payload,
            'footer': footer,
        }

        # ═══════════════════════════════════════════════════════════════
        # STEP 8: Update statistics and counters
        # ═══════════════════════════════════════════════════════════════

        self.packet_counter += 1
        self.stats['total_packets'] += 1
        self.stats['total_bytes'] += packet_size

        encoding_time_ms = (time.time() - start_time) * 1000
        self.stats['encoding_time_ms'] += encoding_time_ms

        return packet

    def _calculate_priority(self, frame: dict) -> int:
        """
        Determine packet priority based on telemetry content.

        Priority helps manage limited bandwidth by sending critical
        data first. This is essential for fault detection and response.

        Args:
            frame: Telemetry frame to analyze

        Returns:
            Priority value: 0 (low) to 10 (critical)

        Teaching Note:
            Priority assignment is a mix of rules and heuristics:
                - Safety-critical conditions (low battery) = high priority
                - Science discoveries (unusual readings) = medium priority
                - Routine housekeeping = low priority

            Real missions have detailed priority schemes defined by
            mission operations teams.
        """
        priority = 5  # Default: medium priority

        # Critical: Low battery (could affect rover survival)
        if frame.get('battery_soc', 100) < 20:
            priority = 10

        # High: Battery moderate but declining
        elif frame.get('battery_soc', 100) < 40:
            priority = 8

        # High: Thermal anomalies (equipment could be damaged)
        battery_temp = frame.get('battery_temp', 0)
        if battery_temp < -20 or battery_temp > 60:
            priority = 9

        # Medium-high: Science instruments active (potential discovery)
        if frame.get('env_info', {}).get('is_science_window', False):
            priority = max(priority, 6)

        # Medium: Rover is moving (navigation data important)
        if frame.get('velocity', 0) > 0.01:
            priority = max(priority, 5)

        # Low: Stationary with good health
        # (priority already at default or increased above)

        return priority

    def _encode_payload(self, frame: dict) -> dict:
        """
        Encode telemetry frame into packet payload.

        Args:
            frame: Raw telemetry frame

        Returns:
            Encoded payload dictionary

        Teaching Note:
            Current implementation just copies the frame (raw encoding).
            Future implementations could:
                - Apply delta encoding (send changes from last frame)
                - Downsample (reduce precision of less-critical fields)
                - Compress (apply gzip or custom algorithms)
                - Selectivity (include only changed or important fields)
        """
        if self.encoding == "raw":
            # Pass through all data unchanged
            return {
                'telemetry': frame.copy()
            }

        elif self.encoding == "compressed":
            # TODO: Implement compression
            # For now, fall back to raw
            return {
                'telemetry': frame.copy(),
                'compression_note': 'Compression not yet implemented'
            }

        else:
            raise ValueError(f"Unknown encoding: {self.encoding}")

    def _estimate_size(self, header: dict, payload: dict) -> int:
        """
        Estimate packet size in bytes.

        Args:
            header: Packet header dictionary
            payload: Packet payload dictionary

        Returns:
            Estimated size in bytes

        Teaching Note:
            Size estimation helps simulate bandwidth constraints.
            We use JSON serialization as a proxy for actual packet size.
            Real protocols (CCSDS, binary formats) are more compact but
            harder to debug. JSON is human-readable and good for teaching.
        """
        # Serialize to JSON and measure length
        # This is an approximation - real binary encoding would be smaller
        combined = {
            'header': header,
            'payload': payload,
        }
        json_string = json.dumps(combined)
        return len(json_string.encode('utf-8'))

    def _calculate_checksum(self, header: dict, payload: dict) -> str:
        """
        Calculate checksum for error detection.

        Args:
            header: Packet header
            payload: Packet payload

        Returns:
            Hex string checksum

        Teaching Note:
            Checksums detect transmission errors. Real spacecraft use:
                - CRC (Cyclic Redundancy Check): Fast, good error detection
                - SHA/MD5: Cryptographic hashes, slower but stronger
                - Reed-Solomon: Error correction codes (can fix errors)

            We use SHA256 for simplicity and good error detection.
            In production, CRC-16 or CRC-32 would be more appropriate.
        """
        # Combine header and payload into canonical string
        combined = {
            'header': header,
            'payload': payload,
        }

        # Serialize to JSON (sorted keys for consistency)
        canonical_string = json.dumps(combined, sort_keys=True)

        # Calculate SHA256 hash
        hash_object = hashlib.sha256(canonical_string.encode('utf-8'))
        checksum = hash_object.hexdigest()[:16]  # Use first 16 chars (64 bits)

        return checksum

    def verify_checksum(self, packet: dict) -> bool:
        """
        Verify packet checksum matches contents.

        Args:
            packet: Complete packet with header, payload, footer

        Returns:
            True if checksum is valid, False otherwise

        Teaching Note:
            Checksum verification is how receivers detect corrupted packets.
            If checksum doesn't match, the packet must be:
                - Requested again (if possible)
                - Reconstructed from redundancy
                - Marked as invalid and discarded

        Example:
            >>> packetizer = Packetizer()
            >>> packet = packetizer.encode_frame(frame)
            >>> assert packetizer.verify_checksum(packet)  # Should be valid
            >>> packet['payload']['telemetry']['battery_soc'] = 999  # Corrupt data
            >>> assert not packetizer.verify_checksum(packet)  # Now invalid
        """
        # Recalculate checksum from header and payload
        calculated = self._calculate_checksum(packet['header'], packet['payload'])

        # Compare with stored checksum
        stored = packet['footer']['checksum']

        return calculated == stored

    def print_packet(self, packet: dict, verbose: bool = False):
        """
        Print packet contents in human-readable format.

        Args:
            packet: Packet to display
            verbose: If True, show full payload; if False, show summary

        Teaching Note:
            Debugging helper for inspecting packet structure. Useful when
            tracing data flow through the pipeline or investigating issues.
        """
        print("╔═══════════════════════════════════════════════════════════")
        print("║ TELEMETRY PACKET")
        print("╠═══════════════════════════════════════════════════════════")
        print("║ HEADER:")
        for key, value in packet['header'].items():
            print(f"║   {key}: {value}")

        print("║")
        print("║ PAYLOAD:")
        if verbose:
            for key, value in packet['payload']['telemetry'].items():
                print(f"║   {key}: {value}")
        else:
            print(f"║   [telemetry with {len(packet['payload']['telemetry'])} fields]")

        print("║")
        print("║ FOOTER:")
        for key, value in packet['footer'].items():
            if key == 'transmission_time':
                print(f"║   {key}: {value:.6f}")
            else:
                print(f"║   {key}: {value}")

        print("╚═══════════════════════════════════════════════════════════")

    def get_statistics(self) -> dict:
        """
        Get packetizer statistics.

        Returns:
            Dictionary with packet count, data volume, timing

        Teaching Note:
            Statistics help monitor system performance and identify
            bottlenecks. In real operations, telemetry about telemetry
            (metadata) is crucial for health monitoring.
        """
        avg_encoding_time = 0.0
        if self.stats['total_packets'] > 0:
            avg_encoding_time = (
                self.stats['encoding_time_ms'] / self.stats['total_packets']
            )

        return {
            'total_packets': self.stats['total_packets'],
            'total_bytes': self.stats['total_bytes'],
            'avg_packet_size': (
                self.stats['total_bytes'] / self.stats['total_packets']
                if self.stats['total_packets'] > 0 else 0
            ),
            'avg_encoding_time_ms': avg_encoding_time,
        }

    def reset_statistics(self):
        """
        Reset statistics counters.

        Useful for benchmarking specific scenarios or missions.
        """
        self.stats = {
            'total_packets': 0,
            'total_bytes': 0,
            'encoding_time_ms': 0.0,
        }
        # Note: We don't reset packet_counter to maintain sequence continuity


# ═══════════════════════════════════════════════════════════════
# DEBUGGING AND TESTING HELPERS
# ═══════════════════════════════════════════════════════════════

def test_packetizer():
    """
    Simple test function to demonstrate packetizer usage.

    This is a teaching example showing how to:
        1. Create a packetizer
        2. Encode frames
        3. Verify checksums
        4. Inspect statistics
    """
    print("Testing Packetizer...")
    print()

    # Create packetizer
    packetizer = Packetizer(encoding="raw")

    # Create sample telemetry frame (simulating simulator output)
    sample_frame = {
        'timestamp': 100.5,
        'frame_id': 42,
        'roll': 1.2,
        'pitch': -0.5,
        'heading': 45.0,
        'battery_voltage': 28.4,
        'battery_current': 2.1,
        'battery_soc': 85.3,
        'battery_temp': 15.2,
        'x': 150.0,
        'y': 200.0,
        'velocity': 0.5,
        'env_info': {'is_science_window': True},
    }

    # Encode frame into packet
    packet = packetizer.encode_frame(sample_frame)

    # Display packet
    packetizer.print_packet(packet, verbose=True)
    print()

    # Verify checksum
    is_valid = packetizer.verify_checksum(packet)
    print(f"Checksum valid: {is_valid}")
    print()

    # Show statistics
    stats = packetizer.get_statistics()
    print("Packetizer Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    # Test corruption detection
    print("Testing corruption detection...")
    packet['payload']['telemetry']['battery_soc'] = 999.9  # Corrupt data
    is_valid_after = packetizer.verify_checksum(packet)
    print(f"Checksum valid after corruption: {is_valid_after}")
    print()

    print("Packetizer test complete!")


if __name__ == "__main__":
    # Run test when script is executed directly
    test_packetizer()
