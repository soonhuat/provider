#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from flask import jsonify, request
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from ocean_provider.constants import BaseURLs, Metadata
from ocean_provider.myapp import app
from ocean_provider.routes import services
from ocean_provider.utils.basics import get_configured_chains, get_provider_addresses
from ocean_provider.utils.error_responses import strip_and_replace_urls
from ocean_provider.utils.util import get_request_data
from ocean_provider.version import get_version

logger = logging.getLogger(__name__)


@app.before_request
def log_incoming_request():
    logger.info(
        f"incoming request = {request.scheme}, {request.method}, {request.remote_addr}, {request.full_path}"
    )


@app.after_request
def add_header(response):
    response.headers["Connection"] = "close"
    return response


@app.errorhandler(Exception)
def handle_error(error):
    code = getattr(error, "code", 503)

    error = strip_and_replace_urls(str(error))

    response = jsonify(error=str(error), context=get_request_data(request))
    response.status_code = code
    response.headers["Connection"] = "close"

    if code != 404:
        logger.error(f"error: {error}, payload: {request.data}", exc_info=1)
    else:
        logger.info(f"error: {str(error)}, payload: {request.data}")

    return response


def get_services_endpoints():
    services_endpoints = dict(
        map(
            lambda url: (url.endpoint.replace("services.", ""), url),
            filter(
                lambda url: url.endpoint.startswith("services."),
                app.url_map.iter_rules(),
            ),
        )
    )
    for (key, value) in services_endpoints.items():
        services_endpoints[key] = (
            list(
                map(
                    str,
                    filter(
                        lambda method: str(method) not in ["OPTIONS", "HEAD"],
                        value.methods,
                    ),
                )
            )[0],
            str(value),
        )
    return services_endpoints


@app.route("/")
def version():
    """
    Contains the provider data for an user:
        - software;
        - version;
        - network url;
        - provider address;
        - service endpoints, which has all
        the existing endpoints from routes.py.
    """
    logger.info("root endpoint called")
    info = dict()
    info["software"] = Metadata.TITLE
    info["version"] = get_version()
    info["providerAddresses"] = get_provider_addresses()
    info["chainIds"] = get_configured_chains()
    info["serviceEndpoints"] = get_services_endpoints()
    response = jsonify(info)
    logger.info(f"root endpoint response = {response}")
    return response


@app.route("/spec")
def spec():
    logger.info("spec endpoint called")
    swag = swagger(app)
    swag["info"]["version"] = get_version()
    swag["info"]["title"] = Metadata.TITLE
    swag["info"]["description"] = Metadata.DESCRIPTION
    response = jsonify(swag)
    logger.debug(f"spec endpoint response = {response}")
    return response


# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    BaseURLs.SWAGGER_URL,
    "/spec",
    config={"app_name": "Test application"},  # Swagger UI config overrides
)

# Register blueprint at URL
app.register_blueprint(swaggerui_blueprint, url_prefix=BaseURLs.SWAGGER_URL)
app.register_blueprint(services, url_prefix=BaseURLs.SERVICES_URL)

if __name__ == "__main__":
    app.run(port=8030)
