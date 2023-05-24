from fastapi import FastAPI

from webui import Request, templates
from webui.admin import admin_router

webui_app = FastAPI(
    title="Repository Service for TUF: WebUI Management",
    description="Web User Interface",
    docs_url="/docs/",
)

webui_app.include_router(admin_router)


@webui_app.get("/")
def get_root(request: Request):
    response = templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            "title": "RSTUF Web Interface"
        }
    )
    return response
