import datetime
import logging
import logging.config
import pathlib
import zipfile
import zoneinfo

import fitdecode

LOGGER = logging.getLogger(__name__)


class FITFile:
    def __init__(self, fit_file_path):
        self.fit_path = fit_file_path
        self.tmp_path = fit_file_path.with_suffix(".fit")

        # self.fit_file = fitparse.FitFile(str(self.fit_path))

    def parse(self):
        for record in self.fit_file.get_messages("file_id"):
            for field in record:
                if field.name == "time_created":
                    print("Recording Date:", field.value)

    def extract(self):
        if not self.tmp_path.exists():
            file_names = []
            with zipfile.ZipFile(self.fit_path, "r") as zip_ref:
                file_names = zip_ref.namelist()
                file_name = pathlib.Path(file_names[0]).name
                with open(self.tmp_path, "wb") as f:
                    f.write(zip_ref.read(file_name))

            LOGGER.debug("file_names, %s", file_names)
        return self.tmp_path

    def get_date(self, convert_local=False):
        self.extract()
        creation_date = None
        session_start_time = None
        with fitdecode.FitReader(str(self.tmp_path)) as fit:
            for frame in fit:
                if isinstance(frame, fitdecode.records.FitDataMessage):
                    # Check 'file_id' message for creation time
                    if frame.name == "file_id":
                        for field in frame.fields:
                            if field.name == "time_created":
                                creation_date = field.value
                                LOGGER.debug("creation_date: %s", creation_date)
                                break
                    # Check 'session' message for start time
                    elif frame.name == "session":
                        for field in frame.fields:
                            if field.name == "start_time":
                                session_start_time = field.value
                                LOGGER.debug(
                                    "session_start_time: %s", session_start_time
                                )
                                break
                if creation_date and session_start_time:
                    break  # Exit early if both are found

        # 2025-04-11 23:18:39+00:00 need to be converted to pacific from utc
        # assumption is if convert_local is set to true
        # the subtract 7 hours
        # LOGGER.debug("type: %s", type(creation_date))
        # utc_dt = datetime.datetime.fromisoformat(creation_date)
        pacific_dt = creation_date.astimezone(zoneinfo.ZoneInfo("America/Los_Angeles"))
        creation_date = pacific_dt.strftime("%Y-%m-%d %H:%M:%S")
        return creation_date


if __name__ == "__main__":
    print("here")

    log_config_path = pathlib.Path(__file__).parent / "logging.config"
    logging.config.fileConfig(
        log_config_path,
        disable_existing_loggers=False,
    )
    LOGGER = logging.getLogger("main")
    LOGGER.info("test")
    ff_pat = "data/activities/17238531921_2024-10-08_out.zip"
    fitPath = pathlib.Path(ff_pat)
    ff = FITFile(fitPath)

    ff.extract()
    ff.get_date()
