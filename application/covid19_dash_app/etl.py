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
    return df_raw.loc[df_raw["state"] == "NSW"]


def clean_cases(df_raw):
    df_raw["locality"] = df_raw["lga_name19"].apply(get_locality)
    return df_raw


def get_locality(lga_name19):
    """
    Get a locality used by Australia Post from Local Government Area (LGA)
    name.

    LGA names have a structure of name & suffix. 
    A suffix indicates the Local Government Area status. 
    In New South Wales these suffixes are: Cities (C) and Areas (A).
    e.g.
    Burwood (A)
    Parramatta (C)

    Return a LGA name in uppercase and the suffix removed.
    """
    if type(lga_name19) != type(str):
        lga_name19 = str(lga_name19)
    locality = lga_name19.upper()
    locality = re.sub(r" \([A,C]\)", "", locality)
    return locality
