import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QLabel,
    QSlider,
    QProgressBar
)
from PyQt6.QtGui import QShortcut
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

STATE_FILE = os.path.join(os.path.expanduser("~"), ".video_tracker_state.json")

def format_time(ms: int) -> str:
    """Format milliseconds into ss, mm:ss, or hh:mm:ss."""
    total_secs = ms // 1000
    h = total_secs // 3600
    m = (total_secs % 3600) // 60
    s = total_secs % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    elif m > 0:
        return f"{m:02d}:{s:02d}"
    else:
        return f"{s:02d}"

class SeekSlider(QSlider):
    """Slider that jumps to click position using provided player reference."""
    def __init__(self, player, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.player = player
        self.setTracking(False)

    def mousePressEvent(self, event):
        if self.maximum() > self.minimum():
            relative_x = event.pos().x()
            new_val = self.minimum() + (self.maximum() - self.minimum()) * relative_x / self.width()
            self.player.setPosition(int(new_val))
        super().mousePressEvent(event)

class VideoTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rust Course Video Tracker")
        self.resize(1000, 600)

        # Load persisted state
        self.state = {"folder": "", "watched": {} }
        self._load_state()

        # Main layout
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)

        # List pane
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.play_selected)
        self.list_widget.itemChanged.connect(self._update_summary)
        self.main_layout.addWidget(self.list_widget, 2)

        # Video pane
        self.video_container = QWidget()
        video_layout = QVBoxLayout(self.video_container)
        self.main_layout.addWidget(self.video_container, 5)

        # Video widget
        self.video_widget = QVideoWidget()
        video_layout.addWidget(self.video_widget, 1)

        # Media player
        self.player = QMediaPlayer()
        self.audio_out = QAudioOutput()
        self.player.setAudioOutput(self.audio_out)
        self.player.setVideoOutput(self.video_widget)

        # Seek slider with click-to-jump
        self.slider = SeekSlider(self.player)
        self.slider.sliderMoved.connect(lambda pos: self.player.setPosition(pos))
        video_layout.addWidget(self.slider, 0)

        # Controls
        ctrl = QHBoxLayout()
        btn_open = QPushButton("Open Folder")
        btn_open.clicked.connect(self._open_folder)
        ctrl.addWidget(btn_open)
        btn_toggle = QPushButton("Hide List")
        btn_toggle.clicked.connect(self._toggle_list)
        ctrl.addWidget(btn_toggle)
        btn_play = QPushButton("Play")
        btn_play.clicked.connect(self.player.play)
        ctrl.addWidget(btn_play)
        btn_pause = QPushButton("Pause")
        btn_pause.clicked.connect(self.player.pause)
        ctrl.addWidget(btn_pause)
        btn_stop = QPushButton("Stop")
        btn_stop.clicked.connect(self.player.stop)
        ctrl.addWidget(btn_stop)
        btn_back = QPushButton("<10s")
        btn_back.clicked.connect(lambda: self._skip(-10000))
        ctrl.addWidget(btn_back)
        btn_fwd = QPushButton("10s>")
        btn_fwd.clicked.connect(lambda: self._skip(10000))
        ctrl.addWidget(btn_fwd)
        lbl_vol = QLabel("Vol:")
        ctrl.addWidget(lbl_vol)
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.audio_out.volume() * 100))
        self.vol_slider.valueChanged.connect(lambda v: self.audio_out.setVolume(v / 100))
        ctrl.addWidget(self.vol_slider)
        video_layout.addLayout(ctrl, 0)

        # Fullscreen + status
        fs_layout = QHBoxLayout()
        btn_fs = QPushButton("Full Screen")
        btn_fs.clicked.connect(self._toggle_fullscreen)
        fs_layout.addWidget(btn_fs)
        self.status = QLabel("No video loaded")
        fs_layout.addWidget(self.status)
        video_layout.addLayout(fs_layout, 0)

        # Progress summary
        summary_layout = QHBoxLayout()
        self.progress = QProgressBar()
        summary_layout.addWidget(self.progress)
        self.summary_label = QLabel("0% complete, 0 left")
        summary_layout.addWidget(self.summary_label)
        video_layout.addLayout(summary_layout, 0)

        # Connect player signals
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.mediaStatusChanged.connect(self._on_media_status)

        # Esc to exit fullscreen
        QShortcut(Qt.Key.Key_Escape, self, activated=self._exit_fullscreen)
        QShortcut(Qt.Key.Key_Escape, self.video_widget, activated=self._exit_fullscreen)

        # Internal state
        self.video_files = []
        self.current_folder = ""
        self.list_visible = True

        # Auto-load
        last = self.state.get("folder", "")
        if os.path.isdir(last):
            self._load_folder(last)

    def _load_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {"folder": "", "watched": {} }

    def _save_state(self):
        self.state['folder'] = self.current_folder
        watched = {path: (self.list_widget.item(i).checkState() == Qt.CheckState.Checked)
                   for i, path in enumerate(self.video_files)}
        self.state['watched'] = watched
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f)

    def closeEvent(self, e):
        self._save_state()
        super().closeEvent(e)

    def _open_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Video Folder")
        if d:
            self._load_folder(d)

    def _load_folder(self, folder):
        self.current_folder = folder
        files = [f for f in os.listdir(folder) if f.lower().endswith('.mp4')]
        files.sort(key=lambda n: int(n.split('.')[0]) if n.split('.')[0].isdigit() else float('inf'))
        self.video_files = [os.path.join(folder, f) for f in files]
        self.list_widget.clear()
        for path in self.video_files:
            item = QListWidgetItem(os.path.basename(path))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if self.state['watched'].get(path, False) else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        self._update_summary()

    def _toggle_list(self):
        self.list_visible = not self.list_visible
        self.list_widget.setVisible(self.list_visible)
        btn = self.sender()
        btn.setText("Hide List" if self.list_visible else "Show List")

    def play_selected(self, item):
        idx = self.list_widget.row(item)
        self.player.setSource(QUrl.fromLocalFile(self.video_files[idx]))
        self.player.play()

    def _on_position(self, pos):
        # Format time properly
        formatted = format_time(pos)
        total = self.player.duration()
        formatted_total = format_time(total)
        self.status.setText(f"{formatted} / {formatted_total}")
        self.slider.setValue(pos)

    def _on_duration(self, dur):
        self.slider.setRange(0, dur)

    def _skip(self, ms):
        self.player.setPosition(max(0, self.player.position() + ms))

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            cur = self.list_widget.currentRow()
            self.list_widget.item(cur).setCheckState(Qt.CheckState.Checked)
            nxt = cur + 1
            if nxt < len(self.video_files):
                self.list_widget.setCurrentRow(nxt)
                self.player.setSource(QUrl.fromLocalFile(self.video_files[nxt]))
                self.player.play()

    def _update_summary(self):
        total = self.list_widget.count()
        watched = sum(1 for i in range(total) if self.list_widget.item(i).checkState() == Qt.CheckState.Checked)
        pct = int((watched/total)*100) if total else 0
        left = total - watched
        self.progress.setValue(pct)
        self.summary_label.setText(f"{pct}% complete, {left} left")

    def _toggle_fullscreen(self):
        self.video_widget.setFullScreen(not self.video_widget.isFullScreen())

    def _exit_fullscreen(self):
        if self.video_widget.isFullScreen():
            self.video_widget.setFullScreen(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = VideoTracker()
    win.show()
    sys.exit(app.exec())
