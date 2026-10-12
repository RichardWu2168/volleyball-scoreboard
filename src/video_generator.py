class VideoGenerator:
    #"""Builds the scoreboard timeline and FFmpeg overlay filter."""

    def __init__(self, game_data):
        self.game_data = game_data

    def build_score_timeline(self, video_duration_ms):
        timeline = []

        current_time = 0
        current_score_a = self.game_data.starting_score_a
        current_score_b = self.game_data.starting_score_b

        for event in self.game_data.events:
            if event["team"] == "START":
                current_score_a = event["score_a"]
                current_score_b = event["score_b"]
                continue

            timeline.append({
                "start_time": current_time,
                "end_time": event["time"],
                "score_a": current_score_a,
                "score_b": current_score_b,
            })

            current_time = event["time"]
            current_score_a = event["score_a"]
            current_score_b = event["score_b"]

        # Last score continues until the end of the video.
        timeline.append({
            "start_time": current_time,
            "end_time": video_duration_ms,
            "score_a": current_score_a,
            "score_b": current_score_b,
        })

        return timeline

    @staticmethod
    def escape_ffmpeg_text(text):
        """Escape text for use in FFmpeg's drawtext filter."""
        text = str(text)

        # Escape backslashes first.
        text = text.replace("\\", "\\\\")
        text = text.replace(":", "\\:")
        text = text.replace(",", "\\,")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        text = text.replace("%", "\\%")

        # Escape apostrophes for FFmpeg filter syntax.
        text = text.replace("'", "'\\''")

        return text

    def build_ffmpeg_filter(self, timeline):
        filters = []

        team_a_name = self.game_data.team_a_name
        team_b_name = self.game_data.team_b_name

        sets_a = self.game_data.team_a_sets_won
        sets_b = self.game_data.team_b_sets_won
        set_number = sets_a + sets_b + 1

        for i, period in enumerate(timeline):
            text = (
                f"Set {set_number}    "
                f"({sets_a}) {self.escape_ffmpeg_text(team_a_name)}    "
                f"{period['score_a']} - {period['score_b']}    "
                f"{self.escape_ffmpeg_text(team_b_name)} ({sets_b})"
            )

            start = period["start_time"] / 1000

            if i == len(timeline) - 1:
                enable = f"gte(t,{start:.3f})"
            else:
                end = period["end_time"] / 1000
                enable = f"gte(t,{start:.3f})*lt(t,{end:.3f})"

            filters.append(
                "drawtext="
                f"text='{text}':"
                "fontcolor=white:"
                "fontsize=72:"
                "box=1:"
                "boxcolor=black@0.6:"
                "boxborderw=20:"
                "x=(w-text_w)/2:"
                "y=h-text_h-30:"
                f"enable='{enable}'"
            )

        return ",".join(filters)

    def build_ffmpeg_command(
        self,
        output_file,
        ffmpeg_filter,
        video_quality
    ):
        #"""Build the FFmpeg arguments for video generation."""
        return [
            "-y",
            "-nostats",
            "-i",
            self.game_data.video_file,
            "-vf",
            ffmpeg_filter,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            str(video_quality),
            "-c:a",
            "copy",
            "-progress",
            "pipe:1",
            "-nostats",
            output_file
        ]
