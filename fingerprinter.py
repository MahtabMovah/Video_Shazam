"""
fingerprinter.py
~~~~~~~~~~~~~~~~
Audio fingerprinting utilities for the video Shazam system.

A "fingerprint" is a per-second amplitude envelope: for every one-second
chunk of an audio file, we record the peak absolute amplitude rounded to
one decimal place.  Matching is done by sliding the query fingerprint over
each reference fingerprint and minimising the L1 distance.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

import librosa
import numpy as np


# ---------------------------------------------------------------------------
# Fingerprint extraction
# ---------------------------------------------------------------------------

def extract_fingerprint(audio_path: str | Path) -> list[float]:
    """
    Load an audio file and return its per-second amplitude envelope.

    Each element is the peak absolute amplitude within one second of audio,
    rounded to one decimal place.  The final (potentially partial) second is
    discarded so every element represents a full second.

    Parameters
    ----------
    audio_path:
        Path to a WAV (or any librosa-supported) audio file.

    Returns
    -------
    list[float]
        Per-second amplitude envelope.
    """
    y, sr = librosa.load(str(audio_path))
    chunks = [y[offset : offset + sr] for offset in range(0, len(y), sr)]
    chunks.pop()  # drop the last (partial) second
    return [round(float(np.max(np.abs(chunk))), 1) for chunk in chunks]


# ---------------------------------------------------------------------------
# Fingerprint matching
# ---------------------------------------------------------------------------

def _l1_distance(query: Sequence[float], reference: Sequence[float], offset: int) -> float:
    """Return the L1 distance between *query* and the *reference* window at *offset*."""
    return sum(abs(q - reference[offset + j]) for j, q in enumerate(query))


def best_match_position(
    query: Sequence[float],
    reference: Sequence[float],
) -> tuple[int, float]:
    """
    Slide *query* over *reference* and find the window with the smallest L1 distance.

    Parameters
    ----------
    query:
        Fingerprint of the query clip (shorter sequence).
    reference:
        Fingerprint of a reference video (longer sequence).

    Returns
    -------
    (frame_index, distance)
        *frame_index* is the second-offset into *reference* where the best
        match starts.  *distance* is the raw L1 cost (lower is better).
        Returns ``(-1, inf)`` if *query* is longer than *reference*.
    """
    max_offset = len(reference) - len(query)
    if max_offset < 0:
        return -1, math.inf

    best_offset = -1
    best_distance = math.inf

    for offset in range(max_offset + 1):
        dist = _l1_distance(query, reference, offset)
        if dist < best_distance:
            best_distance = dist
            best_offset = offset

    return best_offset, best_distance


def find_best_video(
    query: Sequence[float],
    references: Sequence[Sequence[float]],
) -> tuple[int, int, float]:
    """
    Find the reference video that best matches *query*.

    Parameters
    ----------
    query:
        Fingerprint of the query clip.
    references:
        List of per-video fingerprints (e.g. loaded from disk).

    Returns
    -------
    (video_index, frame_index, distance)
        *video_index* is the zero-based index into *references*.
        *frame_index* is the second-offset within that video.
        *distance* is the raw L1 cost.
    """
    best_video = -1
    best_frame = -1
    best_distance = math.inf

    for video_idx, ref in enumerate(references):
        frame, dist = best_match_position(query, ref)
        if dist < best_distance:
            best_distance = dist
            best_frame = frame
            best_video = video_idx

    return best_video, best_frame, best_distance
