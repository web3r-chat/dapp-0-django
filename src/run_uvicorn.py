#!/usr/bin/env python
"""Runs Django under ASGI with uvicorn, with reloading when in Wing Pro.

https://www.uvicorn.org/deployment/#running-programmatically
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/uvicorn/
"""
import os
import uvicorn  # type: ignore[import]

DJANGO_PORT = int(os.environ.get("DJANGO_PORT", 8001))


def main() -> None:
    """Run uvicorn programmatically"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    reload = False
    if "WINGDB_ACTIVE" in os.environ:
        reload = True

    uvicorn.run(
        "project.asgi:application",
        port=DJANGO_PORT,
        reload=reload,
        lifespan="off",
    )


if __name__ == "__main__":
    main()
