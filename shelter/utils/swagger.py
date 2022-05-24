import json
import os
import re
import tempfile
import unicodedata

import swagger_ui
from apispec import APISpec
from apispec.exceptions import APISpecError
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.tornado import TornadoPlugin


def create_api_doc(name, urls, app, config, interface_name):
    """Generates OpenApi doc file for urls and creates Swagger ui presentation for it."""
    spec = generate_swagger_spec(urls, name, config)
    save_swagger_file(spec, name, interface_name)
    swagger_ui.tornado_api_doc(
        app,
        config_path=get_swagger_file_path(name, interface_name),
        url_prefix="/swagger/spec.html",
        title=config.get("title", f"{name} API"),
    )


def generate_swagger_spec(handlers, app_name, config):
    """Automatically generates Swagger spec file based on RequestHandler docstrings."""

    # Starting to generate Swagger spec file. All the relevant
    # information can be found from here https://apispec.readthedocs.io/
    spec = APISpec(
        title=config.get("title", f"{app_name} API"),
        version=config.get("version", "1.0.0"),
        openapi_version=config.get("openapi_version", "3.0.3"),
        info=dict(description=config.get("description", f"Documentation for the {app_name} API")),
        plugins=[TornadoPlugin(), MarshmallowPlugin()],
    )
    # Looping through all the handlers and trying to register them.
    # Handlers without docstring will raise errors. That's why we
    # are catching them silently.
    for handler in handlers:
        try:
            spec.path(urlspec=handler)
        except APISpecError:
            pass
    return spec


def save_swagger_file(spec, app_name, interface_name):
    """Saves Swagger spec file to the temporary file location."""
    with open(get_swagger_file_path(app_name, interface_name), "w", encoding="utf-8") as file:
        json.dump(spec.to_dict(), file, ensure_ascii=False, indent=4)


def get_swagger_file_path(app_name, interface_name):
    """Normalizes the app name to valid filename and puts it to temp folder."""
    formatted_name = f"{slugify(app_name)}-{interface_name}.json"
    swagger_file_path = os.path.join(tempfile.gettempdir(), formatted_name)
    return swagger_file_path


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
