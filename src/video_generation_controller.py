import logging

logger = logging.getLogger(__name__)

class VideoGenerationController:
    def __init__(
        self,
        media_player,
        video_generator,
        video_progress,
        ffmpeg_controller,
        progress_bar,
        status_label,
        generate_button,
        cancel_button,
    ):
        # Store the objects needed to coordinate video generation.
        self.media_player = media_player
        self.video_generator = video_generator
        self.video_progress = video_progress
        self.ffmpeg_controller = ffmpeg_controller

        # Store the UI elements that reflect generation status.
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.generate_button = generate_button
        self.cancel_button = cancel_button

        # Track the current generation state.
        self.current_output_file = None
        self.video_duration_seconds = 0
        self.generation_cancelled = False

    def start(self, output_file, quality):
        logger.info(
            "Starting video generation. Output: %s, quality: %s",
            output_file,
            quality,
        )
        # Get the video duration in seconds.
        duration_ms = self.media_player.duration()
        video_duration_seconds = duration_ms / 1000

        if video_duration_seconds <= 0:
            logger.warning(
                "Cannot start video generation: video duration is unavailable."
            )
            return False, (
                "The video duration is not available. "
                "Please wait until the video loads."
            )

        # Build the timeline and FFmpeg filter.
        timeline = self.video_generator.build_score_timeline(duration_ms)
        ffmpeg_filter = self.video_generator.build_ffmpeg_filter(timeline)

        # Prepare the FFmpeg command.
        command = self.video_generator.build_ffmpeg_command(
            output_file,
            ffmpeg_filter,
            quality,
        )

        # Reset the generation state.
        self.current_output_file = output_file
        self.video_duration_seconds = video_duration_seconds
        self.generation_cancelled = False

        # Reset the progress tracking state.
        self.video_progress.reset()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating video: 0%")
        self.progress_bar.setVisible(True)
        self.status_label.setText("Status: Generating video...")

        # Start the elapsed-time timer.
        self.video_progress.start()

        # Update the generation buttons.
        self.generate_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # Start FFmpeg asynchronously.
        started = self.ffmpeg_controller.start(command)

        if not started:
            logger.warning(
                "Video generation was not started because FFmpeg is already running."
            )
            self.video_progress.stop_timer()
            self.generate_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.status_label.setText(
                "Status: Video generation failed"
            )
            self.progress_bar.setFormat("Generation failed")

            return False, "FFmpeg is already running."

        return True, None
