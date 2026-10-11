class GameData:
    def __init__(
        self,
        video_file="",
        team_a_name="Team A",
        team_b_name="Team B",
        team_a_sets_won=0,
        team_b_sets_won=0,
        starting_score_a=0,
        starting_score_b=0,
        events=None,
    ):
        self.video_file = video_file
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        self.team_a_sets_won = team_a_sets_won
        self.team_b_sets_won = team_b_sets_won
        self.starting_score_a = starting_score_a
        self.starting_score_b = starting_score_b
        self.events = events if events is not None else []
