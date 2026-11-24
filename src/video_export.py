import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from video_generator import describe_export_settings

logger = logging.getLogger(__name__)


class VideoExport:
    """Stage FFmpeg files on the destination volume until the export succeeds."""

    def __init__(self, output_file):
        self.destination = Path(output_file)
        self.directory = TemporaryDirectory(
            prefix=".volleyball-scoreboard-", dir=self.destination.absolute().parent
        )
        work_directory = Path(self.directory.name)
        self.filter_file = work_directory / "scoreboard.filter"
        self.video_file = work_directory / "scored.mp4"

    def prepare(self, generator, duration_ms, quality, *, nvidia_codec=None, bitrate_mbps=None):
        timeline = generator.build_score_timeline(duration_ms)
        self.filter_file.write_text(generator.build_ffmpeg_filter(timeline), encoding="utf-8")
        settings = describe_export_settings(
            quality, nvidia_codec=nvidia_codec, bitrate_mbps=bitrate_mbps
        )
        logger.info("Export settings for %s: %s", self.destination, settings)
        return generator.build_ffmpeg_command(
            str(self.video_file), self.filter_file, quality,
            nvidia_codec=nvidia_codec, bitrate_mbps=bitrate_mbps,
        )

    def publish(self, *, overwrite):
        if self.video_file.stat().st_size == 0:
            raise OSError("FFmpeg produced an empty video file.")
        if overwrite:
            self.video_file.replace(self.destination)
        elif os.name == "nt":
            # On Windows rename fails if another process created the destination.
            self.video_file.rename(self.destination)
        else:
            # A hard link also fails atomically if the destination exists.
            os.link(self.video_file, self.destination)

    def cleanup(self):
        try:
            self.directory.cleanup()
        except OSError:
            logger.exception("Could not clean up temporary export files.")
