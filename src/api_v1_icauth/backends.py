"""Custom authentication backend using Internet Identity login flow.

https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#writing-an-authentication-backend
"""

from typing import Optional, Any
from django.http import HttpRequest
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

from .canister_motoko import canister_motoko, is_response_variant_ok

UserModel = get_user_model()


class PrincipalBackend(BaseBackend):
    """
    Authenticate against the principal's password saved in an ic canister.

    The login flow is as follows:
    (-) User logs into dApp, using internet Identity
    (-) dApp makes authenticated call to ic canister, to get a session password
    (-) The session password is securily stored in the ic canister
    (-) dApp logs the user into project, with:
            username = principal
            password = session password
    (-) the authenticate method calls the ic canister, to check the password

    """

    def authenticate(
        self,
        request: Optional[HttpRequest],
        username: Any = None,
        password: Any = None,
        **kwargs: Any,
    ) -> Optional[Any]:
        """Authenticates username (principal) against session password in ic canister"""

        print("--custom backends.py -- authenticate --TODO: use logger.info--")
        print("TODO: only use CI based authentication when request.get_host() is IC")
        response = canister_motoko.whoami()  # pylint: disable=no-member
        print(
            "Response from canister_motoko.whoami, "
            "for django-server Internet Identity: "
        )
        print(response)
        print("-------------------------------")

        if request and request.session.session_key:
            # called after login
            # we save the session_key in IC canister & return
            try:
                response = canister_motoko.save_django_session_key(  # pylint: disable=no-member
                    request.session.session_key, username, password
                )
            except Exception as e:  # pylint: disable=broad-except
                print(e)
                print("IC Authentication failure - 1")
                return None

            print("--backends.py -- authenticate -- AFTER LOGIN  --TODO: REMOVE THIS--")
            print(f"request.session.session_key: {request.session.session_key}")
            print("Response from canister_motoko.save_django_session_key: ")
            print(response)
            print(f"username: {username}")
            print(
                f"UserModel.objects.get(username=username): "
                f"{UserModel.objects.get(username=username)}"
            )
            print("-------------------------------")
            if is_response_variant_ok(response):
                return UserModel.objects.get(username=username)

            print("IC Authentication failure - 2")
            return None

        # Not yet logged in
        # We need to authenticate the session_password with the IC canister
        if password:
            try:
                response = (
                    canister_motoko.session_password_check(  # pylint: disable=no-member
                        username, password
                    )
                )
            except Exception as e:  # pylint: disable=broad-except
                print(e)
                print("IC Authentication failure - 3")
                return None

            print("--backends.py -- authenticate -- BEFORE LOGIN --TODO: REMOVE THIS--")
            print("Response from canister_motoko.save_django_session_key: ")
            print(response)
            print("-------------------------------")
            if is_response_variant_ok(response):
                try:
                    user = UserModel.objects.get(username=username)
                except UserModel.DoesNotExist:
                    # Create a new user.
                    # There's no need to set a password because we use temporary
                    # session passwords generated and stored in the ic canister.
                    user = UserModel(username=username)
                    user.is_staff = False
                    user.is_superuser = False
                    user.save()
                return user

        print("IC Authentication failure - 4")
        return None

    def get_user(self, user_id: int) -> Optional[Any]:
        """Returns user objec if it exists"""
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
