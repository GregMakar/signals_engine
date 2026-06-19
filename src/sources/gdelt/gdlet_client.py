import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
from pathlib import PurePosixPath
from datetime import datetime
import pandas as pd
from pathlib import Path
import zipfile
from src.config_loader import instantiate_config


load_dotenv(".env")


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
                 ) -> None:

        self.manifest_link = manifest_link
        self.timeout = timeout
        self.exports = exports
        self.gdelt_ingestion_csv = gdelt_ingestion_csv
        self.ingestion_data= pd.read_csv(gdelt_ingestion_csv, parse_dates=['ingestion_timestamp', 'link_timestamp'])
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

        existing_timestamps = set(self.ingestion_data["link_timestamp"])

        for url in self.urls_dict.values():
            timestamp = pd.Timestamp(self._date_time_str_parser(url))

            if timestamp in existing_timestamps:
                return False

        return True


    def installer(self) -> list[str]:
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

            self.ingestion_data.loc[len(self.ingestion_data)] = {
                'ingestion_timestamp': pd.Timestamp.now(),
                'link_timestamp': pd.to_datetime(self._date_time_str_parser(url)),
                'type': type.rstrip('_url')
            }

            self.ingestion_data.to_csv(self.gdelt_ingestion_csv, index=False)

        extracted_files_as_strings = [str(path) for path in extracted_files]

        return extracted_files_as_strings



class GDELTNormalizer:
    GDELT_EVENT_COLUMNS = [
        "GLOBALEVENTID",
        "SQLDATE",
        "MonthYear",
        "Year",
        "FractionDate",

        "Actor1Code",
        "Actor1Name",
        "Actor1CountryCode",
        "Actor1KnownGroupCode",
        "Actor1EthnicCode",
        "Actor1Religion1Code",
        "Actor1Religion2Code",
        "Actor1Type1Code",
        "Actor1Type2Code",
        "Actor1Type3Code",

        "Actor2Code",
        "Actor2Name",
        "Actor2CountryCode",
        "Actor2KnownGroupCode",
        "Actor2EthnicCode",
        "Actor2Religion1Code",
        "Actor2Religion2Code",
        "Actor2Type1Code",
        "Actor2Type2Code",
        "Actor2Type3Code",

        "IsRootEvent",
        "EventCode",
        "EventBaseCode",
        "EventRootCode",
        "QuadClass",
        "GoldsteinScale",
        "NumMentions",
        "NumSources",
        "NumArticles",
        "AvgTone",

        "Actor1Geo_Type",
        "Actor1Geo_FullName",
        "Actor1Geo_CountryCode",
        "Actor1Geo_ADM1Code",
        "Actor1Geo_ADM2Code",
        "Actor1Geo_Lat",
        "Actor1Geo_Long",
        "Actor1Geo_FeatureID",

        "Actor2Geo_Type",
        "Actor2Geo_FullName",
        "Actor2Geo_CountryCode",
        "Actor2Geo_ADM1Code",
        "Actor2Geo_ADM2Code",
        "Actor2Geo_Lat",
        "Actor2Geo_Long",
        "Actor2Geo_FeatureID",

        "ActionGeo_Type",
        "ActionGeo_FullName",
        "ActionGeo_CountryCode",
        "ActionGeo_ADM1Code",
        "ActionGeo_ADM2Code",
        "ActionGeo_Lat",
        "ActionGeo_Long",
        "ActionGeo_FeatureID",

        "DATEADDED",
        "SOURCEURL",
    ]
    GDELT_MENTION_COLUMNS = [
        "GLOBALEVENTID",
        "EventTimeDate",
        "MentionTimeDate",
        "MentionType",
        "MentionSourceName",
        "MentionIdentifier",
        "SentenceID",
        "Actor1CharOffset",
        "Actor2CharOffset",
        "ActionCharOffset",
        "InRawText",
        "Confidence",
        "MentionDocLen",
        "MentionDocTone",
        "MentionDocTranslationInfo",
        "Extras",
    ]

    def __init__(self, paths: str | list[str]) -> None:
        """

        :param paths: it is intended to receive the return value list[str] from GDELTIngestor.installer()
        """
        self.paths = paths
        self.dataframes : dict[str, pd.DataFrame] | None = None


    def _delete_file(self, path: str | Path) -> None:
        path = Path(path)

        if not path.exists():
            return

        if not path.is_file():
            raise ValueError(f"Not a file: {path}")

        path.unlink()

    def csv_to_pd(self) -> dict[str, pd.DataFrame]:
        """

        :return: csv paths that were instantiated converted to dataframes. With the datetime
         columns are normalized.
        """
        dic = {}

        if self.paths[0]:
            df = pd.read_csv(self.paths[0],
                             sep="\t",
                             header=None,
                             names=self.GDELT_EVENT_COLUMNS,
                             dtype=str,
                             parse_dates=['SQLDATE']
                             )

            # dropping redundant cols
            df = df.drop(columns=['MonthYear', 'Year', 'FractionDate'])


            # parsing date added
            df['DATEADDED'] = pd.to_datetime(
                df['DATEADDED'].astype(str),
                format='%Y%m%d%H%M%S',
                errors='coerce'
            )

            dic['events_df'] = df

        if self.paths[1]:
            m_df = pd.read_csv(
                self.paths[1],
                sep='\t',
                header=None,
                names=self.GDELT_MENTION_COLUMNS,
                dtype=str, )

            # parsing EventTimeDate
            m_df['EventTimeDate'] = pd.to_datetime(
                m_df['EventTimeDate'].astype(str),
                format='%Y%m%d%H%M%S',
                errors='coerce'
            )

            # parsing MentionTimeDate
            m_df['MentionTimeDate'] = pd.to_datetime(
                m_df['MentionTimeDate'].astype(str),
                format='%Y%m%d%H%M%S',
                errors='coerce'
            )

            dic['mentions_df'] = m_df

        if self.paths[2]:
            ... # gkg logic here


        self.dataframes = dic

        return dic

    def matcher(self, dataframes:[pd.DataFrame], gkg_enrich:bool = False) -> pd.DataFrame:
        """
        takes events db and mentions db and returns a joint dataframe that
        :param dataframes: events_df + mentions_df + optionally:gkg_df for further enrichment
        :param gkg_enrich: bool, set to False, toggle to True to enrich further
        :return:
        """
        config = instantiate_config('/config/watchlist.yaml')
        concepts = config.concepts
        entities = config.entities

        if not self.dataframes:
            self.csv_to_pd()


        ...

    def to_evidence_hit(self):
        ...

    def to_evidence_hits(self):
        ...
