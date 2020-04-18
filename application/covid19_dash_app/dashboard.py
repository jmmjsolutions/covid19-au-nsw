"""Create a Dash app within a Flask app."""
from pathlib import Path
import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
from .layout import html_layout
from .etl import get_datasets, init_cache

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

    datasets, last_update_dt = get_datasets()

    # Create Dash Layout
    return html.Div(
        children=[
            html.Div(
                className="container",
                children=[
                    html.Div(
                        className="row", children=[html.H1("COVID-19 NSW Situation"),],
                    ),
                    html.Div(id="signal", style={"display": "none"}),
                ],
            )
        ],
        id="dash-container",
    )
