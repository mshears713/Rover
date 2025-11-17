"""
Unit tests for Packetizer class.

Tests cover:
    - Packet encoding and structure
    - Checksum calculation and verification
    - Priority assignment
    - Packet size estimation
    - Statistics tracking
"""

import pytest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'meridian3' / 'src'))

from pipeline.packetizer import Packetizer


@pytest.fixture
def sample_frame():
    """Provide a sample telemetry frame."""
    return {
        'timestamp': 100.5,
        'frame_id': 42,
        'battery_soc': 85.3,
        'battery_voltage': 28.4,
        'battery_temp': 15.2,
        'roll': 1.2,
        'pitch': -0.5,
        'heading': 45.0,
        'velocity': 0.05,
    }


class TestPacketizerInitialization:
    """Test Packetizer initialization."""

    def test_creates_packetizer(self):
        """Packetizer should create successfully."""
        packetizer = Packetizer()
        assert packetizer is not None

    def test_default_encoding_is_raw(self):
        """Default encoding should be 'raw'."""
        packetizer = Packetizer()
        assert packetizer.encoding == "raw"

    def test_can_set_encoding(self):
        """Should be able to set encoding mode."""
        packetizer = Packetizer(encoding="compressed")
        assert packetizer.encoding == "compressed"

    def test_packet_counter_starts_at_zero(self):
        """Packet counter should start at 0."""
        packetizer = Packetizer()
        assert packetizer.packet_counter == 0


class TestPacketEncoding:
    """Test packet encoding functionality."""

    def test_encode_frame_returns_packet(self, sample_frame):
        """encode_frame should return a packet dict."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        assert isinstance(packet, dict)
        assert 'header' in packet
        assert 'payload' in packet
        assert 'footer' in packet

    def test_packet_header_contains_metadata(self, sample_frame):
        """Packet header should contain required metadata."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        header = packet['header']
        assert 'packet_id' in header
        assert 'timestamp' in header
        assert 'frame_id' in header
        assert 'encoding' in header
        assert 'priority' in header
        assert 'packet_size' in header

    def test_packet_payload_contains_telemetry(self, sample_frame):
        """Packet payload should contain telemetry data."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        payload = packet['payload']
        assert 'telemetry' in payload
        assert payload['telemetry']['battery_soc'] == 85.3

    def test_packet_footer_contains_checksum(self, sample_frame):
        """Packet footer should contain checksum and timestamp."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        footer = packet['footer']
        assert 'checksum' in footer
        assert 'transmission_time' in footer

    def test_packet_id_increments(self, sample_frame):
        """Packet ID should increment with each encoding."""
        packetizer = Packetizer()

        packet1 = packetizer.encode_frame(sample_frame)
        packet2 = packetizer.encode_frame(sample_frame)
        packet3 = packetizer.encode_frame(sample_frame)

        assert packet1['header']['packet_id'] == 0
        assert packet2['header']['packet_id'] == 1
        assert packet3['header']['packet_id'] == 2

    def test_timestamp_preserved(self, sample_frame):
        """Frame timestamp should be preserved in packet."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        assert packet['header']['timestamp'] == 100.5

    def test_frame_id_preserved(self, sample_frame):
        """Frame ID should be preserved in packet."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        assert packet['header']['frame_id'] == 42


class TestChecksumCalculation:
    """Test checksum calculation and verification."""

    def test_checksum_is_calculated(self, sample_frame):
        """Checksum should be calculated for each packet."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        checksum = packet['footer']['checksum']
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) > 0

    def test_identical_frames_have_identical_checksums(self, sample_frame):
        """Same frame should produce same checksum."""
        packetizer1 = Packetizer()
        packetizer2 = Packetizer()

        packet1 = packetizer1.encode_frame(sample_frame)
        packet2 = packetizer2.encode_frame(sample_frame)

        # Checksums depend on header (including packet_id), so we need
        # to compare packets with same packet_id
        assert packet1['footer']['checksum'] == packet2['footer']['checksum']

    def test_different_frames_have_different_checksums(self, sample_frame):
        """Different frames should produce different checksums."""
        packetizer = Packetizer()

        packet1 = packetizer.encode_frame(sample_frame)

        modified_frame = sample_frame.copy()
        modified_frame['battery_soc'] = 50.0
        packet2 = packetizer.encode_frame(modified_frame)

        # Different packet IDs will make checksums different anyway,
        # but the payload difference is what we're testing
        assert packet1['footer']['checksum'] != packet2['footer']['checksum']

    def test_verify_checksum_valid_packet(self, sample_frame):
        """verify_checksum should return True for valid packet."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        assert packetizer.verify_checksum(packet) is True

    def test_verify_checksum_corrupted_packet(self, sample_frame):
        """verify_checksum should return False for corrupted packet."""
        packetizer = Packetizer()
        packet = packetizer.encode_frame(sample_frame)

        # Corrupt the payload
        packet['payload']['telemetry']['battery_soc'] = 999.9

        assert packetizer.verify_checksum(packet) is False


class TestPriorityAssignment:
    """Test packet priority calculation."""

    def test_low_battery_gets_high_priority(self):
        """Low battery frames should get critical priority."""
        packetizer = Packetizer()
        frame = {'battery_soc': 10.0, 'timestamp': 0.0, 'frame_id': 0}
        packet = packetizer.encode_frame(frame)

        assert packet['header']['priority'] == 10  # Critical

    def test_moderate_battery_gets_elevated_priority(self):
        """Moderate battery frames should get elevated priority."""
        packetizer = Packetizer()
        frame = {'battery_soc': 30.0, 'timestamp': 0.0, 'frame_id': 0}
        packet = packetizer.encode_frame(frame)

        assert packet['header']['priority'] >= 7

    def test_normal_battery_gets_normal_priority(self):
        """Normal battery frames should get medium priority."""
        packetizer = Packetizer()
        frame = {'battery_soc': 85.0, 'timestamp': 0.0, 'frame_id': 0}
        packet = packetizer.encode_frame(frame)

        assert packet['header']['priority'] <= 6

    def test_thermal_anomaly_gets_high_priority(self):
        """Extreme temperatures should elevate priority."""
        packetizer = Packetizer()
        frame = {'battery_temp': 70.0, 'timestamp': 0.0, 'frame_id': 0}
        packet = packetizer.encode_frame(frame)

        assert packet['header']['priority'] >= 8


class TestPacketStatistics:
    """Test statistics tracking."""

    def test_tracks_total_packets(self, sample_frame):
        """Should track total packet count."""
        packetizer = Packetizer()

        for _ in range(5):
            packetizer.encode_frame(sample_frame)

        stats = packetizer.get_statistics()
        assert stats['total_packets'] == 5

    def test_tracks_total_bytes(self, sample_frame):
        """Should track total bytes written."""
        packetizer = Packetizer()
        packetizer.encode_frame(sample_frame)

        stats = packetizer.get_statistics()
        assert stats['total_bytes'] > 0

    def test_calculates_average_packet_size(self, sample_frame):
        """Should calculate average packet size."""
        packetizer = Packetizer()

        for _ in range(10):
            packetizer.encode_frame(sample_frame)

        stats = packetizer.get_statistics()
        assert stats['avg_packet_size'] > 0
        assert stats['avg_packet_size'] == stats['total_bytes'] / 10

    def test_reset_statistics(self, sample_frame):
        """reset_statistics should clear counters."""
        packetizer = Packetizer()

        for _ in range(5):
            packetizer.encode_frame(sample_frame)

        packetizer.reset_statistics()

        stats = packetizer.get_statistics()
        assert stats['total_packets'] == 0
        assert stats['total_bytes'] == 0

    def test_reset_statistics_preserves_packet_counter(self, sample_frame):
        """reset_statistics should NOT reset packet_id counter."""
        packetizer = Packetizer()

        for _ in range(3):
            packetizer.encode_frame(sample_frame)

        packetizer.reset_statistics()
        packet = packetizer.encode_frame(sample_frame)

        # Packet ID should continue from 3, not reset to 0
        assert packet['header']['packet_id'] == 3


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_empty_frame(self):
        """Should handle empty frame."""
        packetizer = Packetizer()
        empty_frame = {}
        packet = packetizer.encode_frame(empty_frame)

        assert 'header' in packet
        assert 'payload' in packet
        assert 'footer' in packet

    def test_frame_with_missing_timestamp(self):
        """Should handle frame without timestamp."""
        packetizer = Packetizer()
        frame = {'battery_soc': 85.0, 'frame_id': 10}
        packet = packetizer.encode_frame(frame)

        # Should use default timestamp of 0.0
        assert packet['header']['timestamp'] == 0.0

    def test_frame_with_missing_frame_id(self):
        """Should handle frame without frame_id."""
        packetizer = Packetizer()
        frame = {'battery_soc': 85.0, 'timestamp': 100.0}
        packet = packetizer.encode_frame(frame)

        # Should use default frame_id of -1
        assert packet['header']['frame_id'] == -1

    def test_very_large_frame(self):
        """Should handle frame with many fields."""
        packetizer = Packetizer()
        large_frame = {f'field_{i}': float(i) for i in range(100)}
        large_frame['timestamp'] = 0.0
        large_frame['frame_id'] = 0

        packet = packetizer.encode_frame(large_frame)

        assert packet['header']['packet_size'] > 1000

    def test_packet_counter_overflow_scenario(self, sample_frame):
        """Packet counter should handle large numbers."""
        packetizer = Packetizer()
        packetizer.packet_counter = 999999

        packet = packetizer.encode_frame(sample_frame)

        assert packet['header']['packet_id'] == 999999
        assert packetizer.packet_counter == 1000000
