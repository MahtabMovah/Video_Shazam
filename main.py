"""
main.py
~~~~~~~
Entry point for the Video Shazam system.

Usage
-----
Match a query clip against the pre-built fingerprint database::

    python main.py <query_video> <query_audio>

Build (or rebuild) the reference fingerprint database from the reference
audio files::

    python main.py --build-index <audio_dir> [--count 20]

Examples
--------
::

    # First time: index the reference videos' audio
    python main.py --build-index reference_audio/ --count 20

    # Every subsequent query
    python main.py query_clip.mp4 query_clip.wav
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fingerprinter import extract_fingerprint, find_best_video
from reference_store import (
    FINGERPRINT_DIR,
    load_all_fingerprints,
    save_fingerprint,
    iter_video_paths,
)


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def build_index(audio_dir: Path, count: int) -> None:
    """
    Extract and persist fingerprints for all reference audio files.

    Expected filenames: ``video1.wav``, ``video2.wav``, … ``video<count>.wav``

    Parameters
    ----------
    audio_dir:
        Directory containing the reference audio files.
    count:
        Number of reference videos to index.
    """
    print(f"Building fingerprint index from {audio_dir!s} ({count} videos)…")
    for idx, audio_path in iter_video_paths(audio_dir, count, extension=".wav"):
        if not audio_path.exists():
            print(f"  [SKIP] {audio_path} not found.")
            continue
        print(f"  Indexing video {idx}: {audio_path.name}", end="", flush=True)
        fingerprint = extract_fingerprint(audio_path)
        save_fingerprint(fingerprint, idx)
        print(f"  ({len(fingerprint)} seconds)")
    print(f"Done. Fingerprints saved to '{FINGERPRINT_DIR}/'.")


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def run_query(query_audio: Path, query_video: Path) -> None:
    """
    Match *query_audio* against the reference database and launch the player.

    Parameters
    ----------
    query_audio:
        Path to the query audio clip (WAV).
    query_video:
        Path to the query video clip (used only to determine the video
        extension; the *matched* reference video is what gets played).
    """
    # Load reference fingerprints
    references = load_all_fingerprints()
    if not references:
        sys.exit(
            f"No fingerprints found in '{FINGERPRINT_DIR}/'. "
            "Run with --build-index first."
        )

    print(f"Loaded {len(references)} reference fingerprints.")
    print(f"Extracting query fingerprint from '{query_audio}'…")
    query_fp = extract_fingerprint(query_audio)
    print(f"Query length: {len(query_fp)} second(s).")

    video_idx, frame, distance = find_best_video(query_fp, references)
    video_number = video_idx + 1  # convert to 1-based

    print(f"\n— Match found —")
    print(f"  Video   : video{video_number}.mp4")
    print(f"  Frame   : {frame}s")
    print(f"  L1 cost : {distance:.2f}")

    _launch_player(f"video{video_number}.mp4", start_second=frame)


def _launch_player(video_path: str, start_second: int) -> None:
    """Start the Qt application and open the player at *start_second*."""
    # Import here so the rest of the CLI works without a display server
    from PyQt5 import QtWidgets
    from player import Player

    app = QtWidgets.QApplication(sys.argv)
    window = Player(video_path, start_second=start_second)
    window.show()
    window.resize(800, 600)
    sys.exit(app.exec_())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Video Shazam — match a short video/audio clip to a reference library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    # ── build-index sub-command ─────────────────────────────────────────────
    build_parser = subparsers.add_parser(
        "build-index",
        help="Extract and save fingerprints for all reference audio files.",
    )
    build_parser.add_argument(
        "audio_dir",
        type=Path,
        help="Directory containing reference WAV files (video1.wav, video2.wav, …).",
    )
    build_parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of reference videos (default: 20).",
    )

    # ── query (positional) ─────────────────────────────────────────────────
    parser.add_argument(
        "query_video",
        nargs="?",
        type=Path,
        help="Query video clip (e.g. query_clip.mp4).",
    )
    parser.add_argument(
        "query_audio",
        nargs="?",
        type=Path,
        help="Query audio clip extracted from the video (WAV).",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.command == "build-index":
        build_index(args.audio_dir, args.count)
        return

    # Default: query mode
    if args.query_video is None or args.query_audio is None:
        # Try to auto-detect a WAV in argv (legacy invocation compatibility)
        wav_args = [Path(a) for a in sys.argv[1:] if a.lower().endswith(".wav")]
        if wav_args:
            run_query(query_audio=wav_args[0], query_video=wav_args[0])
        else:
            print("Usage: python main.py <query_video> <query_audio>", file=sys.stderr)
            print("       python main.py build-index <audio_dir>", file=sys.stderr)
            sys.exit(1)
    else:
        run_query(query_audio=args.query_audio, query_video=args.query_video)


if __name__ == "__main__":
    main()
