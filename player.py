"""
player.py
~~~~~~~~~
PyQt5 video player widget used to display the matched video.

The player opens the matched video at the detected start time and provides
standard playback controls (play/pause, seek, volume, reset).
"""

from __future__ import annotations

import os
import platform
import sys

import vlc
from PyQt5 import QtCore, QtGui, QtWidgets


class Player(QtWidgets.QMainWindow):
    """
    A minimal VLC-backed video player embedded in a Qt window.

    Parameters
    ----------
    video_path:
        Absolute or relative path to the video file to open.
    start_second:
        Second offset at which to begin playback.
    parent:
        Optional Qt parent widget.
    """

    def __init__(
        self,
        video_path: str,
        start_second: int = 0,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Video Shazam — Match Player")

        self._video_path = video_path
        self._start_second = start_second
        self._is_paused = True

        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()

        self._build_ui()
        self._load_media(video_path, start_second)
        self._attach_window()

        # Immediately pause so the user sees the match frame first
        self._player.play()
        self.play_pause()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create and arrange all widgets."""
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)

        # Video surface
        if platform.system() == "Darwin":
            self._video_frame = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self._video_frame = QtWidgets.QFrame()

        palette = self._video_frame.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self._video_frame.setPalette(palette)
        self._video_frame.setAutoFillBackground(True)

        # Seek slider
        self._seek_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self._seek_slider.setToolTip("Seek")
        self._seek_slider.setMaximum(1000)
        self._seek_slider.sliderMoved.connect(self._on_seek)
        self._seek_slider.sliderPressed.connect(self._on_seek)

        # Buttons
        self._play_btn = QtWidgets.QPushButton("Play")
        self._play_btn.clicked.connect(self.play_pause)

        reset_btn = QtWidgets.QPushButton("Reset to Match")
        reset_btn.clicked.connect(self.reset_to_match)

        # Volume slider
        self._volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self._volume_slider.setMaximum(100)
        self._volume_slider.setValue(self._player.audio_get_volume())
        self._volume_slider.setToolTip("Volume")
        self._volume_slider.valueChanged.connect(
            lambda v: self._player.audio_set_volume(v)
        )

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self._play_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(QtWidgets.QLabel("Volume:"))
        btn_row.addWidget(self._volume_slider)

        layout = QtWidgets.QVBoxLayout(central)
        layout.addWidget(self._video_frame)
        layout.addWidget(self._seek_slider)
        layout.addLayout(btn_row)

        # Menu bar
        file_menu = self.menuBar().addMenu("File")
        open_action = QtWidgets.QAction("Open File…", self)
        quit_action = QtWidgets.QAction("Quit", self)
        open_action.triggered.connect(self._on_open_file)
        quit_action.triggered.connect(sys.exit)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        # Refresh timer (100 ms)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._update_ui)

    def _load_media(self, path: str, start_second: int) -> None:
        """Load *path* into the player, starting at *start_second*."""
        self._match_media = self._instance.media_new(path)
        self._match_media.add_option(f"start-time={start_second}")
        self._player.set_media(self._match_media)

        self._reset_media = self._instance.media_new(path)
        self._reset_media.add_option("start-time=0")

    def _attach_window(self) -> None:
        """Bind the player to the Qt video surface (platform-specific)."""
        wid = int(self._video_frame.winId())
        system = platform.system()
        if system == "Linux":
            self._player.set_xwindow(wid)
        elif system == "Windows":
            self._player.set_hwnd(wid)
        elif system == "Darwin":
            self._player.set_nsobject(wid)

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def play_pause(self) -> None:
        """Toggle between play and pause."""
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("Play")
            self._is_paused = True
            self._timer.stop()
        else:
            if self._player.play() == -1:
                self._on_open_file()
                return
            self._player.play()
            self._play_btn.setText("Pause")
            self._is_paused = False
            self._timer.start()

    def reset_to_match(self) -> None:
        """Stop playback and restart from the detected match position."""
        self._player.stop()
        self._player.set_media(self._match_media)
        self._player.play()
        self._play_btn.setText("Pause")
        self._is_paused = False
        self._timer.start()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_seek(self) -> None:
        self._timer.stop()
        self._player.set_position(self._seek_slider.value() / 1000.0)
        self._timer.start()

    def _on_open_file(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Media File", os.path.expanduser("~")
        )
        if not filename:
            return
        media = self._instance.media_new(filename)
        self._player.set_media(media)
        media.parse()
        self.setWindowTitle(media.get_meta(0) or filename)
        self._attach_window()
        self.play_pause()

    def _update_ui(self) -> None:
        """Sync the seek slider with the current playback position."""
        pos = int(self._player.get_position() * 1000)
        self._seek_slider.setValue(pos)

        if not self._player.is_playing():
            self._timer.stop()
            if not self._is_paused:
                self.reset_to_match()
