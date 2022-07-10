import json
import os
import re
import tempfile
import unicodedata

import swagger_ui
import tornado.web
from apispec import APISpec
from apispec.exceptions import APISpecError
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.tornado import TornadoPlugin

__all__ = ["SwaggerApplication"]


class SwaggerApplication(tornado.web.Application):
    """Extends :class:`tornado.web.Application` with Swagger support.

    Override class :attribute:`API_VERSION` to specify the current application API version.
    Override class :attribute:`OPENAPI_VERSION` to support compatible OpenApi version with your docs.
    """

    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.0.3"

    def __init__(self, handlers=None, default_host=None, transforms=None, **settings):
        super().__init__(handlers=handlers, default_host=default_host, transforms=transforms, **settings)

        swagger_api_spec = {
            "version": self.API_VERSION,
            "openapi_version": self.OPENAPI_VERSION,
        }
        create_api_doc(settings["context"].config.name, handlers, self, swagger_api_spec, settings["interface"].name)


def create_api_doc(name, urls, app, swagger_api_spec, interface_name):
    """Generates OpenApi doc file for urls and creates Swagger ui presentation for it."""
    spec = generate_swagger_spec(urls, name, swagger_api_spec)
    save_swagger_file(spec, name, interface_name)
    swagger_ui.tornado_api_doc(
        app,
        config_path=get_swagger_file_path(name, interface_name),
        url_prefix="/swagger/spec.html",
        title=swagger_api_spec.get("title", f"{name} API"),
    )


def generate_swagger_spec(handlers, app_name, swagger_api_spec):
    """Automatically generates Swagger spec file based on RequestHandler docstrings."""

    # Starting to generate Swagger spec file. All the relevant
    # information can be found from here https://apispec.readthedocs.io/
    spec = APISpec(
        title=swagger_api_spec.get("title", f"{app_name} API"),
        version=swagger_api_spec.get("version", "1.0.0"),
        openapi_version=swagger_api_spec.get("openapi_version", "3.0.3"),
        info=dict(description=swagger_api_spec.get("description", f"Documentation for the {app_name} API")),
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
