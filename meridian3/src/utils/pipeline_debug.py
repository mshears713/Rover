"""
Pipeline Debugging Helpers - Packet Inspection and Visualization

PURPOSE:
    Provides utilities for debugging and inspecting the telemetry pipeline.
    These tools help developers trace data flow, identify corruption,
    and validate pipeline behavior.

TEACHING GOALS:
    - Debugging techniques for data pipelines
    - Visualization of data flow
    - Inspection and validation tools
    - Understanding failure modes through debugging

DEBUGGING PHILOSOPHY:
    Good debugging tools are essential for complex systems. When building
    a multi-stage pipeline (Packetizer → Corruptor → Cleaner → Detector),
    you need visibility into each stage:

        1. What went in?
        2. What came out?
        3. What changed?
        4. Why did it change?

    These helpers answer those questions.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@dataclass
class PipelineTrace:
    """
    Captures the state of data at each pipeline stage.

    Attributes:
        raw_frame: Original simulator output
        packet: After packetization
        corrupted_packet: After corruption
        clean_frame: After cleaning
        labeled_frame: After anomaly detection
    """
    raw_frame: Optional[dict] = None
    packet: Optional[dict] = None
    corrupted_packet: Optional[dict] = None
    clean_frame: Optional[dict] = None
    labeled_frame: Optional[dict] = None


class PipelineDebugger:
    """
    Debugging utilities for telemetry pipeline.

    Provides tracing, inspection, and visualization of data flow.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize debugger.

        Args:
            verbose: If True, print detailed output during operations
        """
        self.verbose = verbose
        self.traces: List[PipelineTrace] = []

    def trace_pipeline(
        self,
        raw_frame: dict,
        packet: dict,
        corrupted_packet: Optional[dict],
        clean_frame: Optional[dict],
        labeled_frame: Optional[dict]
    ) -> PipelineTrace:
        """
        Create a trace of data through all pipeline stages.

        Args:
            raw_frame: Original frame from simulator
            packet: After packetizer
            corrupted_packet: After corruptor (None if lost)
            clean_frame: After cleaner (None if unrecoverable)
            labeled_frame: After anomaly detector

        Returns:
            PipelineTrace object capturing all stages

        Example:
            >>> debugger = PipelineDebugger(verbose=True)
            >>> trace = debugger.trace_pipeline(
            ...     raw_frame=sim_frame,
            ...     packet=packetizer.encode_frame(sim_frame),
            ...     corrupted_packet=corruptor.corrupt_packet(packet),
            ...     clean_frame=cleaner.clean_packet(corrupted_packet),
            ...     labeled_frame=detector.analyze_frame(clean_frame)
            ... )
        """
        trace = PipelineTrace(
            raw_frame=raw_frame,
            packet=packet,
            corrupted_packet=corrupted_packet,
            clean_frame=clean_frame,
            labeled_frame=labeled_frame
        )

        self.traces.append(trace)

        if self.verbose:
            self.print_trace(trace)

        return trace

    def print_trace(self, trace: PipelineTrace):
        """
        Print detailed trace information.

        Args:
            trace: Pipeline trace to display
        """
        print("═" * 70)
        print("PIPELINE TRACE")
        print("═" * 70)

        # Stage 1: Raw Frame
        print("\n┌─ Stage 1: Raw Frame (Simulator Output)")
        if trace.raw_frame:
            print(f"│  Timestamp: {trace.raw_frame.get('timestamp', 'N/A')}")
            print(f"│  Frame ID: {trace.raw_frame.get('frame_id', 'N/A')}")
            print(f"│  Fields: {len(trace.raw_frame)}")
        else:
            print("│  [None]")

        # Stage 2: Packet
        print("\n┌─ Stage 2: Packet (After Packetizer)")
        if trace.packet:
            header = trace.packet.get('header', {})
            print(f"│  Packet ID: {header.get('packet_id', 'N/A')}")
            print(f"│  Priority: {header.get('priority', 'N/A')}")
            print(f"│  Size: {header.get('packet_size', 'N/A')} bytes")
            print(f"│  Checksum: {trace.packet.get('footer', {}).get('checksum', 'N/A')[:8]}...")
        else:
            print("│  [None]")

        # Stage 3: Corrupted Packet
        print("\n┌─ Stage 3: Corrupted Packet (After Corruptor)")
        if trace.corrupted_packet:
            footer = trace.corrupted_packet.get('footer', {})
            corrupted = footer.get('corruption_detected', False)
            if corrupted:
                fields = footer.get('corrupted_fields', [])
                print(f"│  CORRUPTED: {len(fields)} fields affected")
                print(f"│  Affected fields: {', '.join(fields[:3])}...")
            else:
                print("│  Status: Clean (no corruption)")
        else:
            print("│  [PACKET LOST]")

        # Stage 4: Clean Frame
        print("\n┌─ Stage 4: Clean Frame (After Cleaner)")
        if trace.clean_frame:
            metadata = trace.clean_frame.get('metadata', {})
            quality = metadata.get('quality', 'unknown')
            repairs = metadata.get('repairs', [])
            print(f"│  Quality: {quality}")
            print(f"│  Repairs: {len(repairs)} fields repaired")
            if repairs:
                for repair in repairs[:2]:
                    print(f"│    - {repair['field']}: {repair['method']}")
        else:
            print("│  [UNRECOVERABLE]")

        # Stage 5: Labeled Frame
        print("\n┌─ Stage 5: Labeled Frame (After Anomaly Detector)")
        if trace.labeled_frame:
            anomalies = trace.labeled_frame.get('metadata', {}).get('anomalies', [])
            print(f"│  Anomalies: {len(anomalies)} detected")
            for anomaly in anomalies[:3]:
                print(f"│    - {anomaly['severity'].upper()}: {anomaly['description']}")
        else:
            print("│  [None]")

        print("\n" + "═" * 70)

    def compare_frames(self, frame1: dict, frame2: dict, label1: str = "Frame 1", label2: str = "Frame 2"):
        """
        Compare two frames and show differences.

        Args:
            frame1: First frame
            frame2: Second frame
            label1: Label for first frame
            label2: Label for second frame

        Teaching Note:
            Comparing frames at different pipeline stages reveals what
            each stage does to the data. Useful for understanding
            corruption, cleaning, and anomaly detection.
        """
        print(f"\n{'─' * 70}")
        print(f"COMPARING: {label1} vs {label2}")
        print(f"{'─' * 70}")

        # Extract data sections
        data1 = frame1.get('data', frame1)
        data2 = frame2.get('data', frame2)

        all_keys = set(data1.keys()) | set(data2.keys())

        differences = []
        for key in sorted(all_keys):
            val1 = data1.get(key, "MISSING")
            val2 = data2.get(key, "MISSING")

            if val1 != val2:
                differences.append((key, val1, val2))

        if differences:
            print(f"\nFound {len(differences)} differences:")
            print(f"\n{'Field':<20} {'Frame 1':<25} {'Frame 2':<25}")
            print("─" * 70)
            for key, val1, val2 in differences:
                v1_str = f"{val1:.4f}" if isinstance(val1, float) else str(val1)
                v2_str = f"{val2:.4f}" if isinstance(val2, float) else str(val2)
                print(f"{key:<20} {v1_str:<25} {v2_str:<25}")
        else:
            print("\nNo differences found - frames are identical")

        print("─" * 70)

    def inspect_packet(self, packet: dict, show_payload: bool = False):
        """
        Detailed inspection of a packet.

        Args:
            packet: Packet to inspect
            show_payload: If True, show full telemetry payload

        Teaching Note:
            Packet inspection helps understand:
                - Header structure and metadata
                - Payload organization
                - Footer validation data
                - Size and priority calculation
        """
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " PACKET INSPECTION".center(68) + "║")
        print("╠" + "═" * 68 + "╣")

        # Header
        print("║ HEADER:".ljust(69) + "║")
        header = packet.get('header', {})
        for key, value in header.items():
            line = f"║   {key}: {value}"
            print(line.ljust(69) + "║")

        # Payload
        print("║".ljust(69) + "║")
        print("║ PAYLOAD:".ljust(69) + "║")
        payload = packet.get('payload', {})
        telemetry = payload.get('telemetry', {})
        print(f"║   telemetry fields: {len(telemetry)}".ljust(69) + "║")

        if show_payload:
            for key, value in list(telemetry.items())[:10]:  # Show first 10
                val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                line = f"║     {key}: {val_str}"
                print(line[:69].ljust(69) + "║")
            if len(telemetry) > 10:
                print(f"║     ... ({len(telemetry) - 10} more fields)".ljust(69) + "║")

        # Footer
        print("║".ljust(69) + "║")
        print("║ FOOTER:".ljust(69) + "║")
        footer = packet.get('footer', {})
        for key, value in footer.items():
            if key == 'corrupted_fields' and value:
                val_str = f"[{', '.join(value[:3])}{'...' if len(value) > 3 else ''}]"
            else:
                val_str = str(value)
            line = f"║   {key}: {val_str}"
            print(line[:69].ljust(69) + "║")

        print("╚" + "═" * 68 + "╝")

    def visualize_corruption(self, clean_packet: dict, corrupted_packet: Optional[dict]):
        """
        Visualize what the corruptor did to a packet.

        Args:
            clean_packet: Original clean packet
            corrupted_packet: After corruption (or None if lost)

        Teaching Note:
            Visualizing corruption helps understand failure modes and
            test cleaning algorithms. Shows exactly what data was lost
            or modified.
        """
        print("\n" + "┏" + "━" * 68 + "┓")
        print("┃" + " CORRUPTION VISUALIZATION".center(68) + "┃")
        print("┣" + "━" * 68 + "┫")

        if corrupted_packet is None:
            print("┃ RESULT: PACKET COMPLETELY LOST".ljust(69) + "┃")
            print("┗" + "━" * 68 + "┛")
            return

        # Compare telemetry
        clean_telem = clean_packet.get('payload', {}).get('telemetry', {})
        corrupt_telem = corrupted_packet.get('payload', {}).get('telemetry', {})

        corrupted_fields = corrupted_packet.get('footer', {}).get('corrupted_fields', [])

        if not corrupted_fields:
            print("┃ RESULT: No corruption detected".ljust(69) + "┃")
        else:
            print(f"┃ RESULT: {len(corrupted_fields)} fields corrupted".ljust(69) + "┃")
            print("┃".ljust(69) + "┃")

            for field in corrupted_fields:
                original = clean_telem.get(field, "N/A")
                corrupted = corrupt_telem.get(field, "N/A")

                orig_str = f"{original:.4f}" if isinstance(original, float) else str(original)
                corr_str = f"{corrupted:.4f}" if isinstance(corrupted, float) else str(corrupted)

                print(f"┃ {field}:".ljust(69) + "┃")
                print(f"┃   Original:  {orig_str}".ljust(69) + "┃")
                print(f"┃   Corrupted: {corr_str}".ljust(69) + "┃")

        print("┗" + "━" * 68 + "┛")

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate debugging report from all traces.

        Args:
            output_path: If provided, write report to file

        Returns:
            Report as string

        Teaching Note:
            Reports are useful for:
                - Documenting pipeline behavior
                - Sharing debugging information
                - Automated testing and validation
                - Performance analysis
        """
        lines = []
        lines.append("=" * 70)
        lines.append("PIPELINE DEBUGGING REPORT")
        lines.append("=" * 70)
        lines.append(f"\nTotal traces captured: {len(self.traces)}")

        # Statistics
        packets_lost = sum(1 for t in self.traces if t.corrupted_packet is None)
        frames_corrupted = sum(
            1 for t in self.traces
            if t.corrupted_packet and t.corrupted_packet.get('footer', {}).get('corruption_detected', False)
        )
        frames_with_anomalies = sum(
            1 for t in self.traces
            if t.labeled_frame and t.labeled_frame.get('metadata', {}).get('anomalies', [])
        )

        lines.append(f"\nPackets lost: {packets_lost} ({packets_lost/len(self.traces)*100:.1f}%)")
        lines.append(f"Packets corrupted: {frames_corrupted} ({frames_corrupted/len(self.traces)*100:.1f}%)")
        lines.append(f"Frames with anomalies: {frames_with_anomalies} ({frames_with_anomalies/len(self.traces)*100:.1f}%)")

        # Recent anomalies
        lines.append("\n" + "─" * 70)
        lines.append("RECENT ANOMALIES:")
        lines.append("─" * 70)

        anomaly_count = 0
        for trace in reversed(self.traces):
            if trace.labeled_frame:
                anomalies = trace.labeled_frame.get('metadata', {}).get('anomalies', [])
                for anomaly in anomalies:
                    lines.append(f"\n[{trace.labeled_frame.get('timestamp', 'N/A')}] {anomaly['severity'].upper()}")
                    lines.append(f"  {anomaly['description']}")
                    anomaly_count += 1
                    if anomaly_count >= 10:  # Show only last 10
                        break
            if anomaly_count >= 10:
                break

        lines.append("\n" + "=" * 70)

        report = "\n".join(lines)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
            lines.append(f"\nReport written to: {output_path}")

        return report


# ═══════════════════════════════════════════════════════════════
# QUICK INSPECTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def quick_inspect(obj: Any, max_depth: int = 2, indent: int = 0):
    """
    Quick inspection of any object (frame, packet, dict, etc.).

    Args:
        obj: Object to inspect
        max_depth: Maximum nesting depth to display
        indent: Current indentation level (for recursion)
    """
    prefix = "  " * indent

    if isinstance(obj, dict):
        print(f"{prefix}{{")
        for key, value in obj.items():
            if indent < max_depth:
                print(f"{prefix}  {key}:", end=" ")
                if isinstance(value, (dict, list)):
                    print()
                    quick_inspect(value, max_depth, indent + 1)
                else:
                    val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    print(val_str)
            else:
                print(f"{prefix}  {key}: ...")
        print(f"{prefix}}}")

    elif isinstance(obj, list):
        print(f"{prefix}[")
        for i, item in enumerate(obj[:5]):  # Show first 5 items
            if isinstance(item, (dict, list)):
                quick_inspect(item, max_depth, indent + 1)
            else:
                print(f"{prefix}  {item}")
        if len(obj) > 5:
            print(f"{prefix}  ... ({len(obj) - 5} more items)")
        print(f"{prefix}]")

    else:
        print(f"{prefix}{obj}")


def diff_frames(frame1: dict, frame2: dict) -> List[str]:
    """
    Get list of fields that differ between two frames.

    Args:
        frame1: First frame
        frame2: Second frame

    Returns:
        List of field names that differ

    Example:
        >>> diffs = diff_frames(original, repaired)
        >>> print(f"Repaired {len(diffs)} fields: {diffs}")
    """
    data1 = frame1.get('data', frame1)
    data2 = frame2.get('data', frame2)

    all_keys = set(data1.keys()) | set(data2.keys())
    differences = []

    for key in all_keys:
        if data1.get(key) != data2.get(key):
            differences.append(key)

    return differences


# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════

def test_debugging_helpers():
    """
    Test debugging helper functions.
    """
    print("Testing Pipeline Debugging Helpers...")
    print()

    debugger = PipelineDebugger(verbose=False)

    # Create sample data for each stage
    raw_frame = {
        'timestamp': 100.0,
        'frame_id': 42,
        'battery_soc': 75.0,
        'battery_voltage': 28.0,
        'battery_temp': 20.0,
    }

    packet = {
        'header': {
            'packet_id': 10,
            'timestamp': 100.0,
            'frame_id': 42,
            'priority': 5,
            'packet_size': 512,
        },
        'payload': {
            'telemetry': raw_frame.copy()
        },
        'footer': {
            'checksum': 'abc123def456',
            'corruption_detected': False,
            'corrupted_fields': []
        }
    }

    corrupted_packet = {
        'header': packet['header'].copy(),
        'payload': {
            'telemetry': {
                'timestamp': 100.0,
                'frame_id': 42,
                'battery_soc': None,  # Corrupted!
                'battery_voltage': 28.0,
                'battery_temp': 999.0,  # Corrupted!
            }
        },
        'footer': {
            'checksum': 'abc123def456',
            'corruption_detected': True,
            'corrupted_fields': ['battery_soc', 'battery_temp']
        }
    }

    clean_frame = {
        'timestamp': 100.0,
        'frame_id': 42,
        'data': {
            'battery_soc': 75.0,  # Repaired
            'battery_voltage': 28.0,
            'battery_temp': 20.0,  # Repaired
        },
        'metadata': {
            'quality': 'medium',
            'repairs': [
                {'field': 'battery_soc', 'method': 'interpolation'},
                {'field': 'battery_temp', 'method': 'range_clamp'}
            ]
        }
    }

    labeled_frame = clean_frame.copy()
    labeled_frame['metadata']['anomalies'] = [{
        'field': 'battery_soc',
        'value': 75.0,
        'type': 'threshold',
        'severity': 'warning',
        'description': 'Battery SOC below 80%'
    }]

    # Test 1: Create trace
    print("Test 1: Create pipeline trace...")
    trace = debugger.trace_pipeline(
        raw_frame=raw_frame,
        packet=packet,
        corrupted_packet=corrupted_packet,
        clean_frame=clean_frame,
        labeled_frame=labeled_frame
    )
    debugger.print_trace(trace)

    # Test 2: Inspect packet
    print("\n\nTest 2: Inspect packet...")
    debugger.inspect_packet(packet, show_payload=True)

    # Test 3: Visualize corruption
    print("\n\nTest 3: Visualize corruption...")
    debugger.visualize_corruption(packet, corrupted_packet)

    # Test 4: Compare frames
    print("\n\nTest 4: Compare frames...")
    debugger.compare_frames(raw_frame, clean_frame['data'], "Raw", "Cleaned")

    # Test 5: Generate report
    print("\n\nTest 5: Generate report...")
    report = debugger.generate_report()
    print(report)

    print("\n\nDebugging helpers test complete!")


if __name__ == "__main__":
    test_debugging_helpers()
