import json
import math

def save_game_file(file_path, game_data):
    # Save game data to a JSON file.
    saved_data = {
        "video_file": game_data.video_file,
        "team_a_name": game_data.team_a_name,
        "team_b_name": game_data.team_b_name,
        "team_a_sets_won": game_data.team_a_sets_won,
        "team_b_sets_won": game_data.team_b_sets_won,
        "starting_score_a": game_data.starting_score_a,
        "starting_score_b": game_data.starting_score_b,
        "events": game_data.events,
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(saved_data, file, indent=4)

def load_game_file(file_path):
    # Load and validate game data from a JSON file.
    with open(file_path, "r", encoding="utf-8") as file:
        saved_data = json.load(file)

    required_fields = [
        "video_file",
        "team_a_name",
        "team_b_name",
        "starting_score_a",
        "starting_score_b",
        "events",
    ]

    for field in required_fields:
        if field not in saved_data:
            raise ValueError(
                f"Required field '{field}' is missing."
            )

    if not isinstance(saved_data["events"], list):
        raise ValueError("'events' must be a list.")

    # Validate starting scores before checking event consistency.
    for field in ("starting_score_a", "starting_score_b"):
        value = saved_data[field]

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(
                f"'{field}' must be a non-negative integer."
            )

    # Validate each event's structure and values first.
    for index, event in enumerate(saved_data["events"]):
        if not isinstance(event, dict):
            raise ValueError(
                f"Event {index + 1} must be an object."
            )

        for field in ("time", "team", "score_a", "score_b"):
            if field not in event:
                raise ValueError(
                    f"Event {index + 1} is missing '{field}'."
                )

        if event["team"] not in ("START", "A", "B"):
            raise ValueError(
                f"Event {index + 1} has an invalid team."
            )

        if (
            not isinstance(event["time"], (int, float))
            or isinstance(event["time"], bool)
            or not math.isfinite(event["time"])
            or event["time"] < 0
        ):
            raise ValueError(
                f"Event {index + 1} has an invalid timestamp."
            )

        for score_key in ("score_a", "score_b"):
            score = event[score_key]

            if (
                not isinstance(score, int)
                or isinstance(score, bool)
                or score < 0
            ):
                raise ValueError(
                    f"Event {index + 1} has an invalid {score_key}: {event[score_key]}."
                )

    # A saved game must contain exactly one START event.
    start_event_count = sum(
        1 for event in saved_data["events"]
        if event["team"] == "START"
    )

    if start_event_count != 1:
        raise ValueError(
            "The game must contain exactly one START event."
        )

    # Validate event scores in chronological order.
    expected_score_a = saved_data["starting_score_a"]
    expected_score_b = saved_data["starting_score_b"]

    sorted_events = sorted(
        saved_data["events"],
        key=lambda event: event["time"]
    )

    for index, event in enumerate(sorted_events):
        if event["team"] == "START":
            expected_score_a = saved_data["starting_score_a"]
            expected_score_b = saved_data["starting_score_b"]

        elif event["team"] == "A":
            expected_score_a += 1

        elif event["team"] == "B":
            expected_score_b += 1

        if (
            event["score_a"] != expected_score_a
            or event["score_b"] != expected_score_b
        ):
            raise ValueError(
                f"Event {index + 1} has scores that do not "
                "match the event history."
            )

    if not isinstance(saved_data["video_file"], str):
        raise ValueError("'video_file' must be a string.")

    if (
        not isinstance(saved_data["team_a_name"], str)
        or not saved_data["team_a_name"].strip()
    ):
        raise ValueError("'team_a_name' must be a non-empty string.")

    if (
        not isinstance(saved_data["team_b_name"], str)
        or not saved_data["team_b_name"].strip()
    ):
        raise ValueError("'team_b_name' must be a non-empty string.")

    for field in ("team_a_sets_won", "team_b_sets_won"):
        value = saved_data.get(field, 0)

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            or value > 9
        ):
            raise ValueError(
                f"'{field}' must be an integer between 0 and 9."
            )

    return saved_data
