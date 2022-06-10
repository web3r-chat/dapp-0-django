"""Django settings."""

import os
from pathlib import Path
from typing import Optional, cast
from django.core.management.utils import get_random_secret_key
from pydantic import BaseSettings, PostgresDsn, AnyHttpUrl
import dj_database_url  # type: ignore


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


class SettingsFromEnvironment(BaseSettings):
    """Defines environment variables with their types and optional defaults"""

    # postgresql
    # Optional, because DigitalOcean is NOT passing it in during initial setup
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_SSL: bool = True

    # Django settings: Provide a default for all, so it will work as well during
    #                  deployment of static files, when DigitalOcean is running
    #                  django-admin collectstatic
    SECRET_KEY: str = get_random_secret_key()
    DEBUG: bool = False
    DEBUG_TEMPLATES: bool = False
    USE_SSL: bool = False
    ALLOWED_HOSTS: list[str] = []
    DIGITALOCEAN_DOMAIN: Optional[str] = None

    SECRET_JWT_KEY: str = get_random_secret_key()
    JWT_METHOD: str = "HS256"
    IC_IDENTITY_PEM_ENCODED: str = ""
    # https://github.com/rocklabs-io/ic-py/issues/25
    IC_NETWORK_URL: AnyHttpUrl = cast(AnyHttpUrl, "http://localhost:8000")

    CANISTER_MOTOKO_ID: str = "rno2w-sqaaa-aaaaa-aaacq-cai"

    CORS_ALLOWED_ORIGINS: list[str] = []

    class Config:  # pylint: disable=too-few-public-methods
        """Defines configuration for pydantic environment loading"""

        env_file = str(BASE_DIR / ".env")
        case_sensitive = True


config = SettingsFromEnvironment()

if config.DATABASE_URL is not None:
    os.environ["DATABASE_URL"] = config.DATABASE_URL
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=600, ssl_require=config.DATABASE_SSL
        )
    }

SECRET_KEY = config.SECRET_KEY
DEBUG = config.DEBUG
DEBUG_TEMPLATES = config.DEBUG_TEMPLATES
USE_SSL = config.USE_SSL

ALLOWED_HOSTS = config.ALLOWED_HOSTS
if config.DIGITALOCEAN_DOMAIN is not None:
    ALLOWED_HOSTS += config.DIGITALOCEAN_DOMAIN.split(",")

SECRET_JWT_KEY = config.SECRET_JWT_KEY
JWT_METHOD = config.JWT_METHOD
IC_IDENTITY_PEM_ENCODED = config.IC_IDENTITY_PEM_ENCODED
IC_NETWORK_URL = config.IC_NETWORK_URL
CANISTER_MOTOKO_ID = config.CANISTER_MOTOKO_ID

# ######################################################################
# https://www.stackhawk.com/blog/django-cors-guide/

CORS_ALLOWED_ORIGINS = config.CORS_ALLOWED_ORIGINS
print(f"CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "accept-language",
    "access-control-request-headers",
    "access-control-request-method",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "x-csrftoken",
    "x-requested-with",
    "referer",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
    "sec-ch-ua",
    "sec-ch-ua-mobile",
    "sec-ch-ua-platform",
    "user-agent",
    "header",
]
CORS_ALLOW_CREDENTIALS = True
# ######################################################################


# Application definition

INSTALLED_APPS = [
    "corsheaders",
    "api_v1_icauth.apps.ApiV1Icauth",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": True,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# Register the custom authentication backend
# https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#writing-an-authentication-backend # pylint: disable=line-too-long
AUTHENTICATION_BACKENDS = (
    "api_v1_icauth.backends.PrincipalBackend",
    "django.contrib.auth.backends.ModelBackend",
)

# Define session behavior (Django login/logout cookie sessions)
# https://docs.djangoproject.com/en/4.0/topics/http/sessions/#topics-http-sessions
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 8 * 60 * 60

# ##########
# Security #
# ##########
# https://docs.djangoproject.com/en/3.2/topics/security

if not USE_SSL:
    SECURE_PROXY_SSL_HEADER = None
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    # IMPORTANT: ONLY APPLY THESE ON THE SERVER !
    #
    # (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True. Unless your
    #                 site should be available over both SSL and non-SSL connections,
    #                 you may want to either set this setting True or configure a load
    #                 balancer or reverse-proxy server to redirect all connections to
    #                 HTTPS.
    # https://help.heroku.com/J2R1S4T8/can-heroku-force-an-application-to-use-ssl-tls
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True

    # (security.W012) SESSION_COOKIE_SECURE is not set to True. Using a secure-only
    #                 session cookie makes it more difficult for network traffic
    #                 sniffers to hijack user sessions.
    SESSION_COOKIE_SECURE = True

    # (security.W016) You have 'django.middleware.csrf.CsrfViewMiddleware' in your
    #                 MIDDLEWARE, but you have not set CSRF_COOKIE_SECURE to True.
    #                 Using a secure-only CSRF cookie makes it more difficult for
    #                 network traffic sniffers to steal the CSRF token.
    CSRF_COOKIE_SECURE = True

    # (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting. If
    #                 your entire site is served only over SSL, you may want to consider
    #                 setting a value and enabling HTTP Strict Transport Security. Be
    #                 sure to read the documentation first; enabling HSTS carelessly can
    #                 cause serious, irreversible problems.
    #
    # IMPORTANT:
    # (-) Add these only once the HTTPS redirect is confirmed to work
    #
    SECURE_HSTS_SECONDS = 2592000  # 1 month
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # pylint: disable=line-too-long
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# location where you will store your static files
STATICFILES_DIRS = [BASE_DIR / "static"]
# location where django collects all static files
# add this to .gitignore (!)
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)

# URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = "/static/"

# https://www.mattlayman.com/understand-django/serving-static-files/
# https://cheat.readthedocs.io/en/latest/django/static_files.html#the-whitenoise-app
#
# (-) During collectstatic, whitenoise inserts the content hash into filenames, to
#     enable long term caching by browsers. For example, it will modify
#     vendors.js into vendors.abcd1234.js
#
# (-) Whitenoise lets Django itself serve static files in production mode, kind of like
#     runserver does in development mode.
#
# (-) Even though whitenoise docs say ASGI is not supported, it works fine.
#
# (-) It is used only when running locally behind gunicorn and/or uvicorn.
#     Locally, we do not run behind nginx, and the requests for static files are simply
#     send to Django. Whitenoise takes care of serving the static files.
#     You MUST run `python manage.py collectstatic` first!
#
# (-) It is NOT used when developing locally with django's runserver.
#     The Django runserver intercepts the requests for static files and serves them.
#     https://cheat.readthedocs.io/en/latest/django/static_files.html#the-default-case-during-development # pylint: disable=line-too-long
#
# (-) It is NOT used in production on Digital Ocean.
#     The application runs behind nginx, and requests for static files are routed to
#     a CDN. The requests for static files never reach Django!
#     So, whitenoise is not doing anything in production:
#     https://cheat.readthedocs.io/en/latest/django/static_files.html#the-most-common-case-when-deployed-to-production # pylint: disable=line-too-long
#
# https://cheat.readthedocs.io/en/latest/django/static_files.html
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
