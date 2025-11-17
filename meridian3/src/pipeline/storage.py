"""
Storage - Mission Data Archival and Retrieval

PURPOSE:
    Persists telemetry data to SQLite database and manages caching for
    quick retrieval. Provides query interface for mission playback,
    analysis, and reporting.

THEORY:
    Mission data storage involves several engineering considerations:

        1. Persistence: Data must survive process crashes and reboots
            - SQLite: ACID-compliant, embedded database
            - File-based: No separate server process
            - Transactions: Atomic writes prevent corruption

        2. Performance: Balance write speed vs query speed
            - Batch writes: Group insertions for efficiency
            - Indexes: Speed up time-range queries
            - Caching: Keep recent data in memory

        3. Schema Design: Structure for time-series telemetry
            - Normalized: Separate tables for different data types
            - Denormalized: Single table with all fields (simpler)
            - We use denormalized for teaching simplicity

        4. Data Integrity: Ensure data correctness
            - Foreign keys: Maintain relationships
            - Constraints: Enforce valid values
            - Checksums: Detect corruption

        5. Archival: Long-term storage and compression
            - JSON export: Human-readable backup
            - Compression: Save disk space
            - Retention policies: Delete old data

MERIDIAN-3 STORY SNIPPET:
    "Sol 150: Our mission archive contains 12,960,000 telemetry frames.
    Every sensor reading since landing, preserved in SQLite. When engineers
    ask 'What was the battery temperature on Sol 47 at 14:30?', we query
    the database and get the answer in milliseconds. This archive is our
    mission's memory - without it, we'd be blind to trends and patterns."

ARCHITECTURE ROLE:
    Storage sits at the end of the processing pipeline, receiving clean,
    labeled telemetry frames and persisting them for long-term analysis.

    Anomaly Detector → Storage → Mission Archive (SQLite + JSON)
                                    ↓
                              Mission Console (queries)

STORAGE ARCHITECTURE DIAGRAM:

    ╔══════════════════════════════════════════════════════════════╗
    ║                    STORAGE ARCHITECTURE                      ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  Labeled Frame                                               ║
    ║      │                                                       ║
    ║      ▼                                                       ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 1: Serialize Frame             │                   ║
    ║  │  Convert to JSON string              │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 2: Insert to SQLite            │                   ║
    ║  │  Write to telemetry table            │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 3: Update Cache                │                   ║
    ║  │  Keep recent frames in memory        │                   ║
    ║  └──────────────┬───────────────────────┘                   ║
    ║                 │                                            ║
    ║                 ▼                                            ║
    ║  ┌──────────────────────────────────────┐                   ║
    ║  │  STEP 4: Commit Transaction          │                   ║
    ║  │  Ensure ACID durability              │                   ║
    ║  └──────────────────────────────────────┘                   ║
    ║                                                              ║
    ║  ┌────────────────────────────────────────────────┐         ║
    ║  │  QUERY INTERFACE                               │         ║
    ║  │  • query_frames(start_time, end_time)          │         ║
    ║  │  • get_latest(n)                               │         ║
    ║  │  • get_anomalies(severity)                     │         ║
    ║  │  • export_mission(format)                      │         ║
    ║  └────────────────────────────────────────────────┘         ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

TEACHING GOALS:
    - Database design for time-series data
    - SQLite usage and optimization
    - Data archival strategies
    - Query patterns for telemetry
    - ACID properties and durability

DEBUGGING NOTES:
    - To inspect database: sqlite3 missions.sqlite ".schema"
    - To check size: ls -lh data/missions.sqlite
    - To verify writes: SELECT COUNT(*) FROM telemetry
    - Common issue: Database locked (use WAL mode)
    - Performance: Batch inserts, use transactions

I/O AND DURABILITY COMMENTARY:
    Persistent storage is about managing failure modes:

    1. Process Crashes: SQLite transactions ensure atomic writes.
       Either all data is written or none - no partial corruption.

    2. Disk Full: Check available space before large writes.
       Implement retention policies to limit database size.

    3. Corruption: SQLite has built-in integrity checks.
       Regular PRAGMA integrity_check prevents silent corruption.

    4. Concurrent Access: WAL mode allows multiple readers during writes.
       Critical for real-time display while logging continues.

    5. Backup Strategy: Export to JSON provides human-readable backup.
       SQLite backup API creates consistent snapshots.

    Trade-offs:
    - Write-Ahead Logging (WAL): Faster writes, but extra files
    - Synchronous=FULL: Slower but maximum durability
    - Batch inserts: Faster but delays availability
    - In-memory cache: Fast reads but uses RAM

FUTURE EXTENSIONS:
    1. Implement data compression for old missions
    2. Add time-series database (InfluxDB, TimescaleDB)
    3. Support remote storage (S3, cloud databases)
    4. Implement incremental backups
    5. Add data retention and cleanup policies
    6. Support multiple concurrent missions
    7. Add full-text search on anomaly descriptions
"""

import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from collections import deque
from pathlib import Path
import time


class MissionStorage:
    """
    Archives and retrieves mission telemetry.

    Provides persistent storage using SQLite with in-memory caching
    for performance.
    """

    def __init__(self, db_path: str, cache_size: int = 100):
        """
        Initialize storage with database connection.

        Args:
            db_path: Path to SQLite database file
                - Will be created if doesn't exist
                - Parent directories created automatically

            cache_size: Number of recent frames to keep in memory
                - Larger: Better query performance for recent data
                - Smaller: Less memory usage
                - Default: 100 frames

        Teaching Note:
            SQLite is embedded - no separate server needed. The database
            is just a file. This simplifies deployment but means only
            one process should write at a time (readers can be concurrent
            with WAL mode).
        """
        self.db_path = db_path
        self.cache_size = cache_size

        # In-memory cache for recent frames
        self.frame_cache = deque(maxlen=cache_size)

        # Ensure parent directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database connection
        self._init_database()

        # Statistics tracking
        self.stats = {
            'frames_stored': 0,
            'total_bytes_written': 0,
            'queries_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }

    def _init_database(self):
        """
        Initialize database schema and connection.

        Creates tables if they don't exist and configures SQLite for
        optimal performance and durability.

        Teaching Note:
            Database initialization is idempotent - safe to run multiple
            times. CREATE TABLE IF NOT EXISTS ensures we don't error on
            existing tables.
        """
        # Connect to database
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name

        # Configure for performance and durability
        cursor = self.conn.cursor()

        # Enable Write-Ahead Logging for concurrent readers
        # Teaching: WAL allows reads while writing, critical for live display
        cursor.execute("PRAGMA journal_mode=WAL")

        # Synchronous=NORMAL: Balance between speed and safety
        # Teaching: FULL is slower but safer, OFF is faster but risky
        cursor.execute("PRAGMA synchronous=NORMAL")

        # Create telemetry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT,
                timestamp REAL NOT NULL,
                frame_id INTEGER,
                frame_data TEXT NOT NULL,  -- JSON serialized frame
                quality TEXT,
                has_anomalies INTEGER,
                created_at REAL NOT NULL
            )
        """)

        # Create index on timestamp for fast time-range queries
        # Teaching: Indexes speed up WHERE clauses but slow down INSERT
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
            ON telemetry(timestamp)
        """)

        # Create index on mission_id for multi-mission support
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_mission
            ON telemetry(mission_id, timestamp)
        """)

        # Create anomalies table for quick anomaly queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telemetry_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                field TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(telemetry_id) REFERENCES telemetry(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalies_severity
            ON anomalies(severity, timestamp)
        """)

        # Create missions metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                mission_id TEXT PRIMARY KEY,
                start_time REAL,
                end_time REAL,
                frame_count INTEGER,
                metadata TEXT
            )
        """)

        self.conn.commit()

    def store_frame(self, frame: dict, mission_id: str = "default"):
        """
        Store a telemetry frame to database.

        Args:
            frame: Telemetry frame to archive
                Expected structure: {timestamp, frame_id, data, metadata}
            mission_id: Identifier for this mission

        Teaching Note:
            We serialize the entire frame to JSON for simplicity. In a
            production system, you might normalize the data across multiple
            tables. Trade-off: JSON is flexible but harder to query specific
            fields efficiently.

        Example:
            >>> storage = MissionStorage("data/mission.db")
            >>> frame = detector.analyze_frame(clean_frame)
            >>> storage.store_frame(frame, mission_id="mars_2025")
        """
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Extract metadata
        # ═══════════════════════════════════════════════════════════════
        timestamp = frame.get('timestamp', 0.0)
        frame_id = frame.get('frame_id', -1)
        quality = frame.get('metadata', {}).get('quality', 'unknown')
        anomalies = frame.get('metadata', {}).get('anomalies', [])
        has_anomalies = 1 if anomalies else 0

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Serialize frame to JSON
        # ═══════════════════════════════════════════════════════════════
        # Teaching: JSON is human-readable and flexible, but larger than
        # binary formats. For teaching purposes, readability wins.
        frame_json = json.dumps(frame)
        frame_bytes = len(frame_json.encode('utf-8'))

        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Insert into database
        # ═══════════════════════════════════════════════════════════════
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO telemetry
            (mission_id, timestamp, frame_id, frame_data, quality, has_anomalies, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            mission_id,
            timestamp,
            frame_id,
            frame_json,
            quality,
            has_anomalies,
            time.time()
        ))

        telemetry_id = cursor.lastrowid

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Store anomalies in separate table
        # ═══════════════════════════════════════════════════════════════
        # Teaching: Separate table allows efficient anomaly queries without
        # parsing JSON. Normalization trade-off: more tables, faster queries.
        for anomaly in anomalies:
            cursor.execute("""
                INSERT INTO anomalies
                (telemetry_id, timestamp, field, anomaly_type, severity, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                telemetry_id,
                timestamp,
                anomaly.get('field', ''),
                anomaly.get('type', ''),
                anomaly.get('severity', ''),
                anomaly.get('description', '')
            ))

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Commit transaction
        # ═══════════════════════════════════════════════════════════════
        # Teaching: Commit ensures data is durable (survives crashes).
        # Without commit, data stays in memory and could be lost.
        self.conn.commit()

        # ═══════════════════════════════════════════════════════════════
        # STEP 6: Update cache
        # ═══════════════════════════════════════════════════════════════
        self.frame_cache.append(frame)

        # ═══════════════════════════════════════════════════════════════
        # STEP 7: Update statistics
        # ═══════════════════════════════════════════════════════════════
        self.stats['frames_stored'] += 1
        self.stats['total_bytes_written'] += frame_bytes

    def query_frames(
        self,
        start_time: float,
        end_time: float,
        mission_id: str = "default"
    ) -> List[dict]:
        """
        Retrieve frames in a time range.

        Args:
            start_time: Start of time range (mission seconds)
            end_time: End of time range (mission seconds)
            mission_id: Mission identifier

        Returns:
            List of telemetry frames (deserialized from JSON)

        Teaching Note:
            Time-range queries are common for telemetry. The timestamp
            index makes these queries fast (O(log n) seek + O(k) scan
            where k is result size).

        Example:
            >>> # Get all frames from first 10 minutes
            >>> frames = storage.query_frames(0.0, 600.0)
            >>> print(f"Found {len(frames)} frames")
        """
        self.stats['queries_executed'] += 1

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT frame_data FROM telemetry
            WHERE mission_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        """, (mission_id, start_time, end_time))

        frames = []
        for row in cursor.fetchall():
            frame = json.loads(row['frame_data'])
            frames.append(frame)

        return frames

    def get_latest(self, n: int = 10, mission_id: str = "default") -> List[dict]:
        """
        Get the N most recent frames.

        Args:
            n: Number of frames to retrieve
            mission_id: Mission identifier

        Returns:
            List of most recent frames (newest first)

        Teaching Note:
            This query uses cache when possible. Recent data is often
            accessed repeatedly (live dashboards), so caching provides
            significant speedup.
        """
        self.stats['queries_executed'] += 1

        # Try cache first if requesting all cached frames
        if n <= len(self.frame_cache):
            self.stats['cache_hits'] += 1
            # Return last n frames from cache (newest first)
            return list(self.frame_cache)[-n:][::-1]

        # Cache miss - query database
        self.stats['cache_misses'] += 1

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT frame_data FROM telemetry
            WHERE mission_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (mission_id, n))

        frames = []
        for row in cursor.fetchall():
            frame = json.loads(row['frame_data'])
            frames.append(frame)

        return frames

    def get_anomalies(
        self,
        severity: Optional[str] = None,
        limit: int = 100,
        mission_id: str = "default"
    ) -> List[dict]:
        """
        Get anomalies, optionally filtered by severity.

        Args:
            severity: Filter by severity ('warning', 'critical', or None for all)
            limit: Maximum number of anomalies to return
            mission_id: Mission identifier

        Returns:
            List of anomaly records with context

        Teaching Note:
            Separate anomalies table allows efficient queries without
            scanning all telemetry. This is a classic denormalization
            trade-off: duplicate data for faster queries.
        """
        self.stats['queries_executed'] += 1

        cursor = self.conn.cursor()

        if severity:
            cursor.execute("""
                SELECT a.*, t.timestamp, t.frame_id
                FROM anomalies a
                JOIN telemetry t ON a.telemetry_id = t.id
                WHERE t.mission_id = ? AND a.severity = ?
                ORDER BY a.timestamp DESC
                LIMIT ?
            """, (mission_id, severity, limit))
        else:
            cursor.execute("""
                SELECT a.*, t.timestamp, t.frame_id
                FROM anomalies a
                JOIN telemetry t ON a.telemetry_id = t.id
                WHERE t.mission_id = ?
                ORDER BY a.timestamp DESC
                LIMIT ?
            """, (mission_id, limit))

        anomalies = []
        for row in cursor.fetchall():
            anomalies.append({
                'timestamp': row['timestamp'],
                'frame_id': row['frame_id'],
                'field': row['field'],
                'type': row['anomaly_type'],
                'severity': row['severity'],
                'description': row['description'],
            })

        return anomalies

    def export_mission(
        self,
        output_path: str,
        mission_id: str = "default",
        format: str = "json"
    ):
        """
        Export entire mission to file.

        Args:
            output_path: Where to save export
            mission_id: Mission to export
            format: Export format ('json' currently supported)

        Teaching Note:
            JSON export provides:
                - Human-readable backup
                - Platform-independent format
                - Easy import to other tools
            Trade-off: Larger files than binary formats.
        """
        if format != "json":
            raise ValueError(f"Unsupported format: {format}")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT frame_data FROM telemetry
            WHERE mission_id = ?
            ORDER BY timestamp ASC
        """, (mission_id,))

        frames = []
        for row in cursor.fetchall():
            frame = json.loads(row['frame_data'])
            frames.append(frame)

        # Write to file
        with open(output_path, 'w') as f:
            json.dump({
                'mission_id': mission_id,
                'frame_count': len(frames),
                'frames': frames
            }, f, indent=2)

    def get_statistics(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage metrics

        Teaching Note:
            Monitoring storage metrics helps identify:
                - Performance bottlenecks (low cache hit rate)
                - Disk usage (total bytes written)
                - System health (frames stored per second)
        """
        # Get database size
        db_size_bytes = 0
        if os.path.exists(self.db_path):
            db_size_bytes = os.path.getsize(self.db_path)

        # Calculate cache hit rate
        total_cache_queries = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = 0.0
        if total_cache_queries > 0:
            cache_hit_rate = self.stats['cache_hits'] / total_cache_queries

        return {
            'frames_stored': self.stats['frames_stored'],
            'total_bytes_written': self.stats['total_bytes_written'],
            'queries_executed': self.stats['queries_executed'],
            'cache_hit_rate': cache_hit_rate,
            'db_size_bytes': db_size_bytes,
            'db_size_mb': db_size_bytes / (1024 * 1024),
        }

    def close(self):
        """
        Close database connection.

        Teaching Note:
            Always close connections when done. SQLite handles crashes
            gracefully, but explicit close is cleaner and releases locks.
        """
        self.conn.close()


# ═══════════════════════════════════════════════════════════════
# DEBUGGING AND TESTING HELPERS
# ═══════════════════════════════════════════════════════════════

def test_storage():
    """
    Test function to demonstrate storage usage.

    Shows:
        1. Storing frames
        2. Querying by time range
        3. Getting latest frames
        4. Querying anomalies
        5. Statistics tracking
    """
    print("Testing MissionStorage...")
    print()

    # Create temporary storage
    import tempfile
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_mission.db")

    storage = MissionStorage(db_path, cache_size=5)

    # Test Case 1: Store normal frames
    print("Test 1: Storing frames...")
    for i in range(10):
        frame = {
            'timestamp': float(i),
            'frame_id': i,
            'data': {
                'battery_soc': 75.0 - (i * 0.5),
                'battery_temp': 20.0 + (i * 0.1),
            },
            'metadata': {
                'quality': 'high',
                'anomalies': []
            }
        }
        storage.store_frame(frame, mission_id="test_mission")
    print(f"  Stored 10 frames")
    print()

    # Test Case 2: Store frame with anomaly
    print("Test 2: Storing frame with anomaly...")
    anomaly_frame = {
        'timestamp': 10.0,
        'frame_id': 10,
        'data': {
            'battery_soc': 10.0,  # Critical low
            'battery_temp': 20.0,
        },
        'metadata': {
            'quality': 'medium',
            'anomalies': [{
                'field': 'battery_soc',
                'value': 10.0,
                'type': 'threshold',
                'severity': 'critical',
                'description': 'Battery critically low'
            }]
        }
    }
    storage.store_frame(anomaly_frame, mission_id="test_mission")
    print("  Stored frame with anomaly")
    print()

    # Test Case 3: Query time range
    print("Test 3: Query frames 0-5 seconds...")
    frames = storage.query_frames(0.0, 5.0, mission_id="test_mission")
    print(f"  Found {len(frames)} frames")
    print()

    # Test Case 4: Get latest frames
    print("Test 4: Get 3 latest frames...")
    latest = storage.get_latest(3, mission_id="test_mission")
    print(f"  Found {len(latest)} frames")
    for frame in latest:
        print(f"    Frame {frame['frame_id']}: t={frame['timestamp']}")
    print()

    # Test Case 5: Query anomalies
    print("Test 5: Query critical anomalies...")
    anomalies = storage.get_anomalies(severity='critical', mission_id="test_mission")
    print(f"  Found {len(anomalies)} critical anomalies")
    for anomaly in anomalies:
        print(f"    {anomaly['description']}")
    print()

    # Test Case 6: Export mission
    print("Test 6: Export mission to JSON...")
    export_path = os.path.join(temp_dir, "mission_export.json")
    storage.export_mission(export_path, mission_id="test_mission")
    print(f"  Exported to {export_path}")
    print()

    # Show statistics
    stats = storage.get_statistics()
    print("Storage Statistics:")
    for key, value in stats.items():
        if 'bytes' in key or 'mb' in key:
            print(f"  {key}: {value:,.0f}")
        elif 'rate' in key:
            print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")
    print()

    # Cleanup
    storage.close()
    print("Storage test complete!")


if __name__ == "__main__":
    test_storage()
