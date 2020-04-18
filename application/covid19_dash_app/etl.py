import urllib.request
import json
import pandas as pd
import numpy as np
import flask
from flask_caching import Cache


cache = Cache()


def init_cache(app):
    cache.init_app(app)


# Date & time of last update to remote data
_last_src_data_update = "N/A"


@cache.memoize(timeout=360)
def get_datasets():
    return ([], _last_src_data_update)
