import os
import sys
import time
import json

from game import GameData
from project import load_game_file, save_game_file
from scoreboard import Scoreboard
from video_controller import VideoController
from video_generator import VideoGenerator
from video_progress import VideoProgress
from ffmpeg_controller import FFmpegController

from PySide6.QtCore import QUrl, Qt, QProcess
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.game_data = GameData()
        self.scoreboard = Scoreboard(self.game_data)
        self.video_generator = VideoGenerator(self.game_data)
        self.video_controller = VideoController(self)

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
        self.media_player.positionChanged.connect(
            self.video_controller.position_changed
        )
        self.media_player.durationChanged.connect(
            self.video_controller.duration_changed
        )
        self.media_player.playbackStateChanged.connect(
            self.video_controller.playback_state_changed
        )

        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.media_player.setVideoOutput(self.video_widget)

        self.setWindowTitle("Volleyball Scoreboard")

        self.added_event_history = []
        self.event_list = QListWidget()

        self.team_a_score = 0
        self.team_b_score = 0

        self.team_a_name = QLineEdit(self.game_data.team_a_name)
        self.team_b_name = QLineEdit(self.game_data.team_b_name)

        self.team_a_starting_score = QSpinBox()
        self.team_a_starting_score.setValue(self.game_data.starting_score_a)
        self.team_b_starting_score = QSpinBox()
        self.team_b_starting_score.setValue(self.game_data.starting_score_b)

        self.team_a_sets_won_label = QLabel("Sets Won:")
        self.team_b_sets_won_label = QLabel("Sets Won:")
        self.team_a_sets_won_label.setAlignment(Qt.AlignCenter)
        self.team_b_sets_won_label.setAlignment(Qt.AlignCenter)

        self.team_a_sets_won = QSpinBox()
        self.team_a_sets_won.setRange(0, 9)
        self.team_a_sets_won.setValue(0)
        self.team_a_sets_won.setValue(self.game_data.team_a_sets_won)

        self.team_b_sets_won = QSpinBox()
        self.team_b_sets_won.setRange(0, 9)
        self.team_b_sets_won.setValue(0)
        self.team_b_sets_won.setValue(self.game_data.team_b_sets_won)

        self.set_number_label = QLabel("Set #: 1")
        self.set_number_label.setStyleSheet(
            "font-weight: bold;"
        )

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

        self.cancel_video_button = QPushButton("Cancel Generation")
        self.cancel_video_button.setEnabled(False)

        self.video_progress_bar = QProgressBar()
        self.video_progress_bar.setRange(0, 100)
        self.video_progress_bar.setValue(0)
        self.video_progress_bar.setFormat("Ready")
        self.video_progress_bar.setVisible(True)
        self.video_elapsed_label = QLabel("Elapsed time: 00:00:00")
        self.video_elapsed_label.setVisible(False)
        self.video_status_label = QLabel("Status: Ready")
        self.video_progress = VideoProgress(self.video_elapsed_label)

        # Video quality selection
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItem("Highest Quality (CRF 15)", 15)
        self.video_quality_combo.addItem("High Quality (CRF 18)", 18)
        self.video_quality_combo.addItem("Balanced (CRF 23)", 23)
        self.video_quality_combo.addItem("Smaller File (CRF 28)", 28)

        # Use CRF 18 as the default.
        self.video_quality_combo.setCurrentIndex(1)

        # Make the progress bar more noticeable.

        self.video_progress_bar.setStyleSheet(
            "QProgressBar {"
            "    border: none;"
            "    text-align: center;"
            "}"
            "QProgressBar::chunk {"
            "    background-color: #05B8CC;"
            "}"
        )

        self.video_generation_cancelled = False
        self.video_duration_seconds = 0

        # Create the FFmpeg controller.
        self.ffmpeg_controller = FFmpegController()

        # Connect the controller's signals to the existing handlers.
        self.ffmpeg_controller.progress_output_received.connect(
            self.update_video_progress
        )
        self.ffmpeg_controller.process_error_occurred.connect(
            self.ffmpeg_process_error
        )
        self.ffmpeg_controller.process_finished.connect(
            self.video_generation_finished
        )

        self.initialize_button.clicked.connect(self.initialize_scores)

        self.open_video_button.clicked.connect(self.open_video)    
        self.play_button.clicked.connect(self.video_controller.play_pause)
        self.rewind_button.clicked.connect(self.video_controller.rewind)
        self.forward_button.clicked.connect(self.video_controller.forward)
        self.position_slider.sliderMoved.connect(self.video_controller.seek)
        self.position_slider.sliderPressed.connect(self.video_controller.seek_from_slider)

        self.team_a_starting_score.valueChanged.connect(self.update_starting_score_labels)
        self.team_b_starting_score.valueChanged.connect(self.update_starting_score_labels)
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
        self.cancel_video_button.clicked.connect(self.cancel_video_generation)
        self.event_list.itemClicked.connect(self.event_selected)
        self.team_a_sets_won.valueChanged.connect(self.update_set_number)
        self.team_b_sets_won.valueChanged.connect(self.update_set_number)

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

        setup_layout.addWidget(QLabel("Game Setup"), 0, 0, 1, 3)
        setup_layout.addWidget(self.set_number_label, 0, 3, 1, 2)

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

        # Video quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Video Quality:"), 1)
        quality_layout.addWidget(self.video_quality_combo, 3)

        right_layout.addLayout(quality_layout)

        # Generate Video button
        right_layout.addWidget(self.generate_video_button)
        right_layout.addWidget(self.cancel_video_button)

        # Video generation progress
        right_layout.addWidget(self.video_status_label)
        right_layout.addWidget(self.video_progress_bar)
        right_layout.addWidget(self.video_elapsed_label)

        # Exit button
        right_layout.addWidget(self.exit_button)

        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 1)

        # -------------------------------------------------
        # Central widget
        # -------------------------------------------------

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    def update_set_number(self):
        self.game_data.team_a_sets_won = self.team_a_sets_won.value()
        self.game_data.team_b_sets_won = self.team_b_sets_won.value()

        set_number = (
            self.game_data.team_a_sets_won
            + self.game_data.team_b_sets_won
            + 1
        )

        self.set_number_label.setText(
            f"Set #: {set_number}"
        )

    def event_selected(self, item):
        row = self.event_list.row(item)
        event = self.game_data.events[row]

        self.media_player.setPosition(event["time"])

        self.team_a_score = event["score_a"]
        self.team_b_score = event["score_b"]

        self.update_score_labels()
        # self.update_team_buttons()

    def update_starting_score_labels(self):
        self.game_data.starting_score_a = self.team_a_starting_score.value()
        self.game_data.starting_score_b = self.team_b_starting_score.value()

        self.team_a_score = self.game_data.starting_score_a
        self.team_b_score = self.game_data.starting_score_b

        self.update_score_labels()

    def update_score_labels(self):
        self.team_a_score_label.setText(
            f"{self.team_a_score}"
        )
        self.team_b_score_label.setText(
            f"{self.team_b_score}"
        )

    def update_team_buttons(self):
        self.game_data.team_a_name = self.team_a_name.text()
        self.game_data.team_b_name = self.team_b_name.text()

        self.team_a_label.setText(self.game_data.team_a_name)
        self.team_b_label.setText(self.game_data.team_b_name)

        self.team_a_button.setText(f"{self.game_data.team_a_name} + 1")
        self.team_b_button.setText(f"{self.game_data.team_b_name} + 1")

    def reset_game_state(self):
        self.game_data.events.clear()
        self.added_event_history.clear()
        self.event_list.clear()

        self.team_a_score = self.game_data.starting_score_a
        self.team_b_score = self.game_data.starting_score_b

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

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )

        if not file_path:
            return

        # Check whether the current game's video file is missing.
        replacing_missing_video = (
            bool(self.game_data.video_file)
            and not os.path.exists(self.game_data.video_file)
        )

        # Determine whether this is the same video
        same_video = False

        if self.game_data.video_file:
            current_path = os.path.normcase(
                os.path.abspath(self.game_data.video_file)
            )
            new_path = os.path.normcase(
                os.path.abspath(file_path)
            )

            same_video = current_path == new_path

        if same_video:
            return

        if self.game_data.events and not replacing_missing_video:
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

        if not replacing_missing_video:
            self.game_data.events.clear()
            self.added_event_history.clear()
            self.event_list.clear()

            self.team_a_score = self.game_data.starting_score_a
            self.team_b_score = self.game_data.starting_score_b

            self.update_score_labels()
            self.update_team_buttons()

        if not self.ffmpeg_controller.is_running():
            self.video_progress.reset()
            self.video_status_label.setText("Status: Ready")

        self.game_data.video_file = file_path
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
        if self.game_data.events:
            return

        self.team_a_score = self.game_data.starting_score_a
        self.team_b_score = self.game_data.starting_score_b

        event = {
            "time": 0,
            "team": "START",
            "score_a": self.game_data.starting_score_a,
            "score_b": self.game_data.starting_score_b,
        }

        self.game_data.events.append(event)

    def team_a_button_clicked(self):
        self.add_starting_event()

        current_time = self.media_player.position()

        # Calculate the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        # Record Team A's new point.
        self.team_a_score += 1

        event = {
            "time": current_time,
            "team": "A",
            "score_a": self.team_a_score,
            "score_b": self.team_b_score,
        }

        self.game_data.events.append(event)
        self.added_event_history.append(event)

        # Lock the starting scores once the first point is recorded.
        self.team_a_starting_score.setEnabled(False)
        self.team_b_starting_score.setEnabled(False)

        self.scoreboard.recalculate_scores()

        # Display the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        self.update_score_labels()
        self.refresh_event_list(event)

    def team_b_button_clicked(self):
        self.add_starting_event()

        current_time = self.media_player.position()

        # Calculate the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        # Record Team B's new point.
        self.team_b_score += 1

        event = {
            "time": current_time,
            "team": "B",
            "score_a": self.team_a_score,
            "score_b": self.team_b_score,
        }

        self.game_data.events.append(event)
        self.added_event_history.append(event)

        # Lock the starting scores once the first point is recorded.
        self.team_a_starting_score.setEnabled(False)
        self.team_b_starting_score.setEnabled(False)

        self.scoreboard.recalculate_scores()

        # Display the score at the current video timestamp.
        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        self.update_score_labels()
        self.refresh_event_list(event)

    def undo_last_score(self):
        if not self.added_event_history:
            return

        event = self.added_event_history[-1]

        if event not in self.game_data.events:
            self.added_event_history.pop()
            return

        self.added_event_history.pop()
        self.game_data.events.remove(event)

        self.scoreboard.recalculate_scores()
        self.refresh_event_list()

        current_time = self.media_player.position()

        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        self.update_score_labels()
        
    def delete_selected_event(self):
        selected_row = self.event_list.currentRow()

        if selected_row < 0:
            return

        event = self.game_data.events[selected_row]

        if event["team"] == "START":
            return

        self.game_data.events.remove(event)

        # Remove the event from Undo history as well.
        self.added_event_history = [
            added_event
            for added_event in self.added_event_history
            if added_event is not event
        ]

        self.scoreboard.recalculate_scores()
        self.refresh_event_list()

        current_time = self.media_player.position()

        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        self.update_score_labels()

    def edit_selected_event_time(self):
        selected_row = self.event_list.currentRow()

        if selected_row < 0:
            return

        event = self.game_data.events[selected_row]

        # Do not allow editing the starting-score event.
        if event["team"] == "START":
            return

        # Update the event timestamp to the current video position.
        event["time"] = self.media_player.position()

        # Recalculate scores and sort events by timestamp.
        self.scoreboard.recalculate_scores()

        # Refresh the event list.
        self.refresh_event_list()

        # Keep the edited event selected, even if its row changed.
        new_row = self.game_data.events.index(event)
        self.event_list.setCurrentRow(new_row)

        # Update the displayed score for the current video position.
        current_time = self.media_player.position()

        self.team_a_score, self.team_b_score = (
            self.scoreboard.get_score_at_time(current_time)
        )

        self.update_score_labels()
    
    def refresh_event_list(self, selected_event=None):
        self.event_list.clear()

        for event in self.game_data.events:
            time_text = self.format_time(event["time"])

            if event["team"] == "START":
                team_name = "Starting Score"
            elif event["team"] == "A":
                team_name = self.game_data.team_a_name
            else:
                team_name = self.game_data.team_b_name

            self.event_list.addItem(
                f"{time_text}    "
                f"{event['score_a']} - {event['score_b']}    "
                f"{team_name}"
            )

        if selected_event is not None:
            for row, event in enumerate(self.game_data.events):
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

        if not file_path.lower().endswith(".json"):
            file_path += ".json"

        try:
            save_game_file(file_path, self.game_data)

        except (OSError, TypeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save the game.\n\n{error}"
            )

    def load_game(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Game",
            "",
            "Game Files (*.json)"
        )

        if not file_path:
            return

        # Read and validate the file before modifying the current game.
        try:
            saved_data = load_game_file(file_path)

        except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Could not load the game file.\n\n{error}"
            )
            return

        # Apply the validated data to the application.
        if not self.ffmpeg_controller.is_running():
            self.video_progress.reset()
            self.video_status_label.setText("Status: Ready")

        # Update GameData first.
        self.game_data.video_file = saved_data["video_file"]

        self.game_data.team_a_name = saved_data["team_a_name"]
        self.game_data.team_b_name = saved_data["team_b_name"]

        self.game_data.team_a_sets_won = saved_data.get(
            "team_a_sets_won", 0
        )
        self.game_data.team_b_sets_won = saved_data.get(
            "team_b_sets_won", 0
        )

        self.game_data.starting_score_a = saved_data["starting_score_a"]
        self.game_data.starting_score_b = saved_data["starting_score_b"]

        self.game_data.events = saved_data["events"]

        # Update the UI from GameData.
        self.video_file_label.setText(
            f"Video: {os.path.basename(self.game_data.video_file)}"
        )

        self.team_a_name.setText(self.game_data.team_a_name)
        self.team_b_name.setText(self.game_data.team_b_name)

        self.team_a_sets_won.setValue(self.game_data.team_a_sets_won)
        self.team_b_sets_won.setValue(self.game_data.team_b_sets_won)

        self.team_a_starting_score.setValue(
            self.game_data.starting_score_a
        )
        self.team_b_starting_score.setValue(
            self.game_data.starting_score_b
        )

        # Reset the undo history for the newly loaded game.
        self.added_event_history = []

        self.scoreboard.recalculate_scores()
        self.refresh_event_list()

        self.team_a_score, self.team_b_score = self.scoreboard.get_score_at_time(
            self.media_player.position()
        )

        self.update_score_labels()
        self.update_team_buttons()

        self.team_a_name.setEnabled(False)
        self.team_b_name.setEnabled(False)
        self.team_a_starting_score.setEnabled(False)
        self.team_b_starting_score.setEnabled(False)

        self.initialize_button.setEnabled(False)

        if os.path.exists(self.game_data.video_file):
            self.media_player.setSource(
                QUrl.fromLocalFile(self.game_data.video_file)
            )
        else:
            QMessageBox.warning(
                self,
                "Video Not Found",
                f"The video file could not be found:\n\n"
                f"{self.game_data.video_file}"
            )

    def generate_video(self):
        # Check whether a video has been selected.
        if not self.game_data.video_file:
            QMessageBox.warning(
                self,
                "No Video",
                "Please open a video file first."
            )
            return

        # Check whether there are any score events.
        if not self.game_data.events:
            QMessageBox.warning(
                self,
                "No Score Events",
                "Please add at least one score event before generating the video."
            )
            return

        # Ask the user where to save the generated video.
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Generated Video",
            "",
            "MP4 Video (*.mp4)"
        )

        if not output_file:
            return

        # Add the .mp4 extension if necessary.
        if not output_file.lower().endswith(".mp4"):
            output_file += ".mp4"

        self.current_output_file = output_file

        # Get the video duration in seconds.
        self.video_duration_seconds = self.media_player.duration() / 1000

        if self.video_duration_seconds <= 0:
            QMessageBox.warning(
                self,
                "Invalid Video Duration",
                "The video duration is not available. Please wait until the video loads."
            )
            return

        # Build the timeline and FFmpeg filter.
        timeline = self.video_generator.build_score_timeline(
            self.media_player.duration()
        )
        ffmpeg_filter = self.video_generator.build_ffmpeg_filter(timeline)

        # Prepare the FFmpeg command.
        command = self.video_generator.build_ffmpeg_command(
            output_file,
            ffmpeg_filter,
            self.video_quality_combo.currentData()
        )

        # Reset the progress bar and error output.
        self.video_progress.output_buffer = ""
        self.video_generation_cancelled = False
        self.video_progress_bar.setValue(0)
        self.video_progress_bar.setFormat("Generating video: 0%")
        self.video_progress_bar.setVisible(True)
        self.video_status_label.setText("Status: Generating video...")

        # Start the elapsed-time timer.
        self.video_progress.start()

        # Prevent another generation request while FFmpeg is running.
        self.generate_video_button.setEnabled(False)
        self.cancel_video_button.setEnabled(True)

        # Start FFmpeg asynchronously.
        self.ffmpeg_controller.start(command)

    def update_video_progress(self, output):
        # Update the progress display using the output received from FFmpeg.
        self.video_progress.update_progress(
            output,
            self.video_duration_seconds,
            self.video_progress_bar,
        )

    def cancel_video_generation(self):
        if not self.ffmpeg_controller.is_running():
            return

        reply = QMessageBox.question(
            self,
            "Cancel Video Generation",
            "Are you sure you want to cancel video generation?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.video_generation_cancelled = True
            self.ffmpeg_controller.kill()

    def ffmpeg_process_error(self, error):
        # Handle failure to start FFmpeg.
        if error == QProcess.ProcessError.FailedToStart:
            self.video_status_label.setText(
                "Status: Video generation failed"
            )
            self.video_progress.stop_timer()
            self.generate_video_button.setEnabled(True)
            self.cancel_video_button.setEnabled(False)

            self.video_progress_bar.setFormat("Generation failed")

            # Get the error message from FFmpegController.
            error_message = self.ffmpeg_controller.get_error_message(
                error
            )

            QMessageBox.critical(
                self,
                "FFmpeg Error",
                error_message
            )

    def video_generation_finished(self, exit_code, exit_status):
        # Stop the elapsed-time timer.
        self.video_progress.stop_timer()

        # Calculate the total elapsed time.
        elapsed_seconds = elapsed_text = self.video_progress.get_elapsed_time_text()

        self.generate_video_button.setEnabled(True)
        self.cancel_video_button.setEnabled(False)

        if self.video_generation_cancelled:
            self.video_status_label.setText(
                "Status: Video generation cancelled"
            )
            self.video_progress_bar.setFormat("Generation cancelled")
            self.video_elapsed_label.setText(
                f"Elapsed time: {elapsed_text}"
            )

            # Delete the incomplete output file.
            if os.path.exists(self.current_output_file):
                try:
                    os.remove(self.current_output_file)
                except OSError as error:
                    QMessageBox.warning(
                        self,
                        "Cleanup Warning",
                        f"Generation was cancelled, but the incomplete "
                        f"video file could not be deleted:\n\n"
                        f"{self.current_output_file}\n\n{error}"
                    )

            QMessageBox.information(
                self,
                "Video Generation Cancelled",
                f"Video generation was cancelled.\n\n"
                f"Elapsed time: {elapsed_text}"
            )

        elif exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            self.video_status_label.setText("Status: Video generation completed")
            self.video_progress_bar.setValue(100)
            self.video_progress_bar.setFormat("Completed: 100%")

            self.video_elapsed_label.setText(
                f"Elapsed time: {elapsed_text}"
            )

            QMessageBox.information(
                self,
                "Video Generated",
                f"The video was generated successfully.\n\n"
                f"Elapsed time: {elapsed_text}"
            )
        else:
            self.video_status_label.setText("Status: Video generation failed")
            self.video_progress_bar.setFormat("Generation failed")

            self.video_elapsed_label.setText(
                f"Elapsed time: {elapsed_text}"
            )

            QMessageBox.critical(
                self,
                "Video Generation Failed",
                f"{self.ffmpeg_controller.error_output or 'FFmpeg could not generate the video.'}\n\n"
                f"Elapsed time: {elapsed_text}"
            )

    def closeEvent(self, event):
        if self.ffmpeg_controller.is_running():
            QMessageBox.warning(
                self,
                "Video Generation in Progress",
                "Please wait until video generation finishes before closing the application."
            )
            event.ignore()
            return

        event.accept()

app = QApplication(sys.argv)

window = MainWindow()
window.resize(1200, 800)
window.show()

sys.exit(app.exec())