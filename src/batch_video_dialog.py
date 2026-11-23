import logging
import math
import os
import re
import shutil
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ffmpeg_controller import FFmpegController
from game import GameData
from project import load_game_file
from video_export import VideoExport
from video_generator import VideoGenerator
from video_progress import VideoProgress

logger = logging.getLogger(__name__)


def path_key(path):
    return os.path.normcase(os.path.realpath(path))


@dataclass
class BatchJob:
    project: Path
    output: Path
    game: GameData | None = None
    status: str = "Ready"
    detail: str = ""
    elapsed_seconds: int | None = None


class BatchVideoDialog(QDialog):
    running_changed = Signal(bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Batch Generate Videos")
        self.resize(1200, 600)

        self.projects = []
        self.output_folder = None
        self.jobs = []
        self.running = False
        self.cancelled = False
        self.pending: Iterator[int] = iter(())
        self.active_row = None
        self.export = None
        self.quality = None
        self.nvidia_codec = None
        self.bitrate_mbps = None
        self.allow_overwrite = False
        self.duration_seconds = 0
        self.probe_timed_out = False

        self.ffmpeg = FFmpegController(manage_sleep=False)
        self.ffmpeg.progress_output_received.connect(self.update_progress)
        self.ffmpeg.process_finished.connect(self.export_finished)
        self.ffmpeg.process_error_occurred.connect(self.export_error)

        self.probe = QProcess(self)
        self.probe.finished.connect(self.probe_finished)
        self.probe.errorOccurred.connect(self.probe_error)
        self.probe_timer = QTimer(self)
        self.probe_timer.setSingleShot(True)
        self.probe_timer.timeout.connect(self.probe_timeout)

        self.create_widgets()

    def create_widgets(self):
        self.add_button = QPushButton("Add JSON Files…")
        self.remove_button = QPushButton("Remove Selected")
        self.folder_button = QPushButton("Choose Output Folder…")
        self.overwrite_box = QCheckBox("Overwrite existing outputs")
        self.folder_label = QLabel("Output folder: select a JSON file to begin")
        self.folder_label.setWordWrap(True)
        self.quality_label = QLabel()
        self.encoder_label = QLabel()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["JSON file", "Source video", "Output video", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.elapsed_label = QLabel()
        self.progress = VideoProgress(self.elapsed_label)
        self.progress.reset()
        self.start_button = QPushButton("Start Batch")
        self.cancel_button = QPushButton("Cancel Batch")
        self.close_button = QPushButton("Close")
        self.start_button.setAutoDefault(False)

        selection = QGridLayout()
        for column, button in enumerate((self.add_button, self.remove_button, self.folder_button)):
            selection.addWidget(button, 0, column)
            selection.setColumnStretch(column, 1)
        selection.addWidget(self.overwrite_box, 0, 3)
        selection.addWidget(self.folder_label, 1, 0, 1, 2)
        selection.addWidget(self.encoder_label, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        selection.addWidget(self.quality_label, 1, 3, alignment=Qt.AlignmentFlag.AlignTop)
        actions = QHBoxLayout()
        actions.addStretch()
        for widget in (self.start_button, self.cancel_button, self.close_button):
            actions.addWidget(widget)
        layout = QVBoxLayout(self)
        layout.addLayout(selection)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.elapsed_label)
        layout.addLayout(actions)

        self.add_button.clicked.connect(self.add_projects)
        self.remove_button.clicked.connect(self.remove_projects)
        self.folder_button.clicked.connect(self.choose_folder)
        self.overwrite_box.toggled.connect(self.preview)
        self.start_button.clicked.connect(self.start_batch)
        self.cancel_button.clicked.connect(self.cancel_batch)
        self.close_button.clicked.connect(self.reject)
        self.parent().video_quality_combo.currentTextChanged.connect(self.update_export_labels)
        self.parent().video_encoder_combo.currentTextChanged.connect(self.update_export_labels)
        self.parent().target_bitrate_box.toggled.connect(self.update_export_labels)
        self.parent().target_bitrate_spin.valueChanged.connect(self.update_export_labels)
        self.update_export_labels()
        self.preview()

    def update_export_labels(self):
        if not self.running:
            bitrate_mbps = self.parent().export_bitrate_mbps()
            if bitrate_mbps is None:
                quality_name = self.parent().video_quality_combo.currentText()
                self.quality_label.setText(f"Video Quality: {quality_name}")
            else:
                self.quality_label.setText(f"Target Bitrate: {bitrate_mbps} Mbps")
            encoder_name = self.parent().video_encoder_combo.currentText()
            self.encoder_label.setText(f"Export Encoder: {encoder_name}")

    def add_projects(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Game Files", str(self.output_folder or ""), "Game Files (*.json)"
        )
        known = {path_key(path) for path in self.projects}
        for name in paths:
            path = Path(name)
            key = path_key(path)
            if key not in known:
                self.projects.append(path)
                known.add(key)
        if self.output_folder is None and self.projects:
            self.output_folder = self.projects[0].parent
        if paths:
            self.preview()

    def remove_projects(self):
        selected = {item.row() for item in self.table.selectionModel().selectedRows()}
        self.projects = [path for row, path in enumerate(self.projects) if row not in selected]
        self.preview()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Output Folder", str(self.output_folder or "")
        )
        if folder:
            self.output_folder = Path(folder)
            self.preview()

    def preview(self):
        self.jobs = []
        self.progress_bar.setVisible(False)
        self.progress.reset()
        if self.output_folder is not None:
            self.folder_label.setText(f"Output folder: {self.output_folder}")
            self.jobs = [
                BatchJob(path, self.output_folder / path.with_suffix(".mp4").name)
                for path in self.projects
            ]

        source_keys = set()
        for job in self.jobs:
            try:
                data = load_game_file(job.project)
                if not data["video_file"]:
                    raise ValueError("No source video is recorded in the project.")
                source = job.project.parent / data["video_file"]
                data["video_file"] = str(source.absolute())
                job.game = GameData(**{
                    key: data[key] for key in vars(GameData()) if key in data
                })
                source_keys.add(path_key(source))
                if not source.is_file():
                    raise ValueError("Source video is missing.")
            except (OSError, ValueError, RecursionError) as error:
                job.status = "Skipped"
                job.detail = str(error)

        output_counts = Counter(path_key(job.output) for job in self.jobs)
        for job in self.jobs:
            if job.status != "Ready":
                continue
            key = path_key(job.output)
            if key in source_keys:
                job.detail = "Output matches a source video in this batch."
            elif output_counts[key] > 1:
                job.detail = "Another JSON file has the same output name."
            elif job.output.is_dir():
                job.detail = "The output path is a directory."
            elif os.path.lexists(job.output) and not self.overwrite_box.isChecked():
                job.detail = "Output already exists."
            if job.detail:
                job.status = "Skipped"

        self.table.setRowCount(len(self.jobs))
        for row in range(len(self.jobs)):
            self.show_row(row)
        ready = sum(job.status == "Ready" for job in self.jobs)
        self.start_button.setText(f"Start Batch ({ready} ready)")
        self.summary_label.setText(f"{ready} ready, {len(self.jobs) - ready} skipped")
        self.update_controls()

    def show_row(self, row):
        job = self.jobs[row]
        source = Path(job.game.video_file) if job.game is not None else None
        status_text = job.status
        if job.elapsed_seconds is not None:
            minutes, seconds = divmod(job.elapsed_seconds, 60)
            status_text = f"{status_text} ({minutes:02d}:{seconds:02d})"
        values = (
            (job.project.name, str(job.project)),
            (source.name if source else "", str(source) if source else ""),
            (job.output.name, str(job.output)),
            (f"{status_text} — {job.detail}" if job.detail else status_text, job.detail),
        )
        for column, (label, tooltip) in enumerate(values):
            item = QTableWidgetItem(label)
            item.setToolTip(tooltip)
            self.table.setItem(row, column, item)
        self.table.resizeRowToContents(row)

    def update_controls(self):
        for widget in (self.add_button, self.remove_button, self.folder_button, self.overwrite_box,
                       self.close_button):
            widget.setEnabled(not self.running)
        can_start = any(job.status in ("Ready", "Cancelled") for job in self.jobs)
        self.start_button.setEnabled(not self.running and can_start)
        self.cancel_button.setEnabled(self.running and not self.cancelled)

    def start_batch(self):
        if self.running or self.parent().ffmpeg_controller.is_running():
            self.summary_label.setText("Wait for the current export to finish.")
            return
        self.preview()
        pending = [row for row, job in enumerate(self.jobs) if job.status == "Ready"]
        if not pending:
            return
        self.ffmpeg_program = shutil.which("ffmpeg")
        if self.ffmpeg_program is None:
            self.summary_label.setText("Install FFmpeg and make it available on PATH.")
            return

        self.ffprobe_program = shutil.which("ffprobe")
        if self.ffprobe_program is None:
            logger.info("FFprobe is unavailable. Batch video inspection will use FFmpeg.")

        self.quality = self.parent().video_quality_combo.currentData()
        self.nvidia_codec = self.parent().video_encoder_combo.currentData()
        self.bitrate_mbps = self.parent().export_bitrate_mbps()
        self.update_export_labels()
        self.allow_overwrite = self.overwrite_box.isChecked()
        self.pending = iter(pending)
        self.running = True
        self.cancelled = False
        self.ffmpeg.prevent_system_sleep()
        self.running_changed.emit(True)
        self.update_controls()
        self.next_job()

    def next_job(self):
        self.active_row = next(self.pending, None) if not self.cancelled else None
        if self.active_row is None:
            self.finish_batch()
            return

        row = self.active_row
        job = self.jobs[row]
        job.status = "Probing"
        self.show_row(row)
        self.table.scrollToItem(self.table.item(row, 0))
        self.summary_label.setText(f"File {row + 1} of {len(self.jobs)} — {job.project.name}")
        self.progress.reset()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Reading video…")
        self.progress_bar.setVisible(True)
        self.start_probe(use_ffprobe=self.ffprobe_program is not None)

    def start_probe(self, *, use_ffprobe):
        if self.cancelled:
            self.complete_job("Cancelled")
            return

        source = self.jobs[self.active_row].game.video_file
        self.probing_with_ffprobe = use_ffprobe
        self.probe_timed_out = False
        self.probe_timer.start(30_000)
        if use_ffprobe:
            self.probe.start(self.ffprobe_program, [
                "-v", "error", "-select_streams", "V:0",
                "-show_entries", "stream=codec_type:format=duration",
                "-of", "default=noprint_wrappers=1", source,
            ])
        else:
            # Read the input metadata without encoding or writing a video.
            self.probe.start(self.ffmpeg_program, [
                "-hide_banner", "-nostdin", "-nostats", "-loglevel", "info",
                "-i", source, "-map", "0:V:0", "-frames:v", "0",
                "-c:v", "copy", "-f", "null", "-",
            ])

    def retry_probe_with_ffmpeg(self, detail):
        logger.info("FFprobe inspection failed. Trying FFmpeg. %s", detail)
        QTimer.singleShot(0, lambda: self.start_probe(use_ffprobe=False))

    def probe_timeout(self):
        self.probe_timed_out = True
        self.probe.kill()

    def probe_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.probe_timer.stop()
            if self.cancelled:
                self.complete_job("Cancelled")
            elif self.probing_with_ffprobe:
                self.ffprobe_program = None
                self.retry_probe_with_ffmpeg(self.probe.errorString())
            else:
                self.complete_job("Failed", self.probe.errorString())

    def probe_finished(self, exit_code, exit_status):
        self.probe_timer.stop()
        if self.cancelled:
            self.complete_job("Cancelled")
            return
        if self.probe_timed_out:
            self.complete_job("Failed", "Video inspection timed out.")
            return
        stderr = bytes(self.probe.readAllStandardError()).decode("utf-8", errors="replace").strip()
        if exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            if self.probing_with_ffprobe:
                self.retry_probe_with_ffmpeg(stderr or f"FFprobe exited with code {exit_code}.")
            else:
                detail = " ".join(stderr.splitlines()[-3:])
                self.complete_job("Failed", detail or "FFmpeg could not open the source video.")
            return

        duration = self.read_probe_duration(stderr)
        if not math.isfinite(duration) or duration <= 0:
            self.complete_job("Failed", "No video stream with an available duration.")
            return

        self.start_export(duration)

    def read_probe_duration(self, stderr):
        if self.probing_with_ffprobe:
            output = bytes(self.probe.readAllStandardOutput()).decode("utf-8", errors="replace")
            metadata = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
            if metadata.get("codec_type") == "video":
                try:
                    return float(metadata["duration"])
                except (KeyError, ValueError):
                    pass
        else:
            match = re.search(r"^\s*Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", stderr, re.MULTILINE)
            if match:
                hours, minutes, seconds = match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return 0

    def start_export(self, duration):

        job = self.jobs[self.active_row]
        try:
            self.export = VideoExport(job.output)
            command = self.export.prepare(
                VideoGenerator(job.game), round(duration * 1000), self.quality,
                nvidia_codec=self.nvidia_codec, bitrate_mbps=self.bitrate_mbps,
            )
        except (OSError, ValueError, OverflowError) as error:
            self.complete_job("Failed", str(error))
            return

        job.status = "Generating"
        self.show_row(self.active_row)
        self.duration_seconds = duration
        self.progress_bar.setFormat("Generating video: 0%")
        self.progress.start()
        if not self.ffmpeg.start(command, program=self.ffmpeg_program):
            self.complete_job("Failed", "Could not start FFmpeg.")

    def update_progress(self, output):
        self.progress.update_progress(output, self.duration_seconds, self.progress_bar)

    def export_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.complete_job("Failed", self.ffmpeg.get_error_message(error))

    def export_finished(self, exit_code, exit_status):
        if self.cancelled:
            self.complete_job("Cancelled")
        elif exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            self.complete_job("Failed", self.ffmpeg.error_output.strip() or f"FFmpeg exited with code {exit_code}.")
        else:
            try:
                self.export.publish(overwrite=self.allow_overwrite)
            except FileExistsError:
                self.complete_job("Skipped", "Output appeared during processing.")
            except OSError as error:
                self.complete_job("Failed", str(error))
            else:
                self.complete_job("Completed")

    def complete_job(self, status, detail=""):
        job = self.jobs[self.active_row]
        job.status = status
        if status == "Completed" and self.progress.start_time is not None:
            job.elapsed_seconds = self.progress.get_elapsed_seconds()
        # Keep the queue readable and retain full diagnostics in the log.
        job.detail = " ".join(detail.strip().splitlines())[:300]
        logger.info("Batch export %s: %s %s", status, job.project, detail)
        self.show_row(self.active_row)
        self.progress.stop_timer()
        if self.export is not None:
            self.export.cleanup()
            self.export = None
        self.active_row = None
        QTimer.singleShot(0, self.next_job)

    def cancel_batch(self):
        self.cancelled = True
        self.cancel_button.setEnabled(False)
        self.summary_label.setText("Cancelling batch…")
        if self.probe.state() != QProcess.ProcessState.NotRunning:
            self.probe.kill()
        else:
            self.ffmpeg.kill()

    def finish_batch(self):
        for row, job in enumerate(self.jobs):
            if job.status == "Ready":
                job.status = "Cancelled"
                self.show_row(row)
        counts = Counter(job.status for job in self.jobs)
        if counts["Cancelled"]:
            self.start_button.setText("Restart Batch")
        self.summary_label.setText(
            f"{counts['Completed']} completed, {counts['Failed']} failed, "
            f"{counts['Skipped']} skipped, {counts['Cancelled']} cancelled"
        )
        self.progress_bar.setVisible(False)
        self.progress.reset()
        self.ffmpeg.restore_system_sleep()
        self.running = False
        self.update_export_labels()
        self.running_changed.emit(False)
        self.update_controls()

    def reject(self):
        if not self.running:
            super().reject()

    def closeEvent(self, event):
        if self.running:
            event.ignore()
        else:
            super().closeEvent(event)
