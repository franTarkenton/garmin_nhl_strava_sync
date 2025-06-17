import logging

import nhlpy

LOGGER = logging.getLogger(__name__)


class NHL:
    def __init__(self):
        self.nhl_client = nhlpy.NHLClient()

    def get_schedule(self, target_date="2025-04-01"):
        # target_date = "YYYY-MM-DD"  # Replace with your specific date
        schedule = self.nhl_client.schedule.get_schedule(date=target_date)
        # if self.has_habs_game(schedule):
        #     score = self.getScore(schedule)
        #     LOGGER.debug("schedule for %s is %s", target_date, schedule)
        return schedule

    def has_habs_game(self, schedule):
        for game in schedule.games:
            if game["awayTeam"]["abbrev"] == "MTL":
                return True
            if game["homeTeam"]["abbrev"] == "MTL":
                return True

    def get_score_label(self, target_date):
        schedule = self.get_schedule(target_date=target_date)
        for game in schedule["games"]:
            home_team = game["awayTeam"]
            away_team = game["homeTeam"]
            if away_team["abbrev"] == "MTL" or home_team["abbrev"] == "MTL":
                label = None
                if (
                    "abbrev" in away_team
                    and "score" in away_team
                    and "abbrev" in home_team
                    and "score" in home_team
                ):
                    label = f"{away_team['abbrev']} {away_team['score']} - {home_team['abbrev']} {home_team['score']}"
                LOGGER.info("score: %s", label)
                return label
        return None
