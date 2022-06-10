"""Functions to interact with canister_motoko, using ic-py

Reference: https://github.com/rocklabs-io/ic-py
"""
import base64
from typing import Union
from django.conf import settings

from ic.canister import Canister  # type: ignore
from ic.client import Client  # type: ignore
from ic.identity import Identity  # type: ignore
from ic.agent import Agent  # type: ignore

# Read the private key from the .pem file for the `django-server` Identity
##with open(settings.IC_IDENTITY_PEM, "r", encoding="utf-8") as f:
##    private_key = f.read()
##private_key = settings.IC_IDENTITY_PEM
private_key = base64.b64decode(settings.IC_IDENTITY_PEM_ENCODED)


# Create an `django-server` Identity instance using the private key
identity = Identity.from_pem(private_key)

# Create an HTTP client instance for making HTTPS calls to the IC
# https://smartcontracts.org/docs/interface-spec/index.html#http-interface
client = Client(url=settings.IC_NETWORK_URL)

# Create an IC agent to communicate with IC canisters
agent = Agent(identity, client)

# Read canister_motoko candid from file
with open(settings.BASE_DIR / "candid/canister_motoko.did", "r", encoding="utf-8") as f:
    canister_motoko_did = f.read()

# Create a canister_motoko canister instance
canister_motoko = Canister(
    agent=agent, canister_id=settings.CANISTER_MOTOKO_ID, candid=canister_motoko_did
)


def is_response_variant_ok(
    response: Union[str, list[dict[str, Union[str, dict[str, str]]]]]
) -> bool:
    """Returns true if the response is of type=variant with a key=ok"""
    if response == "rejected":
        return False

    if not isinstance(response, list):
        return False

    r = response[0]

    # Format of the ic network, eg.:
    # [{'ok': None}]
    if "ok" in r.keys():
        return True

    # Format of the local network, eg.:
    # [{'type': 'variant', 'value': {'ok': None}}]
    if "type" in r.keys() and r["type"] == "variant":
        if isinstance(r["value"], dict):
            if "ok" in r["value"].keys():
                return True

    return False
