import pandas as pd
from pandas import to_datetime
import csv

pd.set_option("display.max_columns", None)      # show all columns
pd.set_option("display.width", None)

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


events_df = pd.read_csv('/Users/work/Documents/Programming/Palantiresque/Signal Engine/data/raw/gdelt/20260617171500.translation.export.CSV',
                 sep="\t",
                 header=None,
                 names=GDELT_EVENT_COLUMNS,
                 dtype=str,
                 parse_dates=['SQLDATE'])

# dropping redundant cols
events_df = events_df.drop(columns=['MonthYear','Year','FractionDate'])

# parsing date added
events_df['DATEADDED'] = pd.to_datetime(
    events_df['DATEADDED'].astype(str),
    format= '%Y%m%d%H%M%S',
    errors='coerce'
)



mentions_df = pd.read_csv('/Users/work/Documents/Programming/Palantiresque/Signal Engine/data/raw/gdelt/20260617171500.translation.mentions.CSV',
                          sep='\t',
                          header=None,
                          names=GDELT_MENTION_COLUMNS,
                          dtype=str,)

# parsing EventTimeDate
mentions_df['EventTimeDate'] = pd.to_datetime(
    mentions_df['EventTimeDate'].astype(str),
    format= '%Y%m%d%H%M%S',
    errors='coerce'
)

# parsing MentionTimeDate
mentions_df['MentionTimeDate'] = pd.to_datetime(
    mentions_df['MentionTimeDate'].astype(str),
    format= '%Y%m%d%H%M%S',
    errors='coerce'
)

cameo_path = "/Users/work/Documents/Programming/Palantiresque/Signal Engine/data/references/cameo_event_codes.csv"

cameo_df = pd.read_csv(cameo_path, dtype=str)

cameo_lookup= dict(zip(cameo_df["CAMEOEVENTCODE"], cameo_df["EVENTDESCRIPTION"]))

events_df["CAMEO_human_readable"] = (
    events_df["EventCode"]
    .astype(str)
    .map(cameo_lookup)
)

print(events_df.head())
print(mentions_df.head())
print(events_df.columns)