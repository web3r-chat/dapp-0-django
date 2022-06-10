"""Business logic of the apis"""

import time
import jwt
from django.http import HttpRequest

from django.conf import settings
from django.contrib import auth

from ninja.errors import HttpError

from . import schemas

from .canister_motoko import canister_motoko


# We can not use async, because the auth app is not async aware
def login(request: HttpRequest, body: schemas.BodyLoginSchema) -> dict[str, str]:
    """Authenticates with PrincipalBackend and logs into a django cookie based session.

    Returns a JSON containing a JWT token for non-django services:

    {"jwt": "--jwt token--"}
    """
    # https://docs.djangoproject.com/en/4.0/topics/auth/default/#how-to-log-a-user-in-1

    # We authenticate using the IC canister & create the user if not exists
    user = auth.authenticate(
        request, username=body.principal, password=body.session_password
    )

    if user is None:
        raise HttpError(400, "Unauthorized")

    # The user is now authenticated, but to avoid having to re-authenticate, also
    # log the user in, which persists it into a django session.
    print("DEBUG: apis.py - login - 01")
    auth.login(request, user)
    print("DEBUG: apis.py - login - 02")

    # Store the django session_key in the IC canister, for cleanup purposes
    # We call authenticate again, but only to store the django session_key in the
    # IC canister for cleanup purposes
    user = auth.authenticate(
        request, username=body.principal, password=body.session_password
    )
    print("DEBUG: apis.py - login - 03")

    # In addition to the django session approach, we also return a JWT token
    response_dict = {"jwt": create_jwt(body.principal)}
    print("DEBUG: apis.py - login - 04")
    print(f"response_dict: {response_dict}")

    return response_dict


def create_jwt(principal: str) -> str:
    """Creates a jwt for the logged in user."""
    # jwt_header = {"alg": "HS256", "typ": "JWT"} will be inserted by jwt.encode
    jwt_payload = {
        "iss": "web3r.chat",
        "exp": time.time() + settings.SESSION_COOKIE_AGE,
        "sub": principal,
    }
    return jwt.encode(
        jwt_payload,
        settings.SECRET_JWT_KEY,
        algorithm=settings.JWT_METHOD,
        headers=None,
        json_encoder=None,
    )


# We can not use async, because the auth app is not async aware
def logout(request: HttpRequest) -> dict[str, str]:
    """Logout the user."""
    # https://docs.djangoproject.com/en/4.0/topics/auth/default/#how-to-log-a-user-out

    # Remove the session password from the ic canister
    if request.user.is_authenticated and request.session.session_key:
        canister_motoko.session_password_delete(  # pylint: disable=no-member
            request.session.session_key
        )
    else:
        # TODO:
        # Read about SESSION_COOKIE_SAMESITE
        # https://django.readthedocs.io/en/stable/ref/settings.html#session-cookie-samesite
        #
        # The session cookie is not stored by the browser. It actually gives a warning
        # in the console about misuse of the "SameSite" attribute:
        #   Cookie “sessionid” has been rejected because it is in a cross-site context
        #   and its “SameSite” is “Lax” or “Strict”
        #
        # Thread careful though, because setting SESSION_COOKIE_SAMESITE to another
        # value might break CORS again in prod deployment...
        #
        print("logout: TODO - WE STILL NEED TO GET SESSION COOKIES TO STICK...")
        print("logout: We currently do NOT clean up the JWT data in the canister...")

    # Clean out the django session data.
    auth.logout(request)

    return {"status": "logged out"}
