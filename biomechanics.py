import numpy as np
from scipy.signal import find_peaks

def calculate_angle(a, b, c):
    a, b, c = map(lambda p: np.asarray(p, dtype=float), (a, b, c))
    ba = a - b
    bc = c - b
    na, nc = np.linalg.norm(ba), np.linalg.norm(bc)
    if na == 0 or nc == 0:
        return np.nan
    cosine = np.clip(np.dot(ba, bc) / (na * nc), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))

def interpolate_nan(signal):
    signal = np.asarray(signal, dtype=float).copy()
    valid = ~np.isnan(signal)
    if valid.sum() < 2:
        return signal
    idx = np.arange(len(signal))
    signal[~valid] = np.interp(idx[~valid], idx[valid], signal[valid])
    return signal

def smooth_signal(signal, window=7):
    signal = np.asarray(signal, dtype=float)
    if len(signal) < window:
        return signal.copy()
    if window % 2 == 0:
        window += 1
    kernel = np.ones(window) / window
    return np.convolve(signal, kernel, mode="same")

def detect_squat_repetitions(angles, times, flexion_threshold=120, min_distance_seconds=0.8):
    angles = np.asarray(angles, dtype=float)
    times = np.asarray(times, dtype=float)
    valid = ~np.isnan(angles)
    if valid.sum() < 10:
        return []
    clean = smooth_signal(interpolate_nan(angles), 7)
    dt = np.median(np.diff(times)) if len(times) > 1 else 1/30
    if not np.isfinite(dt) or dt <= 0:
        dt = 1/30
    distance = max(1, int(min_distance_seconds / dt))
    minima, _ = find_peaks(-clean, distance=distance, prominence=5)
    return [
        {"index": int(i), "time": float(times[i]), "minimum_angle": float(clean[i])}
        for i in minima if clean[i] <= flexion_threshold
    ]

def calculate_summary(angles, times, repetitions=None):
    angles, times = np.asarray(angles, dtype=float), np.asarray(times, dtype=float)
    valid = ~np.isnan(angles)
    if not valid.any():
        return None
    va, vt = angles[valid], times[valid]
    i = int(np.argmin(va))
    return {
        "minimum_angle": float(va[i]),
        "maximum_angle": float(np.max(va)),
        "time_at_minimum": float(vt[i]),
        "duration": float(vt[-1] - vt[0]),
        "repetitions": len(repetitions or []),
    }
