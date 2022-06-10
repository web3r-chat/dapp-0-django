"""Performs dapp-0-django api smoke tests"""
# pylint: disable=invalid-name
from typing import Any, Optional
import os
import sys
import time
import pprint

import requests
from requests import request

##import jwt


def my_print(msg: Any, status_code: Optional[int] = None) -> None:
    """Pretty print msg"""
    if VERBOSE > 0:
        if status_code:
            print(f"status_code: {status_code}")

        if isinstance(msg, (list, dict)):
            pprint.pprint(msg)
        else:
            print(msg)


HEALTH_CHECK_RETRIES = int(os.environ.get("HEALTH_CHECK_RETRIES", 100))
SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 1))

DJANGO_SERVER_URL = os.environ.get("DJANGO_SERVER_URL")
if DJANGO_SERVER_URL is not None:
    DJANGO_SERVER_URL = DJANGO_SERVER_URL.rstrip("/")

VERBOSE = int(os.environ.get("VERBOSE", 1))


if DJANGO_SERVER_URL is None:
    my_print("DJANGO_SERVER_URL is not defined as environment variable.")
    sys.exit(1)


###################################
my_print("=============================================\nStarting smoketest")

###################################
my_print("--\nDJANGO_SERVER_URL")
my_print(DJANGO_SERVER_URL)

###################################
my_print("--\nHealth check")

url = f"{DJANGO_SERVER_URL}/api/v1/icauth/health"
attempt = 0
while True:
    try:
        attempt += 1
        r = request("GET", url)

        if r.status_code == 200:
            my_print(f"attempt {attempt} succeeded")
            break

        my_print(f"attempt {attempt} failed")
        my_print(r.json(), r.status_code)
    except requests.exceptions.ConnectionError as _err:
        my_print(f"attempt {attempt} failed with requests.exceptions.ConnectionError")

    if attempt < HEALTH_CHECK_RETRIES:
        time.sleep(SLEEP_TIME)
        continue

    my_print("Too many failures...")
    sys.exit(1)


###################################
my_print("--\nSmoke tests passed! ")
sys.exit(0)
