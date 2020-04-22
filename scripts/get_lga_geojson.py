"""Get NSW Local Govt Area boundary geo data.
Reduce precision of NSW LGA geo co-ordinates to 6 decimal places to 
improve map layer generation.
"""
import os.path
import urllib
import json
from geojson_precision import coord_precision as process_features

NSW_LGA_GEOJSON_URL = "https://data.gov.au/geoserver/nsw-local-government-areas/wfs?request=GetFeature&typeName=ckan_f6a00643_1842_48cd_9c2f_df23a3a1dc1e&outputFormat=json"


def get_lga_geojson():
    """Load NSW Local Govt Area boundaries.
    Download from data.gov.au if file does not exist.

    Return geojson object."""
    import json

    lga_path = "data/nsw-lga.geojson"
    lga_exists = False
    # Check if there is a downloaded copy of NSW LGA Geojson data
    if not os.path.isfile(lga_path):
        try:
            print("Download NSW LGA dataset %s...", (NSW_LGA_GEOJSON_URL,))
            req = urllib.request.urlopen(NSW_LGA_GEOJSON_URL)
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
    lga_path = "data/nsw-lga-6dp.geojson"
    with open(lga_path) as f:
        geojson = json.load(f)
    return geojson["features"]


if __name__ == "__main__":
    lga_geojson = get_lga_geojson()

    print(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": list(process_features(lga_geojson, 6)),
            }
        )
    )
