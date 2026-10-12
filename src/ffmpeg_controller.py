from PySide6.QtCore import QObject, QProcess, Signal

class FFmpegController(QObject):
    # Signals that MainWindow can connect to.
    progress_output_received = Signal(str)
    process_error_occurred = Signal(object)
    process_finished = Signal(int, object)

    def __init__(self):
        super().__init__()

        # Create the process used to run FFmpeg.
        self.process = QProcess(self)

        # Store FFmpeg error output for troubleshooting.
        self.error_output = ""

        # Connect process signals to the controller's signals and methods.
        self.process.readyReadStandardOutput.connect(
            self.read_progress_output
        )
        self.process.readyReadStandardError.connect(
            self.read_error_output
        )
        self.process.errorOccurred.connect(
            self._handle_process_error
        )
        self.process.finished.connect(
            self._handle_process_finished
        )

    def _handle_process_error(self, error):
        # Forward the process error through the controller's signal.
        self.process_error_occurred.emit(error)

    def get_error_message(self, error):
        # Return a helpful message for common process errors.
        if error == QProcess.ProcessError.FailedToStart:
            return (
                "Could not start FFmpeg. Please check that FFmpeg "
                "is installed and accessible from your PATH."
            )

        if error == QProcess.ProcessError.Crashed:
            return "FFmpeg crashed while generating the video."

        if error == QProcess.ProcessError.Timedout:
            return "The FFmpeg process timed out."

        if error == QProcess.ProcessError.ReadError:
            return "An error occurred while reading FFmpeg output."

        if error == QProcess.ProcessError.WriteError:
            return "An error occurred while writing to FFmpeg."

        return "An unknown FFmpeg process error occurred."

    def _handle_process_finished(self, exit_code, exit_status):
        # Forward the process completion through the controller's signal.
        self.process_finished.emit(exit_code, exit_status)

    def start(self, command):
        # Do not start FFmpeg if it is already running.
        if self.is_running():
            return False

        # Clear errors from the previous generation.
        self.error_output = ""

        # Start FFmpeg asynchronously.
        self.process.setProgram("ffmpeg")
        self.process.setArguments(command)
        self.process.start()

        return True

    def read_progress_output(self):
        # Read FFmpeg progress output.
        output = bytes(
            self.process.readAllStandardOutput()
        ).decode("utf-8", errors="replace")

        # Send the output to the connected handler.
        self.progress_output_received.emit(output)

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

    def is_running(self):
        # Check whether FFmpeg is currently running.
        return (
            self.process.state()
            != QProcess.ProcessState.NotRunning
        )