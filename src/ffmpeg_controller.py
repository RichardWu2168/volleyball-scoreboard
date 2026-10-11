from PySide6.QtCore import QProcess

class FFmpegController:
    def __init__(self):
        # Create the process used to run FFmpeg.
        self.process = QProcess()

        # Store FFmpeg error output for troubleshooting.
        self.error_output = ""

    def start(self, command):
        # Clear errors from the previous generation.
        self.error_output = ""

        # Start FFmpeg asynchronously.
        self.process.setProgram("ffmpeg")
        self.process.setArguments(command)
        self.process.start()

    def read_error_output(self):
        # Read any available FFmpeg error output.
        error = bytes(
            self.process.readAllStandardError()
        ).decode("utf-8", errors="replace")

        self.error_output += error

    def kill(self):
        # Stop FFmpeg if it is running.
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
