import logging
import logging.config
import os
import pathlib
import sys

import activity_compare
import fit_lib
import garmin_lib
import nhl_lib
import strava_lib

# def update_activities():
#     nhl = nhl_lib.NHL()

#     strava = strava_lib.Strava()
#     activities = strava.get_activities(page_size=20)
#     for act in activities:
#         # 2024-12-21T00:13:04Z
#         act_date = act["start_date_local"].split("T")[0]
#         ride_name = nhl.get_score_label(act_date)
#         LOGGER.debug("%s ride name for %s is %s", act["name"], act_date, ride_name)
#         if (
#             (ride_name)
#             and act["name"] != ride_name
#             and (act["trainer"] or act["private"] or act["visibility"] == "only_me")
#         ):
#             LOGGER.debug("updating activity name to %s", ride_name)
#             strava.update_activity(act_id=act["id"], ride_name=ride_name)
#         else:
#             LOGGER.debug("ride is already named %s", ride_name)


def upload_activities():
    # get the garmin activities
    # probably can't set above 100 without rewriting to handle pages
    num_acts = 5
    bike_id_indoors = "b1348165"

    nhl = nhl_lib.NHL()

    gl = garmin_lib.Garmin()
    gl.login()
    garmin_activity_list = gl.download_activities(num_acts=num_acts)
    LOGGER.info(
        "got %s activites from garmin", len(garmin_activity_list["activityList"])
    )

    strava = strava_lib.Strava()
    strava_activities = strava.get_activities(page_size=num_acts)
    LOGGER.debug("got %s activities from strava", len(strava_activities))
    ac = activity_compare.ActivityCompare(
        garmin_activities=garmin_activity_list, strava_activites=strava_activities
    )
    garmins_to_upload = ac.get_activities_to_upload()

    """
    compare the two lists of actitivites
    garmin:
        data[activityList][item In list][startTimeLocal] looks like 
            2025-04-08 16:19:35
    strava:
        data[item_in_list][start_date_local]
            2025-04-08T16:19:35Z
    """

    for act in garmins_to_upload:
        garmin_dl_path = gl.get_download_path(act)
        date_str = act["startTimeLocal"].split(" ")[0]
        ride_name = nhl.get_score_label(date_str)
        LOGGER.debug("ride_name: %s", ride_name)
        is_indoor = gl.is_indoor(act)

        if not ride_name:
            ride_name = "call me al"

        if ride_name:
            # extract
            LOGGER.debug("extract files from zip")
            ff = fit_lib.FITFile(garmin_dl_path)
            fit_file = ff.extract()
            LOGGER.debug("fit file that is being uploaded: %s", fit_file)
            date = ff.get_date(convert_local=True)
            LOGGER.debug("ffdatetime: %s", date)

            # finally upload to strava
            LOGGER.debug("uploading... %s", ride_name)
            resp = strava.upload(fit_file, ride_name, private=False, indoor=is_indoor)
            strava_act = strava.wait_till_upload_complete(resp)
            LOGGER.debug("uploaded!")
            LOGGER.debug("resp: %s", resp)

            # activityType": {
            #    "typeId": 25,
            #    "typeKey": "indoor_cycling",
            if is_indoor:
                # update the gear  / bike to ole yeller
                strava.update_gear(strava_act["activity_id"], bike_id_indoors)

            # final step ... check if already uploaded...
            # if uploaded do the update for gear.
            # check that gear is a valid end point.

    # strava = strava_lib.Strava()
    # activities = strava.get_activities(page_size=20)


def main():
    LOGGER.info("Hello from garmin-sync!")
    # gl = garmin_lib.Garmin()
    # gl.login()
    # gl.download_activities(num_acts=5)
    nhl = nhl_lib.NHL()
    # score = nhl.get_score_label("2025-04-01")
    # LOGGER.info("score: %s", score)

    # fit_file = pathlib.Path("data/activities/18773241084_2025-04-08_in.fit")
    # if not fit_file.exists():
    #     print("doeesnt exist")

    # with fit_file.open("rb") as fit_file:
    #     print("exists and is valid")

    strava = strava_lib.Strava()

    strava.get_activities()

    # strava.upload(
    #     fit_file_path=fit_file, ride_label="MTL 3 - FLA 2", private=True, indoor=True
    # )

    # test update activity
    aid = 13190208423
    strava.update_activity(aid)


if __name__ == "__main__":
    log_config_path = pathlib.Path(__file__).parent / "logging.config"
    logging.config.fileConfig(
        log_config_path,
        disable_existing_loggers=False,
    )
    global LOGGER
    LOGGER = logging.getLogger("main")

    LOGGER.debug("testing  1 2 3 ")
    # main()
    # update_activities()
    upload_activities()
