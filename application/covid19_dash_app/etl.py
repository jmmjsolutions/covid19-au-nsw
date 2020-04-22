import os.path
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
    NSW_CASES_BY_NOTIFICATION_DATE_AND_POSTCODE_URL = "https://data.nsw.gov.au/data/datastore/dump/21304414-1ff1-4243-a5d2-f52778048b29?bom=True"
    AU_POSTCODES = "au_postcodes"
    AU_POSTCODES_URL = "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv"
    NSW_LGA_GEOJSON_URL = "https://data.gov.au/geoserver/nsw-local-government-areas/wfs?request=GetFeature&typeName=ckan_f6a00643_1842_48cd_9c2f_df23a3a1dc1e&outputFormat=json"


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
            Constants.NSW_CASES_BY_NOTIFICATION_DATE_AND_POSTCODE_URL,
        ),
        (Constants.AU_POSTCODES, Constants.AU_POSTCODES_URL,),
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


@cache.memoize(timeout=3600)
def get_lga_features():
    """Load NSW Local Govt Area boundaries and create dataframe
    suitable for use as a features layer."""
    import json
    from pandas import json_normalize

    lga_path = "data/nsw-lga.geojson"
    lga_exists = False
    # Check if there is a downloaded copy of NSW LGA Geojson data
    if not os.path.isfile(lga_path):
        try:
            print("Download NSW LGA dataset %s...", (Constants.NSW_LGA_GEOJSON_URL,))
            req = urllib.request.urlopen(Constants.NSW_LGA_GEOJSON_URL)
            CHUNK = 256 * 10240
            with open(lga_path, "wb") as fp:
                while True:
                    chunk = req.read(CHUNK)
                    if not chunk:
                        break
                    fp.write(chunk)
        except Exception as e:
            # Download failed, not the end of the world,
            # so return an empty features list
            return []

    # Open LGA GeoJson file and load data
    with open(lga_path) as f:
        geojson = json.load(f)
    features = geojson["features"]

    return features


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
