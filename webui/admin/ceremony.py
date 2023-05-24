from fastapi import APIRouter, Request

from webui.admin import templates, validate_auth
from webui.helpers.api_client import bootstrap_status
from webui import settings

ceremony_router = APIRouter(
    prefix="/ceremony"
)

@ceremony_router.get("/")
@validate_auth
def get_ceremony(request: Request):
    ceremony = bootstrap_status(settings, request.cookies)
    response = templates.TemplateResponse(
        "admin/ceremony.html",
        context={
            "request": request,
            "title": "Ceremony",
            "server": settings.SERVER,
            "ceremony": ceremony
        }
    )
    return response