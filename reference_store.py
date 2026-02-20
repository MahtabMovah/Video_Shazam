"""
reference_store.py
~~~~~~~~~~~~~~~~~~
Utilities for saving and loading pre-computed reference fingerprints.

Fingerprints are stored as plain JSON files — one file per video — so they
can be inspected, version-controlled, and recomputed independently of the
GUI or matching code.

Directory layout expected / produced by this module::

    fingerprints/
        video1.json
        video2.json
        ...
        video20.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


FINGERPRINT_DIR = Path("fingerprints")


def _path_for(video_index: int, directory: Path = FINGERPRINT_DIR) -> Path:
    """Return the JSON path for a 1-based *video_index*."""
    return directory / f"video{video_index}.json"


def save_fingerprint(fingerprint: list[float], video_index: int, directory: Path = FINGERPRINT_DIR) -> None:
    """
    Persist *fingerprint* to disk as JSON.

    Parameters
    ----------
    fingerprint:
        Per-second amplitude envelope produced by :func:`fingerprinter.extract_fingerprint`.
    video_index:
        1-based video number (determines the filename).
    directory:
        Directory in which to write the JSON files.  Created if absent.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = _path_for(video_index, directory)
    path.write_text(json.dumps(fingerprint, separators=(",", ":")))


def load_fingerprint(video_index: int, directory: Path = FINGERPRINT_DIR) -> list[float]:
    """
    Load a single pre-computed fingerprint from disk.

    Raises
    ------
    FileNotFoundError
        If no fingerprint has been saved for *video_index*.
    """
    path = _path_for(video_index, directory)
    return json.loads(path.read_text())


def load_all_fingerprints(directory: Path = FINGERPRINT_DIR) -> list[list[float]]:
    """
    Load every fingerprint found in *directory*, sorted by video index.

    Returns
    -------
    list[list[float]]
        Fingerprints in ascending video-index order.  Empty list if the
        directory does not exist or contains no ``*.json`` files.
    """
    if not directory.exists():
        return []

    def _index(p: Path) -> int:
        # Expect filenames like "video3.json"
        return int("".join(filter(str.isdigit, p.stem)) or -1)

    paths = sorted(directory.glob("video*.json"), key=_index)
    return [json.loads(p.read_text()) for p in paths]


def iter_video_paths(
    video_dir: Path,
    count: int,
    extension: str = ".mp4",
) -> Iterator[tuple[int, Path]]:
    """
    Yield ``(1-based index, path)`` pairs for the reference video files.

    Parameters
    ----------
    video_dir:
        Directory containing ``video1.mp4``, ``video2.mp4`` …
    count:
        Total number of videos expected.
    extension:
        File extension (default ``.mp4``).
    """
    for i in range(1, count + 1):
        yield i, video_dir / f"video{i}{extension}"
