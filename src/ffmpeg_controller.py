import logging
import ctypes
import sys

from PySide6.QtCore import QObject, QProcess, Signal

logger = logging.getLogger(__name__)

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

        # Track whether this controller has requested that Windows
        # prevent the computer from entering sleep mode.
        self.sleep_prevention_active = False

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

    def prevent_system_sleep(self):
        # This feature applies only to Windows.
        if sys.platform != "win32":
            return

        # Keep Windows awake while allowing the display to turn off.
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001

        result = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )

        if result:
            self.sleep_prevention_active = True

    def restore_system_sleep(self):
        # Do nothing if sleep prevention was not activated.
        if not self.sleep_prevention_active:
            return

        try:
            if sys.platform == "win32":
                # Restore the normal Windows power behavior.
                ES_CONTINUOUS = 0x80000000

                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS
                )
        finally:
            self.sleep_prevention_active = False

    def _handle_process_error(self, error):
        # Release the sleep prevention request if FFmpeg cannot start.
        if error == QProcess.ProcessError.FailedToStart:
            logger.error(
                "FFmpeg failed to start. Check whether FFmpeg is installed "
                "and accessible."
            )
            self.restore_system_sleep()

        # Forward the process error through the controller's signal.
        self.process_error_occurred.emit(error)

    def get_error_message(self, error):
        # Map common process errors to helpful messages.
        error_messages = {
            QProcess.ProcessError.FailedToStart: (
                "Could not start FFmpeg. Please check that FFmpeg "
                "is installed and accessible from your PATH."
            ),
            QProcess.ProcessError.Crashed: (
                "FFmpeg crashed while generating the video."
            ),
            QProcess.ProcessError.Timedout: (
                "The FFmpeg process timed out."
            ),
            QProcess.ProcessError.ReadError: (
                "An error occurred while reading FFmpeg output."
            ),
            QProcess.ProcessError.WriteError: (
                "An error occurred while writing to FFmpeg."
            ),
        }

        # Get the corresponding message, if available.
        message = error_messages.get(
            error,
            "An unknown FFmpeg process error occurred."
        )

        # Log the technical error.
        logger.error(
            "FFmpeg process error: %s; message: %s",
            error,
            message,
        )

        return message

    def _handle_process_finished(self, exit_code, exit_status):
        # Restore normal power behavior when FFmpeg finishes,
        # fails, or is terminated.
        self.restore_system_sleep()

        # Forward the process completion through the controller's signal.
        self.process_finished.emit(exit_code, exit_status)

    def start(self, command):
        logger.info("Starting FFmpeg process.")
        # Do not start FFmpeg if it is already running.
        if self.is_running():
            return False

        # Clear errors from the previous generation.
        self.error_output = ""

        # Prevent sleep before starting FFmpeg.
        self.prevent_system_sleep()

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
            logger.info("Terminating FFmpeg process.")
            self.process.kill()

    def is_running(self):
        # Check whether FFmpeg is currently running.
        return (
            self.process.state()
            != QProcess.ProcessState.NotRunning
        )
