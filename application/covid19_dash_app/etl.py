import urllib.request
import json
import re
import pandas as pd
import numpy as np
import flask
from flask_caching import Cache


class Constants:
    NSW_CASES_BY_NOTIFICATION_DATE_AND_POSTCODE = (
        "nsw_cases_by_notification_date_and_postcode"
    )
    AU_POSTCODES = "au_postcodes"


cache = Cache()


def init_cache(app):
    cache.init_app(app)


# Date & time of last update to remote data
_last_src_data_update = "N/A"


@cache.memoize(timeout=360)
def get_datasets():
    """Return all loaded datasets as cleaned dataframes."""
    raw_data = [
        (
            Constants.NSW_CASES_BY_NOTIFICATION_DATE_AND_POSTCODE,
            "https://data.nsw.gov.au/data/datastore/dump/21304414-1ff1-4243-a5d2-f52778048b29?bom=True",
        ),
        (
            Constants.AU_POSTCODES,
            "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv",
        ),
    ]

    dfs = {}

    for data in raw_data:
        data_id = data[0]
        data_url = data[1]
        print("Load %s...", (data_url,))
        df_raw = pd.read_csv(data_url)
        df_clean = clean_data(df_raw, data_id)
        print("Clean %s...", (data_url,))
        dfs[data_id] = df_clean

    return (dfs, _last_src_data_update)


def clean_data(df_raw, df_type):
    if df_type == Constants.AU_POSTCODES:
        df_clean = clean_postcodes(df_raw)
    elif df_type == Constants.NSW_CASES_BY_NOTIFICATION_DATE_AND_POSTCODE:
        df_clean = clean_cases(df_raw)
    else:
        df_clean = df_raw
    return df_clean


def clean_postcodes(df_raw):
    # Only interested in NSW post codes
    df = df_raw.loc[df_raw["state"] == "NSW"]
    # Some postcodes have multiple areas but to simplify plotting
    # we will just assume one location for a postcode.
    return df.drop_duplicates(subset="postcode", keep="first")


def clean_cases(df_raw):
    # Case postcode is a float, convert to int to allow matching with
    # Auspost postcode dataset
    df_raw["postcode"] = df_raw["postcode"].fillna(0)
    df_raw["postcode"] = df_raw["postcode"].astype(int)
    return df_raw
