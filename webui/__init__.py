
import functools

from dynaconf import Dynaconf
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import RedirectResponse

from webui.helpers import api_client

templates = Jinja2Templates(directory="./webui/templates")


rstuf_api_server = "http://api.dev.rstuf.org"

settings = Dynaconf(
    settings_files=["settings.toml"],
    envvar_prefix="RSTUF"
)


settings.AUTH = api_client.auth_enabled(settings)

def validate_auth(func):
    @functools.wraps(func)
    def wrapper_auth(*args, **kwargs):
        if settings.AUTH is True and kwargs["request"].cookies == {}:
            response = RedirectResponse("/admin")
            return response
        func(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper_auth