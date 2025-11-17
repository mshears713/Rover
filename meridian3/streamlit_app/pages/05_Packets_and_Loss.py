"""
Chapter 5: Packets and Loss

TEACHING FOCUS:
    - Telemetry packet structure
    - Transmission encoding and metadata
    - Communication channel imperfections
    - Packet loss and corruption modeling

NARRATIVE:
    Telemetry doesn't magically appear on Earth. It travels hundreds of
    millions of kilometers through space, facing interference, noise, and
    data loss. Understanding the transmission layer is critical for robust
    ground systems.

LEARNING OBJECTIVES:
    - Understand packet structure and encoding
    - Model realistic transmission errors
    - Calculate packet loss statistics
    - Design for degraded communication channels

IMPLEMENTATION:
    Full interactive implementation in Phase 4, Step 36.
"""

import streamlit as st

st.set_page_config(page_title="Packets and Loss", page_icon="📡", layout="wide")

st.title("📡 Chapter 5: Packets and Loss")

st.markdown("""
## From Rover to Earth: The Transmission Challenge

Raw sensor frames must be packaged, encoded, and transmitted across vast
distances. Not all data makes it through intact.

---

### Packet Structure

A telemetry packet includes:

**Header**:
- Packet ID (sequence number)
- Timestamp
- Source identifier
- Packet type

**Payload**:
- Sensor readings (encoded/compressed)
- Engineering data
- Science data

**Footer**:
- Checksum (error detection)
- End-of-packet marker

---

### Transmission Imperfections

**Packet Loss**:
- Entire packets fail to arrive
- Typical rate: 1-5% in nominal conditions
- Higher during conjunction, dust storms

**Bit Flips**:
- Individual bits corrupted in transmission
- Typical rate: 10^-6 to 10^-4 per bit
- Detected by checksum, corrected by error codes

**Field Corruption**:
- Partial payload corruption
- Some fields arrive intact, others garbled
- Requires field-level validation

**Timing Jitter**:
- Packets arrive out of order
- Irregular spacing
- Requires timestamp-based sorting

**Complete Dropouts**:
- Extended periods with no communication
- During conjunction (Mars behind Sun)
- During relay satellite outages

---

### Error Detection and Correction

**Checksums**:
- Simple error detection (CRC, hash)
- Detects corruption but can't fix it

**Forward Error Correction (FEC)**:
- Redundant encoding allows reconstruction
- Example: Reed-Solomon codes
- Trade bandwidth for reliability

**Retransmission**:
- Request missing/corrupted packets again
- Requires two-way communication
- Not always feasible (e.g., during conjunction)

---

## Interactive Features

*Full interactive packet simulator will be implemented in Phase 4*

This chapter will include:
- Packet encoding visualizer
- Corruption simulator with adjustable error rates
- Lost packet tracker
- Error correction demonstration

---

*Proceed to Chapter 6: Cleaning and Validation →*
""")
