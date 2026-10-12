class Scoreboard:
    #"""Handles score calculations based on game data."""

    def __init__(self, game_data):
        self.game_data = game_data

    def recalculate_scores(self):
        #"""Recalculate and update the scores stored in each event."""
        score_a = self.game_data.starting_score_a
        score_b = self.game_data.starting_score_b

        self.game_data.events.sort(key=lambda event: event["time"])

        for event in self.game_data.events:
            if event["team"] == "START":
                score_a = self.game_data.starting_score_a
                score_b = self.game_data.starting_score_b

            elif event["team"] == "A":
                score_a += 1

            elif event["team"] == "B":
                score_b += 1

            event["score_a"] = score_a
            event["score_b"] = score_b

    def get_score_at_time(self, time_ms):
        #"""Return both teams' scores at a given video timestamp."""
        score_a = self.game_data.starting_score_a
        score_b = self.game_data.starting_score_b

        for event in sorted(
            self.game_data.events,
            key=lambda event: event["time"]
        ):
            if event["time"] > time_ms:
                break

            if event["team"] == "START":
                score_a = self.game_data.starting_score_a
                score_b = self.game_data.starting_score_b

            elif event["team"] == "A":
                score_a += 1

            elif event["team"] == "B":
                score_b += 1

        return score_a, score_b
