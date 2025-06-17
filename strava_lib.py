import json
import logging
import os
import pathlib
import time

import requests

LOGGER = logging.getLogger(__name__)


class Strava:
    def __init__(self):
        self.access = None
        self.authenticate()

        self.data_dir = pathlib.Path(__file__).parent / "data" / "strava"
        if not self.data_dir.exists():
            self.data_dir.mkdir()

    def authenticate(self):
        secret = os.getenv("STRAVA_SECRET")
        refresh = os.getenv("STRAVA_REFRESH")
        client = os.getenv("STRAVA_CLIENT_ID")
        self.access = os.getenv("STRAVA_ACCESS_TOKEN")
        if not self.is_token_valid(self.access):
            LOGGER.info("getting new access key")
            self.access = self.get_access_token(client, secret, refresh)

    def get_access_token(self, client, secret, refresh):
        LOGGER.debug("getting new access token...")
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": client,
                "client_secret": secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh,
            },
        )
        resp_json = response.json()
        LOGGER.debug("full str: %s", resp_json)
        access_token = resp_json["access_token"]
        LOGGER.debug("access token: %s", access_token)
        return access_token

    def get_start_time_garmin_format(self, activity):
        start_time_str = " ".join(activity["start_date_local"].split("T"))
        if start_time_str[-1].upper() == "Z":
            start_time_str[:-1]
        LOGGER.debug("garmin start time: %s", start_time_str)
        return start_time_str

    def is_token_valid(self, access_token):
        url = "https://www.strava.com/api/v3/athlete"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 401:  # Token expired
            LOGGER.info("Access token has expired!")
            return False
        elif response.status_code == 200:  # Token is valid
            LOGGER.info("Access token is still valid.")
            return True
        else:
            LOGGER.info(f"Unexpected error: {response.status_code}")
            return None  # Handle other errors separately

    def upload(
        self,
        fit_file_path: pathlib.Path,
        ride_label: str,
        private: bool = False,
        indoor=False,
    ):
        LOGGER.debug("uploading activity... %s", fit_file_path)
        data = {
            "data_type": "fit",
            "name": ride_label,
            "sport_type": "Ride",
        }
        if indoor:
            data["trainer"] = 1
        # if private:
        #     data["private"] = 1

        with fit_file_path.open("rb") as fit_file:
            response = requests.post(
                "https://www.strava.com/api/v3/uploads",
                headers={"Authorization": f"Bearer {self.access}"},
                files={"file": fit_file},
                data=data,
            )
            resp_data = response.json()
            LOGGER.debug("response: %s %s", response, resp_data)
        return resp_data

    def update_gear(self, activity_id, gear_id):
        """
        Update activity with the gearid
        """
        url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {"Authorization": f"Bearer {self.access}"}
        payload = {"gear_id": gear_id}

        res = requests.put(url, headers=headers, data=payload)
        response_data = res.json()
        return response_data

    def wait_till_upload_complete(self, upload_resp):
        # example of upload struct
        # {'id': 15110546685, 'id_str': '15110546685',
        #   'external_id': '17869437845_2024-12-29_in.fit',
        #   'error': None, 'status': 'Your activity is still being processed.',
        # 'activity_id': None}
        LOGGER.debug("waiting 5 seconds...")
        time.sleep(5)
        res = requests.get(
            f"https://www.strava.com/api/v3/uploads/{upload_resp['id_str']}",
            headers={"Authorization": f"Bearer {self.access}"},
        )
        upload = res.json()
        if not upload["activity_id"]:
            LOGGER.debug("activity still not available....")
            self.wait_till_upload_complete(upload)
        LOGGER.debug("response from status, activity is ready: %s", upload)
        return upload

    def get_activities(self, page_size=10):
        params = {"page": 1, "per_page": page_size}
        # https://www.strava.com/api/v3/athlete/activities
        url = "https://www.strava.com/api/v3/athlete/activities"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.access}"},
        )
        results = response.json()
        LOGGER.debug("num results %s", len(results))

        activities_file = self.data_dir / "activities.json"
        if not activities_file.exists():
            with activities_file.open("w") as json_file:
                json.dump(results, json_file, indent=4)  # 'indent' makes it readable

        # start_date
        # trainer - if 1 its an trainer
        # private - True to indicate is private
        return results

    def update_activity(self, act_id, ride_name):
        if not isinstance(act_id, str):
            act_id = str(act_id)
        response = requests.put(
            f"https://www.strava.com/api/v3/activities/{act_id}",
            headers={"Authorization": f"Bearer {self.access}"},
            data={"private": False, "visibility": "everyone", "name": ride_name},
        )
        json_data = response.json()
        # LOGGER.debug("update json: %s", json_data)
        LOGGER.debug("json_data private property: %s", json_data["private"])
        LOGGER.debug("json_data visibility property: %s", json_data["visibility"])
        LOGGER.debug("json_data fide name property: %s", json_data["name"])


# 1348165 = yellow bike
