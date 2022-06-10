"""URLs"""

from django.urls import path
from django.http import HttpRequest

from ninja import NinjaAPI

from . import schemas
from . import apis

api = NinjaAPI()


@api.get("/health")
async def health(request: HttpRequest) -> dict[str, str]:
    """Health endpoint for api/v1/icauth"""
    return {"status": "ok"}


@api.post("/login")
def login(request: HttpRequest, body: schemas.BodyLoginSchema) -> dict[str, str]:
    """Logs the user in & returns a JWT token valid for duration of django session:

    {"jwt": "--jwt token--"}
    """
    return apis.login(request, body)


@api.post("/logout")
def logout(request: HttpRequest) -> dict[str, str]:
    """ "Logs the user out."""
    return apis.logout(request)


urlpatterns = [
    path("api/v1/icauth/", api.urls),
]
