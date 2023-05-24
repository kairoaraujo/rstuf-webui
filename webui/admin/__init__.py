from enum import Enum
from typing import Dict

from fastapi import APIRouter, Request, Form, status, Depends, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import BaseModel, Field, SecretStr, ValidationError

from webui import settings, templates, validate_auth
from webui.admin.ceremony import ceremony_router
from webui.helpers import api_client

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

admin_router.include_router(ceremony_router)

def _login(server: str, data: Dict[str, str]):
    token_response = api_client.request_server(
        server, api_client.URL.token.value, api_client.Methods.post, data=data
    )
    if token_response.status_code != 200:
        return None

    return token_response.json()

@admin_router.get("/")
def get_root(request: Request):
    token = request.cookies.get("Authorization")
    response = templates.TemplateResponse(
        "admin/index.html",
        context={
            "request": request,
            "title": "Admin",
            "auth": settings.AUTH,
            "server": settings.SERVER,
            "token": token
        }
    )
    return response

class TokenRequestForm:
    def __init__(
        self,
        password: SecretStr = Form(),
    ):
        self.password = password.get_secret_value()


@admin_router.post("/")
def post_root(response: Response, form: TokenRequestForm = Depends()):
    data = {
        "username": "admin",
        "password": form.password,
        "scope": (
            "write:targets "
            "write:bootstrap "
            "read:bootstrap "
            "read:settings "
            "read:token "
            "read:tasks "
            "write:token "
        ),
        "expires": 8,
    }

    login_response = _login(settings.SERVER, data=data)
    response = RedirectResponse(url="/admin/",status_code=status.HTTP_303_SEE_OTHER)
    if login_response is not None:
        rstuf_token = f"Bearer {login_response.get('access_token')}"

    else:
        rstuf_token = "Failed"

    response.set_cookie(
        key="Authorization",
        value=rstuf_token,
        domain=settings.SERVER.split("://")[1].split("/")[0],
        httponly=True,
        max_age=30,
        expires=30,
    )

    return response
