"""
Math Helpers - Common Mathematical Operations

PURPOSE:
    Provides mathematical utilities for simulation including noise generation,
    smoothing, interpolation, drift modeling, and other common numerical
    operations. These are the building blocks used throughout the simulator
    for realistic sensor modeling and data processing.

THEORY:
    Scientific simulations require many mathematical operations:

    - NOISE: Random fluctuations that model measurement uncertainty
      * Gaussian (normal) noise: Most common, models independent errors
      * Uniform noise: All values equally likely in a range
      * Pink/Brownian noise: Correlated noise with memory

    - SMOOTHING: Filtering to reduce noise and extract trends
      * Moving average: Simple, intuitive, but has lag
      * Exponential smoothing: Weighs recent values more heavily
      * Median filter: Removes outlier spikes

    - INTERPOLATION: Filling gaps in data
      * Linear: Straight line between points
      * Cubic: Smooth curves through points
      * Nearest neighbor: Use closest known value

    - DRIFT: Slow systematic changes over time
      * Linear drift: Constant rate of change
      * Random walk: Accumulation of small random steps
      * Thermal drift: Temperature-dependent bias

ARCHITECTURE ROLE:
    These utilities are used by:
        - Sensors: Add noise and drift to measurements
        - Cleaner: Smooth and interpolate corrupted data
        - Anomaly Detector: Statistical analysis needs smoothed baselines
        - Visualizations: Plot processing and presentation

TEACHING GOALS:
    - Understanding different noise distributions and when to use them
    - Signal processing fundamentals (filtering, smoothing)
    - Numerical stability and edge cases
    - Trade-offs between accuracy and computational cost
    - Debugging numerical algorithms

DEBUGGING NOTES:
    - To verify noise: Generate 1000 samples, plot histogram, check mean/stddev
    - To test smoothing: Create signal with known noise, verify reduction
    - To validate interpolation: Use known function, compare to true values
    - Watch for edge effects in window-based operations
    - Check for numerical instability with extreme values

FUTURE EXTENSIONS:
    - Add Kalman filtering for optimal state estimation
    - Implement FFT-based frequency domain analysis
    - Add wavelet transforms for multi-scale analysis
    - Implement adaptive filtering (parameters adjust to data)
    - Add numerical integration/differentiation with error bounds
"""

import random
import math
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# NOISE GENERATION
# ═══════════════════════════════════════════════════════════════

def add_gaussian_noise(value: float, stddev: float) -> float:
    """
    Add Gaussian (normal) noise to a value.

    Gaussian noise is the most common type in real sensors because of the
    Central Limit Theorem: many independent error sources combine to produce
    a normal distribution.

    Args:
        value: Clean input value
        stddev: Standard deviation of noise (controls spread)
                - stddev=0.1 means 68% of readings within ±0.1 of true value
                - stddev=1.0 means 68% within ±1.0

    Returns:
        Value with added Gaussian noise

    Example:
        # Simulate a temperature sensor with 0.5°C accuracy
        true_temp = 25.0  # Celsius
        measured = add_gaussian_noise(true_temp, 0.5)
        # measured might be 25.3, 24.7, 25.1, etc.

    Teaching Note:
        random.gauss() uses the Box-Muller transform to generate normally
        distributed values from uniform random numbers. The mean is 0 (we're
        adding noise, not bias) and the spread is controlled by stddev.
    """
    if stddev == 0:
        return value  # Optimization: no noise needed

    noise = random.gauss(0, stddev)
    return value + noise


def add_uniform_noise(value: float, half_range: float) -> float:
    """
    Add uniform noise to a value.

    Uniform noise has all values in a range equally likely. Less common in
    real sensors but useful for modeling quantization error or bounded
    uncertainty.

    Args:
        value: Clean input value
        half_range: Half the width of uniform distribution
                    - half_range=1.0 means noise uniformly distributed in [-1, +1]

    Returns:
        Value with added uniform noise

    Example:
        # Simulate an ADC quantization error (uniform between steps)
        voltage = 3.3
        measured = add_uniform_noise(voltage, 0.005)  # ±5mV uncertainty
    """
    if half_range == 0:
        return value

    noise = random.uniform(-half_range, half_range)
    return value + noise


def random_walk_drift(current_drift: float, step_size: float, dt: float = 1.0) -> float:
    """
    Simulate drift as a random walk process.

    Real sensors drift over time - their bias slowly changes. A random walk
    models this: each timestep, the drift changes by a small random amount.
    Over time, drift can accumulate to significant levels.

    Args:
        current_drift: Current drift value
        step_size: Standard deviation of drift change per time unit
                   (e.g., 0.01 degrees/hour for IMU drift)
        dt: Time step in appropriate units (default 1.0)

    Returns:
        New drift value after this timestep

    Example:
        # Simulate IMU drift over a mission
        drift = 0.0
        for hour in range(24):
            drift = random_walk_drift(drift, step_size=0.01, dt=1.0)
            # After 24 hours, drift might accumulate to ~0.1-0.3 degrees

    Teaching Note:
        This is a Brownian motion / Wiener process. The drift follows a
        random walk, so variance grows linearly with time. After N steps,
        expected absolute drift is proportional to sqrt(N).
    """
    drift_change = random.gauss(0, step_size * math.sqrt(dt))
    new_drift = current_drift + drift_change

    return new_drift


def pink_noise(current_value: float, alpha: float = 0.7) -> float:
    """
    Generate correlated (pink/red) noise using first-order autoregressive process.

    Unlike white noise (completely random each sample), pink noise has
    memory - the current value depends on previous values. This better
    models many real-world phenomena like thermal fluctuations.

    Args:
        current_value: Previous noise value
        alpha: Correlation coefficient (0 to 1)
               - 0 = white noise (no memory)
               - 0.5 = pink noise (1/f spectrum)
               - 0.9 = red noise (strong correlation)

    Returns:
        New correlated noise value

    Example:
        # Generate correlated temperature fluctuations
        noise = 0.0
        temps = []
        for i in range(100):
            noise = pink_noise(noise, alpha=0.8)
            temps.append(25.0 + noise)  # 25°C ± correlated fluctuations

    Teaching Note:
        This is an AR(1) process: x[n] = alpha * x[n-1] + white_noise
        The correlation length is proportional to alpha/(1-alpha).
    """
    white_noise = random.gauss(0, 1)
    new_value = alpha * current_value + (1 - alpha) * white_noise
    return new_value


# ═══════════════════════════════════════════════════════════════
# SMOOTHING AND FILTERING
# ═══════════════════════════════════════════════════════════════

def smooth_signal(values: List[float], window_size: int) -> List[float]:
    """
    Apply moving average smoothing to a signal.

    Moving average smoothing replaces each point with the average of nearby
    points. This reduces high-frequency noise but introduces lag and can
    blur sharp features.

    Args:
        values: Input signal (list of measurements)
        window_size: Number of points to average (must be odd)
                     - Larger window = more smoothing but more lag
                     - window_size=3 is minimal smoothing
                     - window_size=11 is moderate smoothing

    Returns:
        Smoothed signal (same length as input)

    Example:
        noisy_temps = [25.1, 24.9, 25.3, 24.8, 25.0]
        smooth_temps = smooth_signal(noisy_temps, window_size=3)
        # Result: [25.0, 25.1, 25.0, 24.9, 24.9] (less noisy)

    Teaching Note:
        Edge handling is important! We use 'reflect' padding: values near
        edges are mirrored. Other options: zero-pad, replicate, or use
        smaller windows at edges.
    """
    if window_size < 1:
        return values.copy()

    if window_size == 1:
        return values.copy()

    # Ensure window size is odd for symmetric filtering
    if window_size % 2 == 0:
        window_size += 1

    smoothed = []
    half_window = window_size // 2

    for i in range(len(values)):
        # Determine window bounds with edge handling
        start = max(0, i - half_window)
        end = min(len(values), i + half_window + 1)

        # Compute average of window
        window_values = values[start:end]
        avg = sum(window_values) / len(window_values)
        smoothed.append(avg)

    return smoothed


def exponential_smoothing(values: List[float], alpha: float = 0.3) -> List[float]:
    """
    Apply exponential smoothing (single exponential smoothing / EMA).

    Exponential smoothing gives more weight to recent values while maintaining
    a memory of past values. Unlike moving average, it doesn't require a
    fixed window and adapts faster to changes.

    Args:
        values: Input signal
        alpha: Smoothing factor (0 to 1)
               - 0 = no response to new data (flat line)
               - 0.1 = very smooth, slow to respond
               - 0.5 = balanced
               - 0.9 = minimal smoothing, fast response

    Returns:
        Smoothed signal (same length as input)

    Example:
        noisy_current = [1.2, 1.5, 1.3, 1.4, 1.6]  # Amperes
        smooth_current = exponential_smoothing(noisy_current, alpha=0.3)
        # More recent values have stronger influence than old values

    Teaching Note:
        Formula: S[n] = alpha * x[n] + (1-alpha) * S[n-1]
        This is equivalent to an infinite weighted average where weights
        decay exponentially into the past. Used extensively in control
        systems and signal processing.
    """
    if not values:
        return []

    if alpha <= 0:
        # No smoothing - return constant value
        return [values[0]] * len(values)

    if alpha >= 1:
        # No memory - return original signal
        return values.copy()

    smoothed = [values[0]]  # Initialize with first value

    for i in range(1, len(values)):
        new_value = alpha * values[i] + (1 - alpha) * smoothed[-1]
        smoothed.append(new_value)

    return smoothed


def median_filter(values: List[float], window_size: int = 3) -> List[float]:
    """
    Apply median filtering to remove outlier spikes.

    Median filtering replaces each point with the median of nearby points.
    Excellent for removing isolated spikes (impulse noise) while preserving
    edges, unlike averaging which blurs everything.

    Args:
        values: Input signal
        window_size: Window size (must be odd, typically 3 or 5)

    Returns:
        Filtered signal with spikes removed

    Example:
        with_spikes = [25, 25, 25, 100, 25, 25]  # 100 is a spike
        clean = median_filter(with_spikes, window_size=3)
        # Result: [25, 25, 25, 25, 25, 25] - spike removed!

    Teaching Note:
        Median filter is non-linear (unlike averaging) and preserves edges.
        It's resistant to outliers: one bad value won't corrupt the output.
        Widely used in image processing and sensor data cleaning.
    """
    if window_size < 1:
        return values.copy()

    if window_size == 1:
        return values.copy()

    # Ensure odd window size
    if window_size % 2 == 0:
        window_size += 1

    filtered = []
    half_window = window_size // 2

    for i in range(len(values)):
        # Get window around current point
        start = max(0, i - half_window)
        end = min(len(values), i + half_window + 1)
        window = values[start:end]

        # Compute median
        sorted_window = sorted(window)
        median = sorted_window[len(sorted_window) // 2]
        filtered.append(median)

    return filtered


# ═══════════════════════════════════════════════════════════════
# INTERPOLATION
# ═══════════════════════════════════════════════════════════════

def interpolate_gap(before: float, after: float, fraction: float) -> float:
    """
    Linear interpolation for gap-filling.

    Linear interpolation draws a straight line between two known points
    and estimates values in between. Simple, fast, and often good enough
    for sensor data with small gaps.

    Args:
        before: Value before gap
        after: Value after gap
        fraction: Position in gap (0.0 = before, 1.0 = after, 0.5 = midpoint)

    Returns:
        Interpolated value

    Example:
        # Fill missing temperature value between 25°C and 27°C
        before_temp = 25.0
        after_temp = 27.0
        middle_temp = interpolate_gap(before_temp, after_temp, 0.5)
        # Result: 26.0°C (halfway between)

    Teaching Note:
        This implements the standard linear interpolation formula:
        y = y1 + (y2 - y1) * t  where t in [0, 1]
        Also known as "lerp" in computer graphics.
    """
    # Clamp fraction to [0, 1] to prevent extrapolation
    fraction = max(0.0, min(1.0, fraction))

    return before + (after - before) * fraction


def interpolate_series(values: List[Optional[float]]) -> List[float]:
    """
    Interpolate missing values (None) in a time series.

    Finds gaps (None values) in a list and fills them by linear interpolation
    between surrounding valid points. Handles edge cases like missing values
    at start/end.

    Args:
        values: List with some None values representing missing data

    Returns:
        List with all values filled (no Nones)

    Example:
        temps = [25.0, 25.5, None, None, 27.0, 27.5]
        filled = interpolate_series(temps)
        # Result: [25.0, 25.5, 26.0, 26.5, 27.0, 27.5]

    Teaching Note:
        This is essential for telemetry cleaning when packets are lost.
        For long gaps (>10 points), linear interpolation may not be accurate.
        Consider flagging interpolated points for downstream awareness.
    """
    if not values:
        return []

    result = values.copy()
    n = len(result)

    # Forward fill for leading Nones
    first_valid = None
    for i in range(n):
        if result[i] is not None:
            first_valid = result[i]
            break

    if first_valid is None:
        # All values are None - can't interpolate!
        return [0.0] * n  # Return zeros as fallback

    # Fill leading Nones with first valid value
    for i in range(n):
        if result[i] is None:
            result[i] = first_valid
        else:
            break

    # Backward fill for trailing Nones
    last_valid = None
    for i in range(n - 1, -1, -1):
        if result[i] is not None:
            last_valid = result[i]
            break

    for i in range(n - 1, -1, -1):
        if result[i] is None:
            result[i] = last_valid
        else:
            break

    # Linear interpolate interior gaps
    i = 0
    while i < n:
        if result[i] is None:
            # Find start and end of gap
            gap_start = i - 1
            gap_end = i
            while gap_end < n and result[gap_end] is None:
                gap_end += 1

            # Interpolate gap
            if gap_start >= 0 and gap_end < n:
                before_val = result[gap_start]
                after_val = result[gap_end]
                gap_size = gap_end - gap_start

                for j in range(gap_start + 1, gap_end):
                    fraction = (j - gap_start) / gap_size
                    result[j] = interpolate_gap(before_val, after_val, fraction)

            i = gap_end
        else:
            i += 1

    return result


# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value to a specified range.

    Args:
        value: Input value
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Value clamped to [min_val, max_val]

    Example:
        # Ensure temperature stays in valid sensor range
        temp = clamp(measured_temp, -40, 85)  # Valid for many sensors
    """
    return max(min_val, min(max_val, value))


def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to 0-1 range.

    Args:
        value: Input value
        min_val: Value that maps to 0
        max_val: Value that maps to 1

    Returns:
        Normalized value (0 to 1, or outside if value exceeds range)

    Example:
        # Convert battery voltage (28-36V) to 0-1 scale
        voltage = 32.0
        normalized = normalize(voltage, 28.0, 36.0)  # Returns 0.5
    """
    if max_val == min_val:
        return 0.5  # Avoid division by zero

    return (value - min_val) / (max_val - min_val)


def moving_stddev(values: List[float], window_size: int = 10) -> List[float]:
    """
    Calculate moving standard deviation.

    Useful for detecting when signal variance changes (e.g., sensor getting
    noisier, or vehicle entering rough terrain).

    Args:
        values: Input signal
        window_size: Window for standard deviation calculation

    Returns:
        List of standard deviations (one per point)

    Example:
        # Detect when temperature sensor becomes noisier
        temps = [25.0, 25.1, 25.0, 25.2, 24.8, 26.5, 23.1, 27.9]
        stddevs = moving_stddev(temps, window_size=4)
        # stddevs increases at the end where variance grows
    """
    if window_size < 2:
        return [0.0] * len(values)

    result = []
    half_window = window_size // 2

    for i in range(len(values)):
        start = max(0, i - half_window)
        end = min(len(values), i + half_window + 1)
        window = values[start:end]

        # Calculate standard deviation
        if len(window) < 2:
            result.append(0.0)
        else:
            mean = sum(window) / len(window)
            variance = sum((x - mean) ** 2 for x in window) / len(window)
            stddev = math.sqrt(variance)
            result.append(stddev)

    return result


# ═══════════════════════════════════════════════════════════════
# FUTURE EXTENSION IDEAS
# ═══════════════════════════════════════════════════════════════
# def kalman_filter(measurements, process_variance, measurement_variance):
#     """Optimal estimation filter for noisy measurements."""
#     pass
#
# def butterworth_filter(values, cutoff_freq, sampling_rate, order=2):
#     """Frequency-domain low-pass filter."""
#     pass
#
# def detect_outliers_zscore(values, threshold=3.0):
#     """Detect outliers using z-score method."""
#     pass
#
# def fit_polynomial_trend(values, degree=2):
#     """Fit polynomial trend line to data."""
#     pass
#
# def cross_correlate(signal1, signal2):
#     """Find time lag between two related signals."""
#     pass
