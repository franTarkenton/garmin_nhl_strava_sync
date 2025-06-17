import datetime
import json
import logging
import pathlib
import sys
import zoneinfo

import dateutil

LOGGER = logging.getLogger(__name__)


class ActivityCompare:
    def __init__(self, garmin_activities, strava_activites):
        self.garmin_activities = garmin_activities
        self.strava_activites = strava_activites

        self.strava_idx = {}
        self.garmin_idx = {}

        self.index_garmin()
        self.index_strava()

    def get_activities_to_upload(self):
        """
        Does a comparison between garmin and strava activities and
        Identifies activities in the garmin list that do not exist
        in the strava list.  Uses start_time to build a bridge between
        the two sets.
        """
        # looking for garmins not in strava
        missing_keys = list(set(self.garmin_idx.keys()) - set(self.strava_idx.keys()))
        missing_keys.sort()
        LOGGER.debug("missing keys (first 3):%s ...", ",".join(missing_keys[0:4]))
        garmin_to_upload = []
        for missing_key in missing_keys:
            garmin_to_upload.append(self.garmin_idx[missing_key])
        return garmin_to_upload

    def index_strava(self):
        for act in self.strava_activites:
            start_date = act["start_date"]
            # LOGGER.debug("start_date, %s, %s", start_date, type(start_date))
            utc_dt2 = dateutil.parser.isoparse(start_date)
            pacific_dt = utc_dt2.astimezone(zoneinfo.ZoneInfo("America/Los_Angeles"))
            pacific_str = pacific_dt.strftime("%Y-%m-%d %H:%M:%S")
            # LOGGER.debug("pacific_str: %s", pacific_str)
            self.strava_idx[pacific_str] = act

    def index_garmin(self):
        for act in self.garmin_activities["activityList"]:
            start_date = act["startTimeGMT"]

            dt = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")

            # Mark as UTC
            utc_dt = dt.replace(tzinfo=datetime.timezone.utc)

            pacific_dt = utc_dt.astimezone(zoneinfo.ZoneInfo("America/Los_Angeles"))
            pacific_str = pacific_dt.strftime("%Y-%m-%d %H:%M:%S")
            # LOGGER.debug("pacific_str: %s", pacific_str)
            self.garmin_idx[pacific_str] = act


if __name__ == "__main__":
    import logging.config

    log_config_path = pathlib.Path(__file__).parent / "logging.config"
    logging.config.fileConfig(
        log_config_path,
        disable_existing_loggers=False,
    )
    # global LOGGER
    log_name = pathlib.Path(__file__).stem
    print(f"log_name is {log_name}")
    LOGGER = logging.getLogger(log_name)

    test_activites_strava = (
        pathlib.Path(__file__).parent / "data" / "strava" / "activities.json"
    )
    with test_activites_strava.open("r") as f:
        strava_data = json.load(f)
    test_activites_garmin = (
        pathlib.Path(__file__).parent / "data" / "garmin" / "activities.json"
    )
    with test_activites_garmin.open("r") as f:
        garmin_data = json.load(f)

    act = ActivityCompare(garmin_activities=garmin_data, strava_activites=strava_data)
    # act.index_strava()
    # act.index_garmin()

    act.get_activities_to_upload()
