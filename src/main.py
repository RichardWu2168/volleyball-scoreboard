import json
import os
import subprocess
import sys

from pathlib import Path
from warnings import filters

from PySide6.QtCore import QUrl, Qt
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.video_file_path = ""
        self.video_file_label = QLabel("No video loaded")

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(800, 320)
        self.play_button = QPushButton("Play")

        self.position_label = QLabel("00:00.000 / 00:00.000")

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)

        self.rewind_button = QPushButton("-10 sec")
        self.forward_button = QPushButton("+10 sec")

        self.media_player = QMediaPlayer()
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)

        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.media_player.setVideoOutput(self.video_widget)

        self.setWindowTitle("Volleyball Scoreboard")
        
        self.events = []
        self.added_event_history = []
        self.event_list = QListWidget()

        self.team_a_score = 0
        self.team_b_score = 0

        self.team_a_name = QLineEdit("Team A")
        self.team_b_name = QLineEdit("Team B")

        self.team_a_starting_score = QSpinBox()
        self.team_b_starting_score = QSpinBox()

        self.team_a_sets_won_label = QLabel("Sets Won:")
        self.team_b_sets_won_label = QLabel("Sets Won:")
        self.team_a_sets_won_label.setAlignment(Qt.AlignCenter)
        self.team_b_sets_won_label.setAlignment(Qt.AlignCenter)

        self.team_a_sets_won = QSpinBox()
        self.team_a_sets_won.setRange(0, 9)
        self.team_a_sets_won.setValue(0)

        self.team_b_sets_won = QSpinBox()
        self.team_b_sets_won.setRange(0, 9)
        self.team_b_sets_won.setValue(0)

        self.team_a_starting_score.setRange(0, 99)
        self.team_b_starting_score.setRange(0, 99)

        self.team_a_label = QLabel("Team A")
        self.team_b_label = QLabel("Team B")
        self.team_a_label.setAlignment(Qt.AlignCenter)
        self.team_b_label.setAlignment(Qt.AlignCenter)
        self.team_a_label.setStyleSheet(
            "font-size: 12pt; font-weight: bold;"
        )
        self.team_b_label.setStyleSheet(
            "font-size: 12pt; font-weight: bold;"
        )

        self.team_a_score_label = QLabel("0")
        self.team_b_score_label = QLabel("0")
        self.team_a_score_label.setAlignment(Qt.AlignCenter)
        self.team_b_score_label.setAlignment(Qt.AlignCenter)
        self.team_a_score_label.setStyleSheet(
            "font-size: 48pt; font-weight: bold;"
        )
        self.team_b_score_label.setStyleSheet(
            "font-size: 48pt; font-weight: bold;"
        )

        self.open_video_button = QPushButton("Open Video")
        self.team_a_button  = QPushButton("Team A + 1")
        self.team_b_button  = QPushButton("Team B + 1")
        self.undo_button = QPushButton("Undo Last Score")
        self.delete_button = QPushButton("Delete Selected Event")
        self.edit_event_time_button = QPushButton("Edit Event Time")
        self.exit_button = QPushButton("Exit")
        self.initialize_button = QPushButton("Start Game")
        self.new_game_button = QPushButton("New Game")
        self.save_button = QPushButton("Save Game")
        self.load_button = QPushButton("Load Game")
        self.generate_video_button = QPushButton("Generate Video")

        self.initialize_button.clicked.connect(self.initialize_scores)

        self.open_video_button.clicked.connect(self.open_video)    
        self.play_button.clicked.connect(self.play_pause)
        self.rewind_button.clicked.connect(self.rewind)
        self.forward_button.clicked.connect(self.forward)
        self.position_slider.sliderMoved.connect(self.seek)
        self.position_slider.sliderPressed.connect(self.seek_from_slider)

        self.team_a_starting_score.valueChanged.connect(self.update_starting_score_labels)
        self.team_b_starting_score.valueChanged.connect(self.update_starting_score_labels)
        self.team_a_name.textChanged.connect(self.update_score_labels)
        self.team_b_name.textChanged.connect(self.update_score_labels)
        self.team_a_name.textChanged.connect(self.update_team_buttons)
        self.team_b_name.textChanged.connect(self.update_team_buttons)

        self.team_a_button.clicked.connect(self.team_a_button_clicked)
        self.team_b_button.clicked.connect(self.team_b_button_clicked)
        self.undo_button.clicked.connect(self.undo_last_score)
        self.delete_button.clicked.connect(self.delete_selected_event)
        self.edit_event_time_button.clicked.connect(self.edit_selected_event_time)
        self.exit_button.clicked.connect(self.close)
        self.new_game_button.clicked.connect(self.new_game)
        self.save_button.clicked.connect(self.save_game)
        self.load_button.clicked.connect(self.load_game)
        self.generate_video_button.clicked.connect(self.generate_video)
        self.event_list.itemClicked.connect(self.event_selected)

        # Main layout
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # -------------------------------------------------
        # Video
        # -------------------------------------------------

        left_layout.addWidget(self.open_video_button)
        left_layout.addWidget(self.video_file_label)
        left_layout.addWidget(self.video_widget, 1)

        # -------------------------------------------------
        # Video controls
        # -------------------------------------------------

        video_controls_layout = QHBoxLayout()

        video_controls_layout.addWidget(self.rewind_button)
        video_controls_layout.addWidget(self.play_button)
        video_controls_layout.addWidget(self.forward_button)

        left_layout.addWidget(self.position_label)
        left_layout.addWidget(self.position_slider)
        left_layout.addLayout(video_controls_layout)

        # -------------------------------------------------
        # Game setup + current score
        # -------------------------------------------------

        game_layout = QHBoxLayout()

        # Game setup
        setup_layout = QGridLayout()

        setup_layout.addWidget(QLabel("Game Setup"), 0, 0, 1, 4)

        setup_layout.addWidget(QLabel("Team A:"), 1, 0)
        setup_layout.addWidget(self.team_a_name, 1, 1, 1, 3)

        setup_layout.addWidget(QLabel("Start:"), 2, 0)
        setup_layout.addWidget(self.team_a_starting_score, 2, 1)

        setup_layout.addWidget(self.team_a_sets_won_label, 2, 2)
        setup_layout.addWidget(self.team_a_sets_won, 2, 3)

        setup_layout.addWidget(QLabel("Team B:"), 3, 0)
        setup_layout.addWidget(self.team_b_name, 3, 1, 1, 3)

        setup_layout.addWidget(QLabel("Start:"), 4, 0)
        setup_layout.addWidget(self.team_b_starting_score, 4, 1)

        setup_layout.addWidget(self.team_b_sets_won_label, 4, 2)
        setup_layout.addWidget(self.team_b_sets_won, 4, 3)

        setup_layout.addWidget(self.initialize_button, 5, 0)
        setup_layout.addWidget(self.new_game_button, 5, 1)
        setup_layout.addWidget(self.save_button, 5, 2)
        setup_layout.addWidget(self.load_button, 5, 3)

        # Current score layout
        score_layout = QGridLayout()

        # Current scores
        score_layout.addWidget(QLabel("Current Score"), 0, 0, 1, 4)

        # Team A
        score_layout.addWidget(self.team_a_label, 1, 0, 1, 2)
        score_layout.addWidget(self.team_a_score_label, 2, 0, 1, 2)
        score_layout.addWidget(self.team_a_button, 3, 0, 1, 2)

        # Team B
        score_layout.addWidget(self.team_b_label, 1, 2, 1, 2)
        score_layout.addWidget(self.team_b_score_label, 2, 2, 1, 2)
        score_layout.addWidget(self.team_b_button, 3, 2, 1, 2)

        # Make the four columns fill the available width
        for column in range(4):
            score_layout.setColumnStretch(column, 1)

        # Put the two vertical layouts side by side
        game_layout.addLayout(setup_layout)
        game_layout.addLayout(score_layout)
        game_layout.setStretch(0, 1)
        game_layout.setStretch(1, 1)

        # Add the horizontal layout to the main vertical layout
        left_layout.addLayout(game_layout)

        # -------------------------------------------------
        # Score events
        # -------------------------------------------------

        right_layout.addWidget(QLabel("Score Events"))
        right_layout.addWidget(self.event_list)

        # -------------------------------------------------
        # Event editing buttons
        # -------------------------------------------------

        event_buttons_layout = QHBoxLayout()

        event_buttons_layout.addWidget(self.undo_button)
        event_buttons_layout.addWidget(self.delete_button)
        event_buttons_layout.addWidget(self.edit_event_time_button)

        right_layout.addLayout(event_buttons_layout)

        # Exit button
        right_layout.addWidget(self.exit_button)

        # Generate Video button
        right_layout.addWidget(self.generate_video_button)

        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 1)

        # -------------------------------------------------
        # Central widget
        # -------------------------------------------------

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    def event_selected(self, item):
        row = self.event_list.row(item)
        event = self.events[row]

        self.media_player.setPosition(event["time"])

        self.team_a_score = event["score_a"]
        self.team_b_score = event["score_b"]

        self.update_score_labels()
        # self.update_team_buttons()

    def update_starting_score_labels(self):
        self.team_a_score = self.team_a_starting_score.value()
        self.team_b_score = self.team_b_starting_score.value()
        self.update_score_labels()

    def update_score_labels(self):
        self.team_a_score_label.setText(
            f"{self.team_a_score}"
        )
        self.team_b_score_label.setText(
            f"{self.team_b_score}"
        )

    def update_team_buttons(self):
        self.team_a_label.setText(
            f"{self.team_a_name.text()}"
        )
        self.team_b_label.setText(
            f"{self.team_b_name.text()}"
        )        
        self.team_a_button.setText(
            f"{self.team_a_name.text()} + 1"
        )
        self.team_b_button.setText(
            f"{self.team_b_name.text()} + 1"
        )        

    def reset_game_state(self):
        self.events.clear()
        self.added_event_history.clear()
        self.event_list.clear()

        self.team_a_score = self.team_a_starting_score.value()
        self.team_b_score = self.team_b_starting_score.value()

        self.update_score_labels()
        self.update_team_buttons()

    def initialize_scores(self):
        self.reset_game_state()

        self.team_a_name.setEnabled(False)
        self.team_b_name.setEnabled(False)
        self.team_a_starting_score.setEnabled(False)
        self.team_b_starting_score.setEnabled(False)

        self.initialize_button.setEnabled(False)

    def new_game(self):
        self.reset_game_state()

        self.team_a_name.setEnabled(True)
        self.team_b_name.setEnabled(True)
        self.team_a_starting_score.setEnabled(True)
        self.team_b_starting_score.setEnabled(True)

        self.initialize_button.setEnabled(True)

    def play_pause(self):
        if self.media_player.isPlaying():
            self.media_player.pause()
        else:
            self.media_player.play()

    def rewind(self):
        new_position = max(0, self.media_player.position() - 10000)
        self.media_player.setPosition(new_position)

    def forward(self):
        new_position = self.media_player.position() + 10000
        self.media_player.setPosition(new_position)

    def position_changed(self, position):
        self.position_slider.setValue(position)

        self.position_label.setText(
            f"{self.format_time(position)} / "
            f"{self.format_time(self.media_player.duration())}"
        )

        # Update the score based on the current video position.
        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(position)
        )

        self.update_score_labels()

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def seek(self, position):
        self.media_player.setPosition(position)

    def seek_from_slider(self):
        position = self.position_slider.value()
        self.media_player.setPosition(position)

        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(position)
        )

        self.update_score_labels()

    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )

        if not file_path:
            return

        # Determine whether this is the same video
        same_video = False

        if self.video_file_path:
            current_path = os.path.normcase(
                os.path.abspath(self.video_file_path)
            )
            new_path = os.path.normcase(
                os.path.abspath(file_path)
            )

            same_video = current_path == new_path

        if same_video:
            return

        if self.events:
            result = QMessageBox.question(
                self,
                "Open New Video",
                "Opening a new video will clear the current score events. "
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result != QMessageBox.Yes:
                return

        self.events.clear()
        self.added_event_history.clear()
        self.event_list.clear()

        self.team_a_score = self.team_a_starting_score.value()
        self.team_b_score = self.team_b_starting_score.value()

        self.update_score_labels()
        self.update_team_buttons()

        self.video_file_path = file_path
        self.video_file_label.setText(
            f"Video: {os.path.basename(file_path)}"
        )

        self.media_player.setSource(
            QUrl.fromLocalFile(file_path)
        )
        self.media_player.play()

    def format_time(self, milliseconds):
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        millis = milliseconds % 1000

        return f"{minutes:02d}:{seconds:02d}.{millis:03d}"

    def add_starting_event(self):
        if self.events:
            return

        self.team_a_score = self.team_a_starting_score.value()
        self.team_b_score = self.team_b_starting_score.value()

        event = {
            "time": 0,
            "team": "START",
            "score_a": self.team_a_starting_score.value(),
            "score_b": self.team_b_starting_score.value(),
        }

        self.events.append(event)

    def team_a_button_clicked(self):
        self.add_starting_event()

        current_time = self.media_player.position()

        # Calculate the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        # Record Team A's new point.
        self.team_a_score += 1

        event = {
            "time": current_time,
            "team": "A",
            "score_a": self.team_a_score,
            "score_b": self.team_b_score,
        }

        self.events.append(event)
        self.added_event_history.append(event)

        self.recalculate_scores()

        # Display the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        self.update_score_labels()
        self.refresh_event_list(event)

    def team_b_button_clicked(self):
        self.add_starting_event()

        current_time = self.media_player.position()

        # Calculate the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        # Record Team B's new point.
        self.team_b_score += 1

        event = {
            "time": current_time,
            "team": "B",
            "score_a": self.team_a_score,
            "score_b": self.team_b_score,
        }

        self.events.append(event)
        self.added_event_history.append(event)

        self.recalculate_scores()

        # Display the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        self.update_score_labels()
        self.refresh_event_list(event)

    def undo_last_score(self):
        if not self.added_event_history:
            return

        event = self.added_event_history[-1]

        if event not in self.events:
            self.added_event_history.pop()
            return

        self.added_event_history.pop()
        self.events.remove(event)

        self.recalculate_scores()
        self.refresh_event_list()

        current_time = self.media_player.position()

        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        self.update_score_labels()
        
    def delete_selected_event(self):
        selected_row = self.event_list.currentRow()

        if selected_row < 0:
            return

        event = self.events[selected_row]

        if event["team"] == "START":
            return

        self.events.remove(event)

        # Remove the event from Undo history as well.
        self.added_event_history = [
            added_event
            for added_event in self.added_event_history
            if added_event is not event
        ]

        self.recalculate_scores()
        self.refresh_event_list()

        current_time = self.media_player.position()

        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        self.update_score_labels()

    def edit_selected_event_time(self):
        selected_row = self.event_list.currentRow()

        if selected_row < 0:
            return

        event = self.events[selected_row]

        # Do not allow editing the starting-score event.
        if event["team"] == "START":
            return

        # Update the event timestamp to the current video position.
        event["time"] = self.media_player.position()

        # Recalculate scores and sort events by timestamp.
        self.recalculate_scores()

        # Refresh the event list.
        self.refresh_event_list()

        # Keep the edited event selected, even if its row changed.
        new_row = self.events.index(event)
        self.event_list.setCurrentRow(new_row)

        # Update the displayed score for the current video position.
        current_time = self.media_player.position()

        self.team_a_score, self.team_b_score = (
            self.get_score_at_time(current_time)
        )

        self.update_score_labels()
    
    def recalculate_scores(self):
        score_a = self.team_a_starting_score.value()
        score_b = self.team_b_starting_score.value()

        self.events.sort(key=lambda event: event["time"])

        for event in self.events:
            if event["team"] == "START":
                score_a = self.team_a_starting_score.value()
                score_b = self.team_b_starting_score.value()

            elif event["team"] == "A":
                score_a += 1

            elif event["team"] == "B":
                score_b += 1

            event["score_a"] = score_a
            event["score_b"] = score_b

    def get_score_at_time(self, time_ms):
        score_a = self.team_a_starting_score.value()
        score_b = self.team_b_starting_score.value()

        for event in sorted(self.events, key=lambda e: e["time"]):
            if event["time"] > time_ms:
                break

            if event["team"] == "A":
                score_a += 1
            elif event["team"] == "B":
                score_b += 1

        return score_a, score_b

    def refresh_event_list(self, selected_event=None):
        self.event_list.clear()

        for event in self.events:
            time_text = self.format_time(event["time"])

            if event["team"] == "START":
                team_name = "Starting Score"
            elif event["team"] == "A":
                team_name = self.team_a_name.text()
            else:
                team_name = self.team_b_name.text()

            self.event_list.addItem(
                f"{time_text}    "
                f"{event['score_a']} - {event['score_b']}    "
                f"{team_name}"
            )

        if selected_event is not None:
            for row, event in enumerate(self.events):
                if event is selected_event:
                    item = self.event_list.item(row)
                    self.event_list.setCurrentItem(item)
                    self.event_list.scrollToItem(item)
                    break

    def save_game(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Game",
            "",
            "Game Files (*.json)"
        )

        if not file_path:
            return

        game_data = {
            "video_file": self.video_file_path,
            "team_a_name": self.team_a_name.text(),
            "team_b_name": self.team_b_name.text(),
            "team_a_sets_won": self.team_a_sets_won.value(),
            "team_b_sets_won": self.team_b_sets_won.value(),
            "starting_score_a": self.team_a_starting_score.value(),
            "starting_score_b": self.team_b_starting_score.value(),
            "events": self.events,
        }

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(game_data, file, indent=4)

    def load_game(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Game",
            "",
            "Game Files (*.json)"
        )

        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as file:
            game_data = json.load(file)

        self.video_file_path = game_data["video_file"]
        self.video_file_label.setText(
            f"Video: {os.path.basename(self.video_file_path)}"
        )

        self.team_a_name.setText(game_data["team_a_name"])
        self.team_b_name.setText(game_data["team_b_name"])

        self.team_a_sets_won.setValue(game_data.get("team_a_sets_won", 0))
        self.team_b_sets_won.setValue(game_data.get("team_b_sets_won", 0))

        self.team_a_starting_score.setValue(
            game_data["starting_score_a"]
        )
        self.team_b_starting_score.setValue(
            game_data["starting_score_b"]
        )

        self.events = game_data["events"]

        self.recalculate_scores()
        self.refresh_event_list()

        if self.events:
            last_event = self.events[-1]
            self.team_a_score = last_event["score_a"]
            self.team_b_score = last_event["score_b"]
        else:
            self.team_a_score = self.team_a_starting_score.value()
            self.team_b_score = self.team_b_starting_score.value()

        self.update_score_labels()
        self.update_team_buttons()

        self.team_a_name.setEnabled(False)
        self.team_b_name.setEnabled(False)
        self.team_a_starting_score.setEnabled(False)
        self.team_b_starting_score.setEnabled(False)

        self.initialize_button.setEnabled(False)

        if os.path.exists(self.video_file_path):
            self.media_player.setSource(
                QUrl.fromLocalFile(self.video_file_path)
            )
        else:
            QMessageBox.warning(
                self,
                "Video Not Found",
                f"The video file could not be found:\n\n"
                f"{self.video_file_path}"
            )

    def build_score_timeline(self):
        timeline = []

        current_time = 0
        current_score_a = self.team_a_starting_score.value()
        current_score_b = self.team_b_starting_score.value()

        for event in self.events:
            if event["team"] == "START":
                current_score_a = event["score_a"]
                current_score_b = event["score_b"]
                continue

            timeline.append({
                "start_time": current_time,
                "end_time": event["time"],
                "score_a": current_score_a,
                "score_b": current_score_b,
            })

            current_time = event["time"]
            current_score_a = event["score_a"]
            current_score_b = event["score_b"]

        # Last score continues until the end of the video
        timeline.append({
            "start_time": current_time,
            "end_time": self.media_player.duration(),
            "score_a": current_score_a,
            "score_b": current_score_b,
        })

        return timeline

    def build_ffmpeg_filter(self, timeline):
        filters = []

        team_a_name = self.team_a_name.text()
        team_b_name = self.team_b_name.text()

        sets_a = self.team_a_sets_won.value()
        sets_b = self.team_b_sets_won.value()

        for i, period in enumerate(timeline):
            text = (
                f"{sets_a}  {team_a_name}    "
                f"{period['score_a']} - {period['score_b']}    "
                f"{team_b_name}  {sets_b}"
            )

            start = period["start_time"] / 1000

            if i == len(timeline) - 1:
                enable = f"gte(t,{start:.3f})"
            else:
                end = period["end_time"] / 1000
                enable = f"gte(t,{start:.3f})*lt(t,{end:.3f})"

            filters.append(
                "drawtext="
                f"text='{text}':"
                "fontcolor=white:"
                "fontsize=72:"
                "box=1:"
                "boxcolor=black@0.6:"
                "boxborderw=20:"
                "x=(w-text_w)/2:"
                "y=h-text_h-30:"
                f"enable='{enable}'"
            )

        return ",".join(filters)

    def generate_video(self):
        if not self.video_file_path:
            QMessageBox.warning(
                self,
                "No Video",
                "Please load a video first."
            )
            return

        if not os.path.exists(self.video_file_path):
            QMessageBox.warning(
                self,
                "Video Not Found",
                f"The video file could not be found:\n\n"
                f"{self.video_file_path}"
            )
            return

        if not self.events:
            QMessageBox.warning(
                self,
                "No Score Events",
                "There are no score events to generate."
            )
            return

        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Generate Video",
            "",
            "MP4 Video (*.mp4)"
        )

        if not output_file:
            return

        # Build the score timeline from the recorded events.
        timeline = self.build_score_timeline()

        if not timeline:
            QMessageBox.warning(
                self,
                "No Timeline",
                "There is no score timeline to generate."
            )
            return

        # Build the FFmpeg drawtext filter.
        ffmpeg_filter = self.build_ffmpeg_filter(timeline)

        command = [
            "ffmpeg",
            "-y",
            "-i",
            self.video_file_path,
            "-vf",
            ffmpeg_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "copy",
            output_file
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                QMessageBox.critical(
                    self,
                    "FFmpeg Error",
                    result.stderr[-3000:]
                )
                return

            QMessageBox.information(
                self,
                "Video Generated",
                f"Video generated successfully:\n\n{output_file}"
            )

        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                "FFmpeg could not be found. "
                "Please make sure FFmpeg is installed and available in PATH."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate video:\n\n{e}"
            )
app = QApplication(sys.argv)

window = MainWindow()
window.resize(1200, 800)
window.show()

sys.exit(app.exec())