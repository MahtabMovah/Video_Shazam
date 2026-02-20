# Video Shazam

A Shazam-style video fingerprinting and retrieval system. Given a short video/audio clip, it identifies which video in your reference library the clip came from and at what timestamp — then plays it from that point.

## How It Works

1. **Fingerprinting** — Each reference video's audio is converted to a per-second *amplitude envelope*: the peak absolute amplitude of every one-second chunk, rounded to one decimal place.
2. **Matching** — The query clip's envelope is slid over each reference envelope. The position and video with the minimum L1 distance wins.
3. **Playback** — A VLC-backed Qt player opens the matched video at the detected timestamp.

This is intentionally lightweight. For production use, consider MFCC-based or spectrogram hashing approaches (e.g. the Shazam constellation algorithm).

---

## Project Structure

```
video_shazam/
├── main.py             # CLI entry point
├── fingerprinter.py    # Fingerprint extraction and matching logic
├── reference_store.py  # Load/save fingerprints to/from disk (JSON)
├── player.py           # PyQt5 + VLC video player
├── requirements.txt
└── fingerprints/       # Auto-created by build-index
    ├── video1.json
    ├── video2.json
    └── ...
```

---

## Setup

```bash
pip install -r requirements.txt
```

Make sure VLC is installed on your system:
- **Linux**: `sudo apt install vlc`
- **macOS**: download from [videolan.org](https://www.videolan.org)
- **Windows**: download from [videolan.org](https://www.videolan.org)

---

## Usage

### Step 1 — Build the fingerprint index (one-time setup)

Place your reference audio files (`video1.wav`, `video2.wav`, …) in a directory and run:

```bash
python main.py build-index reference_audio/ --count 20
```

This writes `fingerprints/video1.json`, `fingerprints/video2.json`, … to disk. You only need to re-run this if your reference library changes.

### Step 2 — Query

```bash
python main.py query_clip.mp4 query_clip.wav
```

The system will print the matched video and timestamp, then open the player at that position:

```
Loaded 20 reference fingerprints.
Extracting query fingerprint from 'query_clip.wav'…
Query length: 8 second(s).

— Match found —
  Video   : video3.mp4
  Frame   : 142s
  L1 cost : 1.40
```

---

## Limitations

- **Amplitude-envelope fingerprinting** is simple and fast but fragile under noise, pitch shifts, or heavy compression. For a production system, use a spectrogram-based approach.
- **Minimum query length**: very short clips (< 3–4 seconds) may produce false matches.
- Reference videos must be named `video1.mp4` … `video<N>.mp4` and reside in the working directory (or adjust paths in `main.py`).

---

## Requirements

See `requirements.txt`. Key dependencies:

| Package | Purpose |
|---------|---------|
| `librosa` | Audio loading and processing |
| `numpy` | Array operations |
| `PyQt5` | GUI framework |
| `python-vlc` | VLC bindings for video playback |
