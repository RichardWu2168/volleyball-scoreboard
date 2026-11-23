import os
from pathlib import Path


class VideoGenerator:
    # Builds the scoreboard timeline and FFmpeg overlay filter.

    def __init__(self, game_data):
        self.game_data = game_data

    def build_score_timeline(self, video_duration_ms):
        timeline = []

        current_time = 0
        current_score_a = self.game_data.starting_score_a
        current_score_b = self.game_data.starting_score_b

        for event in sorted(
            self.game_data.events,
            key=lambda event: event["time"]
        ):
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

        # Escape drawtext option syntax, then quote it for the filtergraph.
        text = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        return text.replace("'", "'\\''")

    def build_ffmpeg_filter(self, timeline):
        filters = []

        team_a_name = self.game_data.team_a_name
        team_b_name = self.game_data.team_b_name

        sets_a = self.game_data.team_a_sets_won
        sets_b = self.game_data.team_b_sets_won
        set_number = sets_a + sets_b + 1

        font_option = ""
        windows_directory = os.environ.get("SystemRoot")
        if os.name == "nt" and windows_directory:
            font_file = Path(windows_directory) / "Fonts" / "segoeui.ttf"
            if font_file.is_file():
                font_path = self.escape_ffmpeg_text(font_file.as_posix())
                font_option = f"fontfile='{font_path}':"

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
                "expansion=none:"
                f"{font_option}"
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
        filter_file,
        video_quality,
        *,
        nvidia_codec=None,
        bitrate_mbps=None,
    ):
        if nvidia_codec:
            # Leave decoded frames in system memory for the drawtext filter.
            decoder_args = ["-hwaccel", "cuda"]
            encoder_args = ["-c:v", f"{nvidia_codec}_nvenc", "-preset", "p4", "-rc", "vbr"]
            if bitrate_mbps is None:
                encoder_args.extend(["-cq", str(video_quality), "-b:v", "0"])
            else:
                encoder_args.extend(["-b:v", f"{bitrate_mbps}M"])
            if nvidia_codec == "hevc":
                encoder_args.extend(["-tag:v", "hvc1"])
        else:
            decoder_args = []
            encoder_args = [
                "-c:v", "libx264", "-preset", "medium", "-crf", str(video_quality),
            ]

        return [
            "-nostdin",
            "-y",
            *decoder_args,
            "-i",
            self.game_data.video_file,
            "-/filter:v",
            str(filter_file),
            "-pix_fmt",
            "yuv420p",
            *encoder_args,
            "-c:a",
            "copy",
            "-progress",
            "pipe:1",
            "-nostats",
            output_file
        ]
