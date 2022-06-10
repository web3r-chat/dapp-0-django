#!/usr/bin/env bash
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(cat .env | grep -v '#' | xargs) && doctl auth init --access-token ${DIGITALOCEAN_ACCESS_TOKEN}
else
    echo "Cannot find .env - assuming environment variables are set"
    doctl auth init --access-token ${DIGITALOCEAN_ACCESS_TOKEN}
fi