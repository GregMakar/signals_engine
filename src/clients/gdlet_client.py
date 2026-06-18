import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
from pathlib import PurePosixPath
from datetime import datetime
import pandas as pd
from pathlib import Path
from urllib.request import urlretrieve
import zipfile


load_dotenv("/Users/work/Documents/Programming/Palantiresque/Signal Engine/src/clients/clients.env")


class GDELTIngestor:
    """
    simply instantiate the class, and run installer() which will automatically install
    the latest news articles if it is not installed already.
    """
    def __init__(self,
                 manifest_link: str = os.getenv('GDELT_LAST_UPDATE_MANIFEST_LINK'),
                 timeout: str = os.getenv('REQ_TIMEOUT_SEC'),
                 exports: tuple[str] = ('events', 'mentions'),
                 gdelt_ingestion_csv: str = os.getenv('GDELT_INGESTIONS_CSV'),
                 extract_to: str = os.getenv('GDELT_EXTRACT_TO')
                 ):

        self.manifest_link = manifest_link
        self.timeout = timeout
        self.exports = exports
        self.gdelt_ingestion_csv = gdelt_ingestion_csv
        self.ingestions_data= pd.read_csv(gdelt_ingestion_csv, parse_dates=['ingestion_timestamp', 'link_timestamp'])
        self.urls_dict = None
        self.extract_to = extract_to

    def fetch(self) -> dict[str, str]:
        """
        sample...
            74078 bf2d68a69980365347b127f1f4cdd78a http://data.gdeltproject.org/gdeltv2/20260618113000.translation.export.CSV.zip
            111081 aab3218685425c34441233c16635d730 http://data.gdeltproject.org/gdeltv2/20260618113000.translation.mentions.CSV.zip
            13293270 36eca0cf6cc6a582efd71f277346a0fd http://data.gdeltproject.org/gdeltv2/20260618113000.translation.gkg.csv.zip
        :return: ex. {'events_url': 'http://data.gdeltproject.org/gdeltv2/20260618121500.translation.export.CSV.zip', 'mentions_url': 'http://data.gdeltproject.org/gdeltv2/20260618121500.translation.mentions.CSV.zip'}

        """

        response = requests.get(self.manifest_link, timeout=int(self.timeout))
        response.raise_for_status()

        cleaned_list = [line for line in response.iter_lines()]

        urls = []
        for line in cleaned_list:
            line = str(line).split(' ')
            urls.append(line[2].rstrip("'"))

        urls_dict = {}
        if 'events' in self.exports:
            urls_dict['events_url'] = urls[0]
        if 'mentions' in self.exports:
            urls_dict['mentions_url'] = urls[1]
        if 'gkg' in self.exports:
            urls_dict['gkg_url'] = urls[2]

        self.urls_dict = urls_dict

        return urls_dict

    def _date_time_str_parser(self, url: str) -> datetime:
        """
        timestamp_str -> 20260618121500 str
        timestamp -> 2026-06-18 12:15:00 obj
        """

        filename = PurePosixPath(urlparse(url).path).name
        timestamp_str = filename.split(".", 1)[0]

        timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

        return timestamp


    def validator(self) -> bool:
        if self.urls_dict is None:
            self.fetch()

        existing_timestamps = set(self.ingestions_data["link_timestamp"])

        for url in self.urls_dict.values():
            timestamp = pd.Timestamp(self._date_time_str_parser(url))

            if timestamp in existing_timestamps:
                return False

        return True


    def installer(self):
        if self.urls_dict is None:
            self.fetch()

        if not self.validator():
            raise FileExistsError("File already downloaded")

        extract_dir = Path(self.extract_to)
        extract_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []

        for type, url in self.urls_dict.items():
            filename = PurePosixPath(urlparse(url).path).name
            zip_path = extract_dir / filename

            response = requests.get(url, timeout=int(self.timeout))
            response.raise_for_status()

            zip_path.write_bytes(response.content)

            if not zipfile.is_zipfile(zip_path):
                raise ValueError(f"Invalid zip file: {zip_path}")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
                extracted_files.extend(extract_dir / name for name in zip_ref.namelist())

            self.ingestions_data.loc[len(self.ingestions_data)] = {
                'ingestion_timestamp': pd.Timestamp.now(),
                'link_timestamp': pd.to_datetime(self._date_time_str_parser(url)),
                'type': type.rstrip('_url')
            }

            self.ingestions_data.to_csv(self.gdelt_ingestion_csv, index=False)


        return extracted_files



class GDELTNormalizer:

