import time

from PySide6.QtCore import QTimer

class VideoProgress:
    def __init__(self, elapsed_label):
        self.elapsed_label = elapsed_label
        self.start_time = None
        self.output_buffer = ""

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

    def update_progress(self, output, video_duration_seconds, progress_bar):
        # Keep any incomplete line for the next read.
        self.output_buffer += output
        lines = self.output_buffer.split("\n")

        # The last element may be incomplete, so retain it.
        self.output_buffer = lines.pop()

        for line in lines:
            line = line.strip()

            if line.startswith("out_time="):
                time_text = line.split("=", 1)[1]

                if (
                    time_text != "N/A"
                    and video_duration_seconds > 0
                ):
                    try:
                        hours, minutes, seconds = time_text.split(":")

                        elapsed = (
                            int(hours) * 3600
                            + int(minutes) * 60
                            + float(seconds)
                        )

                        percent = int(
                            elapsed / video_duration_seconds * 100
                        )

                        # Keep progress below 100% until FFmpeg finishes.
                        percent = max(0, min(99, percent))

                        # Never let the displayed percentage decrease.
                        percent = max(
                            progress_bar.value(),
                            percent,
                        )

                        progress_bar.setValue(percent)
                        progress_bar.setFormat(
                            f"Generating video: {percent}%"
                        )

                    except ValueError:
                        pass

    def get_elapsed_time_text(self):
        # Get the elapsed time in seconds.
        elapsed_seconds = self.get_elapsed_seconds()

        # Convert seconds into hours, minutes, and seconds.
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"