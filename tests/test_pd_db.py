import re
from pathlib import Path

import pandas as pd

from src.config_loader import instantiate_config


pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


BASE_DIR = Path("/Users/work/Documents/Programming/Palantiresque/Signal Engine")

CONFIG_PATH = BASE_DIR / "config/watchlist.yaml"

EVENTS_PATH = BASE_DIR / "data/raw/gdelt/20260618133000.translation.export.CSV"
MENTIONS_PATH = BASE_DIR / "data/raw/gdelt/20260618133000.translation.mentions.CSV"

CAMEO_PATH = BASE_DIR / "data/references/cameo_event_codes.csv"


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


def load_events(events_path: Path, cameo_path: Path) -> pd.DataFrame:
    events_df = pd.read_csv(
        events_path,
        sep="\t",
        header=None,
        names=GDELT_EVENT_COLUMNS,
        dtype=str,
    )

    events_df = events_df.drop(
        columns=["MonthYear", "Year", "FractionDate"],
        errors="ignore",
    )

    events_df["SQLDATE"] = pd.to_datetime(
        events_df["SQLDATE"],
        format="%Y%m%d",
        errors="coerce",
    )

    events_df["DATEADDED"] = pd.to_datetime(
        events_df["DATEADDED"],
        format="%Y%m%d%H%M%S",
        errors="coerce",
    )

    cameo_df = pd.read_csv(cameo_path, dtype=str)

    cameo_lookup = dict(
        zip(
            cameo_df["CAMEOEVENTCODE"],
            cameo_df["EVENTDESCRIPTION"],
        )
    )

    events_df["CAMEO_human_readable"] = events_df["EventCode"].map(cameo_lookup)

    return events_df


def load_mentions(mentions_path: Path) -> pd.DataFrame:
    mentions_df = pd.read_csv(
        mentions_path,
        sep="\t",
        header=None,
        names=GDELT_MENTION_COLUMNS,
        dtype=str,
    )

    mentions_df["EventTimeDate"] = pd.to_datetime(
        mentions_df["EventTimeDate"],
        format="%Y%m%d%H%M%S",
        errors="coerce",
    )

    mentions_df["MentionTimeDate"] = pd.to_datetime(
        mentions_df["MentionTimeDate"],
        format="%Y%m%d%H%M%S",
        errors="coerce",
    )

    return mentions_df


def match_concepts(
    events_df: pd.DataFrame,
    concepts: dict,
    cols: list[str],
) -> pd.DataFrame:
    matched_dfs = []

    existing_cols = [col for col in cols if col in events_df.columns]

    if not existing_cols:
        raise ValueError(f"None of these columns exist in events_df: {cols}")

    for concept_id, concept in concepts.items():
        terms = [term for term in concept.terms if term]

        if not terms:
            continue

        pattern = "(" + "|".join(re.escape(term) for term in terms) + ")"

        contains_df = (
            events_df[existing_cols]
            .astype("string")
            .apply(
                lambda col: col.str.contains(
                    pattern,
                    case=False,
                    na=False,
                    regex=True,
                )
            )
        )

        mask = contains_df.any(axis=1)

        if not mask.any():
            continue

        matched = events_df.loc[mask].copy()

        matched["concept_id"] = concept_id
        matched["concept_description"] = concept.description
        matched["concept_score"] = concept.score

        matched["matched_columns"] = contains_df.loc[mask].apply(
            lambda row: list(row.index[row.to_numpy()]),
            axis=1,
        )

        matched["matched_terms"] = (
            events_df.loc[mask, existing_cols]
            .astype("string")
            .apply(
                lambda row: sorted(
                    {
                        match.lower()
                        for value in row.dropna()
                        for match in re.findall(
                            pattern,
                            str(value),
                            flags=re.IGNORECASE,
                        )
                    }
                ),
                axis=1,
            )
        )

        matched_dfs.append(matched)

    if not matched_dfs:
        return pd.DataFrame()

    return pd.concat(matched_dfs, ignore_index=True)


def main() -> None:
    config = instantiate_config('/Users/work/Documents/Programming/Palantiresque/Signal Engine/config/watchlist_v2.yaml')
    concepts = config.concepts

    events_df = load_events(EVENTS_PATH, CAMEO_PATH)
    mentions_df = load_mentions(MENTIONS_PATH)

    print("\nEVENTS HEAD:")
    print(events_df.head())

    print("\nMENTIONS HEAD:")
    print(mentions_df.head())

    print("\nCAMEO MAPPING CHECK:")
    print(events_df[["EventCode", "CAMEO_human_readable"]].head(20))
    print(
        "\nCAMEO missing ratio:",
        events_df["CAMEO_human_readable"].isna().mean(),
    )

    cols_to_match = [
        "CAMEO_human_readable",
        "Actor1Name",
        "Actor2Name",
        "Actor1Geo_FullName",
        "Actor2Geo_FullName",
        "ActionGeo_FullName",
        "SOURCEURL",
    ]

    matches_df = match_concepts(
        events_df=events_df,
        concepts=concepts,
        cols=cols_to_match,
    )

    print("\nMATCHES:")
    print(matches_df)

    print("\nMATCH COUNT:", len(matches_df))

    if not matches_df.empty:
        print("\nMATCH SUMMARY BY CONCEPT:")
        print(
            matches_df
            .groupby(["concept_id", "concept_score"])
            .size()
            .reset_index(name="match_count")
            .sort_values(["concept_score", "match_count"], ascending=False)
        )

        print("\nSELECTED MATCH COLUMNS:")
        print(
            matches_df[
                [
                    "GLOBALEVENTID",
                    "SQLDATE",
                    "DATEADDED",
                    "EventCode",
                    "CAMEO_human_readable",
                    "Actor1Name",
                    "Actor2Name",
                    "ActionGeo_FullName",
                    "concept_id",
                    "concept_score",
                    "matched_columns",
                    "matched_terms",
                    "SOURCEURL",
                ]
            ].head(50)
        )


if __name__ == "__main__":
    main()