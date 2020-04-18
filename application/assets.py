from flask_assets import Environment, Bundle


def compile_assets(app):
    """Configure & compile asset bundles."""
    assets = Environment(app)
    # ToDo