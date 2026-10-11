from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaPlayer

class VideoController:
#"""Handles video playback controls and position updates."""

    def __init__(self, main_window):
        self.main_window = main_window

    def play_pause(self):
        player = self.main_window.media_player

        if player.isPlaying():
            player.pause()
        else:
            player.play()

    def rewind(self):
        player = self.main_window.media_player
        new_position = max(0, player.position() - 10000)
        player.setPosition(new_position)

    def forward(self):
        player = self.main_window.media_player
        new_position = player.position() + 10000
        player.setPosition(new_position)

    def position_changed(self, position):
        window = self.main_window

        window.position_slider.setValue(position)

        window.position_label.setText(
            f"{window.format_time(position)} / "
            f"{window.format_time(window.media_player.duration())}"
        )

        window.team_a_score, window.team_b_score = (
            window.scoreboard.get_score_at_time(position)
        )

        window.update_score_labels()

    def duration_changed(self, duration):
        self.main_window.position_slider.setRange(0, duration)

    def seek(self, position):
        self.main_window.media_player.setPosition(position)

    def seek_from_slider(self):
        window = self.main_window
        position = window.position_slider.value()

        window.media_player.setPosition(position)

        window.team_a_score, window.team_b_score = (
            window.scoreboard.get_score_at_time(position)
        )

        window.update_score_labels()

    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.main_window.play_button.setText("Pause")
        else:
            self.main_window.play_button.setText("Play")
