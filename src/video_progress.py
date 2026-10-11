import time

from PySide6.QtCore import QTimer

class VideoProgress:
    def __init__(self, elapsed_label):
        self.elapsed_label = elapsed_label
        self.start_time = None

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_elapsed_time)

    def start(self):
        # Record when video generation starts.
        self.start_time = time.perf_counter()

        self.elapsed_label.setText("Elapsed time: 00:00:00")
        self.elapsed_label.setVisible(True)

        self.timer.start()

    def update_elapsed_time(self):
        if self.start_time is None:
            return

        elapsed_seconds = self.get_elapsed_seconds()

        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        self.elapsed_label.setText(
            f"Elapsed time: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def get_elapsed_seconds(self):
        if self.start_time is None:
            return 0

        return int(time.perf_counter() - self.start_time)

    def stop_timer(self):
        self.timer.stop()

    def reset(self):
        self.timer.stop()
        self.start_time = None

        self.elapsed_label.setText("Elapsed time: 00:00:00")
        self.elapsed_label.setVisible(False)
