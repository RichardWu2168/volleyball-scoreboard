import json

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

    validate_game_data(saved_data)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(saved_data, file, indent=4)

def load_game_file(file_path):
    # Load and validate game data from a JSON file.
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            saved_data = json.load(file)
        validate_game_data(saved_data)
    except RecursionError as error:
        raise ValueError("The game file contains too many nested JSON values.") from error
    return saved_data


def validate_game_data(saved_data):
    """Check the project format used by both save and load."""
    if not isinstance(saved_data, dict):
        raise ValueError("The game must be a JSON object.")

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
            or not 0 <= value <= 99
        ):
            raise ValueError(
                f"'{field}' must be an integer between 0 and 99."
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
            or event["time"] < 0
            or event["time"] > 2_147_483_647
            or (isinstance(event["time"], float) and not event["time"].is_integer())
        ):
            raise ValueError(
                f"Event {index + 1} has an invalid timestamp."
            )

        event["time"] = int(event["time"])

        for score_key in ("score_a", "score_b"):
            score = event[score_key]

            if (
                not isinstance(score, int)
                or isinstance(score, bool)
                or score < 0
            ):
                raise ValueError(
                    f"Event {index + 1} has an invalid {score_key}."
                )

    # A game with events begins with a single starting score at time zero.
    start_event_count = sum(
        1 for event in saved_data["events"]
        if event["team"] == "START"
    )

    if saved_data["events"] and start_event_count != 1:
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

    if sorted_events and (
        sorted_events[0]["team"] != "START" or sorted_events[0]["time"] != 0
    ):
        raise ValueError("The START event must be first and have timestamp 0.")

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
    if "\x00" in saved_data["video_file"]:
        raise ValueError("'video_file' must not contain a null character.")

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

    for field in ("video_file", "team_a_name", "team_b_name"):
        try:
            saved_data[field].encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError(f"'{field}' contains invalid Unicode text.") from error

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
