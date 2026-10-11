from PySide6.QtCore import QObject, QProcess, Signal

class FFmpegController(QObject):
    # Signals that MainWindow can connect to.
    progress_output_received = Signal()
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
            self.progress_output_received
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

    def _handle_process_finished(self, exit_code, exit_status):
        # Forward the process completion through the controller's signal.
        self.process_finished.emit(exit_code, exit_status)

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
