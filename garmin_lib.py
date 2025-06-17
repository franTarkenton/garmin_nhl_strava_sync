import json
import logging
import os
import pathlib

import garth
import garth.exc

LOGGER = logging.getLogger(__name__)


class Garmin:
    def __init__(self):
        LOGGER.debug("test message")
        self.data_dir = pathlib.Path(__file__).parent / "data"
        self.session_dir = pathlib.Path(__file__).parent / "garth_session"
        if not self.session_dir.exists():
            LOGGER.debug("creating the dir %s", self.session_dir.parent)
            self.session_dir.mkdir()

        self.activity_dir = self.data_dir / "activities"
        if not self.activity_dir.exists():
            LOGGER.debug("creating the activity dir: %s", self.data_dir)
            self.activity_dir.mkdir(parents=True, exist_ok=True)
        self.client = None

        # write samples here to later look at
        self.garmin_obj_path = pathlib.Path(__file__).parent / "data" / "garmin"
        if not self.garmin_obj_path.exists():
            self.garmin_obj_path.mkdir()

    def login(self):
        # try to resume first
        garth.resume(str(self.session_dir))
        try:
            garth.client.username
        except garth.exc.GarthException:
            # Session is expired. You'll need to log in again
            LOGGER.info("getting a new session")
            email = os.getenv("GARMIN_USER")
            password = os.getenv("GARMIN_PASSWORD")
            garth.login(email, password)
            garth.save(str(self.session_dir))
        self.client = garth.client

    def get_activities_list(self, num_acts: int = 10):
        # url = "https://connect.garmin.com/proxy/activitylist-service/activities"
        service_path = "/activitylist-service/activities"
        params = {
            "start": 1,
            "limit": num_acts,
        }
        activities = garth.connectapi(service_path, params=params)

        acts_path = self.garmin_obj_path / "activities.json"
        if not acts_path.exists():
            with acts_path.open("w") as json_file:
                json.dump(activities, json_file, indent=4)  # 'indent' makes it readable

        # LOGGER.debug(activities)
        return activities

    def download_activities(self, num_acts):
        activity_list = self.get_activities_list(num_acts=num_acts)
        for activity in activity_list["activityList"]:
            self.download_activity(activity)
        return activity_list

    def get_download_path(self, activity):
        profile_str = "out"
        if "indoor" in activity["activityType"]["typeKey"]:
            profile_str = "in"

        date_str = activity["startTimeLocal"].split(" ")[0]
        activity_file_name = f"{activity['activityId']}_{date_str}_{profile_str}.zip"
        dest_path = self.activity_dir / activity_file_name
        return dest_path

    def download_activity(self, activity):
        dest_path = self.get_download_path(activity)
        if not dest_path.exists():
            url_path = f"/download-service/files/activity/{activity['activityId']}"
            response = self.client.get("connectapi", url_path, api=True, stream=True)
            if response.status_code == 200:
                with dest_path.open("wb") as f:
                    # for chunk in response.iter_content(chunk_size=8192):
                    #     f.write(chunk)
                    f.write(response.content)
                print(f"Downloaded {dest_path}")

            else:
                LOGGER.debug("file %s already exists", dest_path)

    def is_indoor(self, activity):
        if "indoor" in activity["activityType"]["typeKey"].lower():
            return True
        return False
