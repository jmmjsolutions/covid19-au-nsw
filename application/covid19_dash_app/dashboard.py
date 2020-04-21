"""Create a Dash app within a Flask app."""
from pathlib import Path
from flask import current_app
import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
from .layout import html_layout
from .etl import get_datasets, get_lga_features, init_cache, Constants

cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "cache-directory",
    "CACHE_THRESHOLD": 10,
}


def Add_Dash(server):
    """Create a Dash app."""
    external_stylesheets = [
        "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css",
        "https://fonts.googleapis.com/css?family=Lato",
        "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
    ]
    external_scripts = [
        "https://code.jquery.com/jquery-3.2.1.slim.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js",
        "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js",
        "/static/dist/js/main.js",
    ]
    dash_app = dash.Dash(
        server=server,
        external_stylesheets=external_stylesheets,
        external_scripts=external_scripts,
        routes_pathname_prefix="/dashboard/",
    )

    server.config.from_mapping(cache_config)
    init_cache(server)

    # Override the underlying HTML template
    dash_app.index_string = html_layout

    dash_app.layout = generate_layout

    return dash_app.server


def generate_layout():
    """Generate dashboard html layout."""
    datasets, last_update_dt = get_datasets()

    df_cases = combine_data(
        datasets[Constants.NSW_CASES_BY_NOTIFICATION_DATE_AND_POSTCODE],
        datasets[Constants.AU_POSTCODES],
    )

    # Create Dash Layout
    return html.Div(
        children=[
            html.Div(
                className="container",
                children=[
                    html.Div(
                        className="row",
                        children=[html.H1("COVID-19 NSW Cases By Postcode"),],
                    ),
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className="col",
                                children=total_cases_nsw_map(df_cases, colname="cases"),
                            )
                        ],
                    ),
                    html.Div(id="signal", style={"display": "none"}),
                ],
            )
        ],
        id="dash-container",
    )


def combine_data(df_cases, df_postcodes):
    """Join cases dataframe to postcode dataframe to get geo co-ords.
    Total cases by postcode."""
    df_cases_with_geo = df_cases.merge(df_postcodes, on="postcode", how="left")
    df_cases_with_geo["cases"] = 1
    cases_total_by_postcode = (
        df_cases_with_geo.groupby(by=["postcode", "lga_name19", "long", "lat"])["cases"]
        .sum()
        .groupby(level=[1])
        .cumsum()
        .reset_index()
    )

    return cases_total_by_postcode


def total_cases_nsw_map(df, colname="cases"):
    """Create NSW map of confirmed cases by postcode."""

    token = current_app.config["MAPBOX_TOKEN"]

    fig = go.Figure(
        go.Scattermapbox(
            name="",
            mode="markers+text",
            hovertext=df["postcode"].astype(str) + " " + df["lga_name19"],
            lon=df["long"],
            lat=df["lat"],
            marker={
                "color": "red",
                "size": df["cases"],
                "symbol": "circle",
                "sizemode": "area",
                "sizemin": 2,
                "sizeref": 2.0 * max(df["cases"]) / (16.0 ** 2),
            },
            hovertemplate="<b>%{hovertext} </b><br>"
            + "cases: %{marker.size}<br>"
            + "longitude: %{lon}<br>"
            + "latitude: %{lat}<br>",
        )
    )

    fig.update_layout(
        mapbox={
            "accesstoken": token,
            "style": "open-street-map",
            "center": {"lon": 146.9211, "lat": -31.2532},
            "zoom": 5,
            "layers": [
                {
                    "source": {
                        "type": "FeatureCollection",
                        "features": get_lga_features(),
                    },
                    "type": "line",
                    "below": "traces",
                    "color": "royalblue",
                }
            ],
        },
        showlegend=False,
        margin={"l": 0, "r": 0, "b": 0, "t": 0},
    )

    return [dcc.Graph(figure=fig)]
