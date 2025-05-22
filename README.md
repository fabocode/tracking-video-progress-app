# Overview
A simple desktop application built with Python 3 and PyQt6 to help you catalogue and track progress through local .mp4 video courses. It lets you mark videos watched/unwatched, persists your last-used folder and watch states, supports click-to-seek, skip controls, volume adjustment, full-screen mode, and automatic playback of the next video.

# Features
- Folder management: Browse and select any folder containing your course videos.
- Watch tracking: Checkboxes to mark each video watched; persisted across sessions.
- Playback controls: Play, pause, stop, skip ±10 s, click-to-seek, and adjustable volume.
- Full-screen mode: Toggle full-screen and exit with Esc.
- Autoplay next: Automatically plays the next video when one finishes.
- Progress summary: Overall percentage complete and remaining videos count.

# Installation
1. Clone the repository:
```sh
git clone https://github.com/your-username/video-tracker.git
cd video-tracker
```
2. Create and activate a virtual environment (Windows 11 example):
```sh
python -m venv .venv
.venv\Scripts\activate
```
3. Install dependencies:
```sh
pip install PyQt6
```
# Usage
1. Launch the app:
```sh
python video_tracker.py
```
2. Click Open Folder and choose your .mp4 directory.
3. Double-click any video in the list to play.
4. Use the playback controls or click-to-seek slider below the video.
5. oggle full-screen and exit with Esc.

# State Persistence
Your last-opened folder and individual video watch states are stored in:

```sh
C:\Users\<your-username>\.video_tracker_state.json
```
Inspect or back up this file to preserve your progress across machines.

# Configuration
- Custom shortcuts can be added by modifying the QShortcut definitions in video_tracker.py.

- To change skip durations or UI text, adjust the respective button callbacks and labels in the code.

# Contributing
1. Fork this repository.
2. Create a feature branch (git checkout -b feature/awesome-feature).
3. Commit your changes (git commit -m 'Add awesome feature').
4. Push to the branch (git push origin feature/awesome-feature).
5. Open a Pull Request for review.

# License
This project is released under the MIT License. See LICENSE for details
