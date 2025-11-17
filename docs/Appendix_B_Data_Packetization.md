# Appendix B: Data Packetization & Transmission

This appendix explains how raw sensor data is packaged for transmission over a simulated radio link, just like real spacecraft communicate with Earth.

---

## Part 1: Why Packetization Matters

### The Communication Challenge

**Beginner Explanation:**
Imagine you're on Mars and need to send data back to Earth. You can't just blast all your data at once! The radio link is slow (like old dial-up internet), has limited power, and sometimes the signal gets corrupted. So you need to:

1. **Break data into packets** (small chunks)
2. **Add headers** (like addressing an envelope)
3. **Add checksums** (to detect if data got corrupted)
4. **Prioritize important data** (send critical info first)

<details>
<summary><b>🔍 Intermediate Details: Real Spacecraft Communication Constraints</b></summary>

Real Mars rovers face severe communication limits:

- **Bandwidth**: 500 bits/second to 32 kbps (compared to home internet at ~100 Mbps = 100,000 kbps)
- **Latency**: 3-22 minutes one-way depending on Earth-Mars distance
- **Window**: Only ~4 hours per day when Mars orbiters are overhead
- **Power**: Every bit transmitted costs precious energy

**Packetization strategies help:**
- **Error detection**: Checksums catch corruption without retransmission
- **Priority**: Send "rover alive" status before science images
- **Efficiency**: Compress/downsample less-critical data
- **Recovery**: Lost packets can be requested again (when feasible)

The Consultative Committee for Space Data Systems (CCSDS) defines standard protocols used by NASA, ESA, and other agencies. Our implementation simplifies CCSDS concepts for teaching.

</details>

---

## Part 2: Packet Structure

### What's in a Packet?

**Beginner Explanation:**
A telemetry packet has three parts, like a sandwich:

- **Header** (top bun): Metadata about the packet
- **Payload** (filling): The actual sensor data
- **Footer** (bottom bun): Validation and transmission info

```
╔══════════════════════════════════════════════════════════════╗
║                    TELEMETRY PACKET                          ║
╠══════════════════════════════════════════════════════════════╣
║  HEADER (metadata)                                           ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ packet_id: 42            (sequence number)             │  ║
║  │ timestamp: 123.4         (mission time in seconds)     │  ║
║  │ frame_id: 100            (which sensor reading)        │  ║
║  │ encoding: "raw"          (compression type)            │  ║
║  │ priority: 5              (0=low to 10=critical)        │  ║
║  │ packet_size: 1024        (bytes)                       │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  PAYLOAD (sensor data)                                       ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ telemetry: {                                           │  ║
║  │   'roll': 2.3,                                         │  ║
║  │   'pitch': -1.1,                                       │  ║
║  │   'battery_soc': 75.2,                                 │  ║
║  │   ... (all sensor readings)                            │  ║
║  │ }                                                       │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  FOOTER (validation)                                         ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ checksum: "a3f5b2c1..."  (error detection hash)       │  ║
║  │ transmission_time: 1234567890.123                      │  ║
║  └────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════╝
```

<details>
<summary><b>🔍 Intermediate Details: Packet Header Fields</b></summary>

Each header field serves a specific purpose:

**packet_id** (sequence number):
- Monotonically increasing counter
- Helps receivers detect missing packets
- Example: Packets 100, 101, 103 arrive → packet 102 is missing

**timestamp** (mission elapsed time):
- When the data was collected
- Critical for reconstructing mission timeline
- Allows time-correlation analysis

**frame_id** (original telemetry frame ID):
- Links packet back to sensor reading
- Multiple packets might come from same frame (if data is split)

**encoding** (compression/format):
- "raw" = no compression, full precision
- "compressed" = data reduced to save bandwidth (future enhancement)
- Receiver needs to know how to decode

**priority** (0-10):
- Determines transmission order when bandwidth limited
- Critical: Battery failure (priority 10)
- Warning: Battery low (priority 8)
- Normal: Routine housekeeping (priority 5)

**packet_size** (bytes):
- Helps estimate transmission time
- Power cost is proportional to size
- Allows bandwidth allocation

</details>

---

## Part 3: The Packetizer Code

### Creating a Packet

**Beginner Explanation:**
The `Packetizer` class takes a telemetry frame and wraps it in a packet structure:

```python
class Packetizer:
    """Encodes telemetry frames into transmission packets."""

    def __init__(self, encoding: str = "raw"):
        self.encoding = encoding
        self.packet_counter = 0  # Sequence number for all packets

    def encode_frame(self, frame: dict) -> dict:
        """Encode a telemetry frame into a transmission packet."""

        # STEP 1: Determine packet priority based on frame contents
        priority = self._calculate_priority(frame)

        # STEP 2: Build packet header with metadata
        header = {
            'packet_id': self.packet_counter,
            'timestamp': frame.get('timestamp', 0.0),
            'frame_id': frame.get('frame_id', -1),
            'encoding': self.encoding,
            'priority': priority,
        }

        # STEP 3: Encode payload (currently just pass through)
        payload = {'telemetry': frame.copy()}

        # STEP 4: Calculate packet size
        packet_size = self._estimate_size(header, payload)
        header['packet_size'] = packet_size

        # STEP 5: Calculate checksum for error detection
        checksum = self._calculate_checksum(header, payload)

        # STEP 6: Build footer
        footer = {
            'checksum': checksum,
            'transmission_time': time.time(),
        }

        # STEP 7: Assemble complete packet
        packet = {
            'header': header,
            'payload': payload,
            'footer': footer,
        }

        self.packet_counter += 1
        return packet
```

**File location:** `meridian3/src/pipeline/packetizer.py:134-243`

<details>
<summary><b>🔍 Intermediate Details: Priority Calculation Algorithm</b></summary>

The priority calculation uses domain knowledge to assess data criticality:

```python
def _calculate_priority(self, frame: dict) -> int:
    """Determine packet priority based on telemetry content."""
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

    return priority
```

**File location:** `meridian3/src/pipeline/packetizer.py:245-293`

**Decision rationale:**
- Safety-critical conditions (low battery, thermal extremes) = highest priority
- Science opportunities = medium-high (mission value)
- Routine telemetry = default medium

This mirrors real mission operations where engineers define priority schemes based on:
- Hardware safety limits
- Mission objectives
- Past experience with anomalies

</details>

---

## Part 4: Checksums - Detecting Corruption

### What is a Checksum?

**Beginner Explanation:**
A checksum is like a "fingerprint" of the data. If even one bit changes during transmission, the fingerprint changes completely. The receiver calculates the fingerprint from received data and compares it to the transmitted fingerprint. If they don't match, the data got corrupted.

Example:
```
Original data: "battery_soc: 75.2"
Checksum: "a3f5b2c1"

Corrupted data: "battery_soc: 95.2"  (75 changed to 95!)
Checksum: "7d4e1a89"  (completely different!)
```

<details>
<summary><b>🔍 Intermediate Details: Checksum Algorithm</b></summary>

The packetizer uses SHA-256 hashing for checksums:

```python
def _calculate_checksum(self, header: dict, payload: dict) -> str:
    """Calculate checksum for error detection."""

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
```

**File location:** `meridian3/src/pipeline/packetizer.py:356-389`

**Why SHA-256?**
- **Strong**: Detects all single-bit and multi-bit errors
- **One-way**: Can't forge data to match checksum
- **Collision-resistant**: Two different packets won't have same checksum

**In production, we'd use:**
- **CRC-16 or CRC-32**: Faster, simpler, standard for spacecraft
- **Reed-Solomon codes**: Can actually *correct* errors, not just detect them

**Checksum verification:**
```python
def verify_checksum(self, packet: dict) -> bool:
    """Verify packet checksum matches contents."""
    # Recalculate checksum from header and payload
    calculated = self._calculate_checksum(packet['header'], packet['payload'])

    # Compare with stored checksum
    stored = packet['footer']['checksum']

    return calculated == stored
```

**File location:** `meridian3/src/pipeline/packetizer.py:391-422`

</details>

### Checksum Example

Here's what happens when we verify a packet:

```python
# Create packetizer
packetizer = Packetizer()

# Encode a frame into a packet
frame = {
    'timestamp': 100.5,
    'frame_id': 42,
    'battery_soc': 85.3,
    'roll': 1.2,
    # ... more fields
}
packet = packetizer.encode_frame(frame)

# Verify checksum - should be True
print(packetizer.verify_checksum(packet))  # True

# Corrupt the data
packet['payload']['telemetry']['battery_soc'] = 999.9

# Verify again - now False!
print(packetizer.verify_checksum(packet))  # False
```

---

## Part 5: Packet Size and Bandwidth

### Estimating Transmission Cost

**Beginner Explanation:**
Bigger packets take longer to send and use more power. The packetizer estimates packet size to help manage bandwidth.

```python
def _estimate_size(self, header: dict, payload: dict) -> int:
    """Estimate packet size in bytes."""

    # Serialize to JSON and measure length
    combined = {
        'header': header,
        'payload': payload,
    }
    json_string = json.dumps(combined)
    return len(json_string.encode('utf-8'))
```

**File location:** `meridian3/src/pipeline/packetizer.py:330-354`

<details>
<summary><b>🔍 Intermediate Details: Size vs Bandwidth Tradeoff</b></summary>

**Typical packet sizes:**
- **Header**: ~100 bytes (metadata)
- **Telemetry payload**: ~500-1000 bytes (depends on fields)
- **Footer**: ~50 bytes (checksum, timestamps)
- **Total**: ~650-1150 bytes per packet

**Transmission time calculation:**
```
Time = Packet_Size / Bandwidth

Example (500 bytes at 2 kbps):
Time = (500 bytes × 8 bits/byte) / (2000 bits/sec)
     = 4000 bits / 2000 bits/sec
     = 2 seconds
```

**Power consumption:**
If transmitter uses 10W, sending one packet costs:
```
Energy = Power × Time
       = 10W × 2 seconds
       = 20 joules
```

For a battery with 500 Wh (1,800,000 joules) capacity:
```
Packets per full battery = 1,800,000 J / 20 J = 90,000 packets
```

**Why this matters:**
- Real Mars rovers carefully budget transmission time
- Images are compressed heavily (JPEG quality ~10-30%)
- Some data is never sent (stored onboard for years)
- Priority system ensures critical data gets through

</details>

---

## Part 6: The Complete Packetization Process

### Step-by-Step Walkthrough

**Beginner Explanation:**
Here's what happens when a telemetry frame becomes a packet:

1. **Input**: Telemetry frame from sensors
   ```python
   frame = {
       'timestamp': 123.4,
       'frame_id': 100,
       'battery_soc': 75.2,
       'battery_voltage': 28.3,
       'cpu_temp': 35.4,
       # ... 15+ more fields
   }
   ```

2. **Priority Assessment**: Check if data is critical
   ```python
   priority = 5  # Normal, battery is healthy
   ```

3. **Header Creation**: Add metadata
   ```python
   header = {
       'packet_id': 0,
       'timestamp': 123.4,
       'frame_id': 100,
       'encoding': 'raw',
       'priority': 5,
       'packet_size': 842,  # Calculated
   }
   ```

4. **Payload Packaging**: Wrap telemetry
   ```python
   payload = {
       'telemetry': frame  # The actual sensor data
   }
   ```

5. **Checksum Calculation**: Generate fingerprint
   ```python
   checksum = "a3f5b2c148e7"  # SHA-256 hash (truncated)
   ```

6. **Footer Addition**: Add validation
   ```python
   footer = {
       'checksum': "a3f5b2c148e7",
       'transmission_time': 1234567890.123
   }
   ```

7. **Output**: Complete packet ready for transmission
   ```python
   packet = {
       'header': {...},
       'payload': {...},
       'footer': {...}
   }
   ```

<details>
<summary><b>🔍 Intermediate Details: Statistics Tracking</b></summary>

The packetizer tracks operational metrics:

```python
self.stats = {
    'total_packets': 0,
    'total_bytes': 0,
    'encoding_time_ms': 0.0,
}
```

After encoding:
```python
self.packet_counter += 1
self.stats['total_packets'] += 1
self.stats['total_bytes'] += packet_size
self.stats['encoding_time_ms'] += encoding_time_ms
```

**Why track statistics?**
- **Performance monitoring**: Detect slowdowns in encoding
- **Bandwidth planning**: Estimate total mission data volume
- **Debugging**: Identify unusual packet sizes or patterns

**Retrieving statistics:**
```python
stats = packetizer.get_statistics()
print(f"Sent {stats['total_packets']} packets")
print(f"Total data: {stats['total_bytes'] / 1024:.1f} KB")
print(f"Avg size: {stats['avg_packet_size']:.0f} bytes")
print(f"Avg encoding time: {stats['avg_encoding_time_ms']:.2f} ms")
```

</details>

---

## Key Takeaways

1. **Packets structure data** into header, payload, and footer sections
2. **Headers contain metadata** for routing, sequencing, and interpretation
3. **Checksums detect corruption** by creating data fingerprints
4. **Priority determines transmission order** when bandwidth is limited
5. **Size estimation helps manage** power and bandwidth budgets

### Where to Look in the Code

- **Packetizer class**: `meridian3/src/pipeline/packetizer.py:100-500`
- **encode_frame() method**: `meridian3/src/pipeline/packetizer.py:134-243`
- **Priority calculation**: `meridian3/src/pipeline/packetizer.py:245-293`
- **Checksum calculation**: `meridian3/src/pipeline/packetizer.py:356-389`
- **Checksum verification**: `meridian3/src/pipeline/packetizer.py:391-422`

---

**Previous:** [Appendix A: Sensor Data Generation](./Appendix_A_Sensor_Data_Generation.md)
**Next:** [Appendix C: Data Cleaning & Validation](./Appendix_C_Data_Cleaning.md)
