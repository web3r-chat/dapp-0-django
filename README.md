# dapp-0-django

A Django Ninja api for our first Rasa Chatbot for the Internet Computer

The live deployment can be found at https://web3r.chat

The full application consists of 3 GitHub repositories:
1. [dapp-0](https://github.com/web3r-chat/dapp-0)
2. [dapp-0-django](https://github.com/web3r-chat/dapp-0-django)
3. [dapp-0-bot](https://github.com/web3r-chat/dapp-0-bot)

# Setup

## Git

```bash
git clone git@github.com:web3r-chat/dapp-0-django.git
cd dapp-0-django
```

### pre-commit

Create this pre-commit script, file `.git/hooks/pre-commit`

```bash
#!/bin/bash

# Apply all static auto-formatting & perform the static checks
export PATH="$HOME/miniconda3/envs/dapp-0-django/bin:$PATH"
/usr/bin/make all-static
```

and make the script executable:

```bash
chmod +x .git/hooks/pre-commit
```

## django-server identity

The API makes authenticated calls to canister_motoko, using a dedicated django-server identity.

- We used dfx to create the [dfx identity](https://smartcontracts.org/docs/developers-guide/cli-reference/dfx-identity.html) `django-server`, with the command:

  ```bash
  dfx identity new django-server

  # The private key is stored in the file:
  # ~/.config/dfx/identity/django-server/identity.pem
  ```

- We used dfx to specify that this identity uses our regular cycles wallet, with the commands:

  ```bash
  # Issue these commands from the dapp-0 repository
  dfx identity --network ic use django-server
  dfx identity --network ic set-wallet aaaaa-aaaaa-aaaaa-aaaaa-aaa  # Replace with your wallet id !

  # Verify it is all ok
  dfx identity --network ic get-wallet

  # Reset identity to default
  dfx identity --network ic use default
  ```

- We base64 encoded the pem file into a single line with the command:

  ```bash
  base64 -w 0 ~/.config/dfx/identity/django-server/identity.pem
  ```

- We pass this value into our Django application via the environment variable `IC_IDENTITY_PEM_ENCODED`

  - Locally, store it in `src/.env`

    ````bash
    IC_IDENTITY_PEM_ENCODED=...
    ```project

    ````

  - In Github, store it in a secret

  - In Digital ocean, store it as an encrypted environment variable

- We extract it as usual in the file `src/project/settings.py`

- We figured out the principal of this identity by calling the `whoami` method.

  - We updated the value for `_django_server_principal` in the smart contract of the  `dapp-0` repository:

    ```javascript
    # file: dapp-0/src/backend/motoko/auth.mo
  
    public func is_django_server(p: Principal) : Result.Result<(), Http.StatusCode> {
        ...
        let _django_server_principal : Principal = Principal.fromText("xxxx-xxxx-...");
    	...
    };
    ```

- Now we can use use [ic-py](https://github.com/rocklabs-io/ic-py) to make authenticated calls from the django python code to the protected APIs of the smart contract that is running in the motoko_canister on the Internet Computer.

## Conda

[Download MiniConda](https://docs.conda.io/en/latest/miniconda.html#linux-installers) and then install it:

```bash
bash Miniconda3-xxxxx.sh
```

Create a conda environment with NodeJS & Python:

```bash
conda create --name dapp-0-django python=3.9
conda activate dapp-0-django

# Install the python packages
make install-python-dev
```



# Development



## Start PostgreSQL cluster

```bash
# Start
make docker-services-up

# View logs
make docker-services-logs

# Stop
make docker-services-down
```

## Create database

#### Option 1: with Makefile

This option uses psql of docker-service under the hood.

```bash
make docker-services-up
make docker-services-db-create
```

#### Option 2: with [pgAdmin4](https://www.pgadmin.org/docs/pgadmin4/5.3/index.html).

- Register the PostgreSQL cluster as a new server, with values as defined in `docker-services/.env-db`

- Create a new database with name `django-server`

## Configure Django

### Create`.env`

Create the environment file, `dapp-0-django/src/.env`, by copying `dapp-0-django/src/.env-template`.

It looks like this:

```bash
########################################################################################
# NOTE:
#
# You can use this command to create the SECRET_KEY & SECRET_JWT_KEY:
#  $ openssl rand -base64 32
#
# If doing it manually, avoid these symbols in the key, because they cause trouble 
# when setting it as environment variable in GitHub, Cloud or as Makefile variables
# (-) #
# (-) &
# (-) $
# (-) !
#
########################################################################################

DIGITALOCEAN_ACCESS_TOKEN=dop_v1_73a111adcd295e686dfff52694e2d528208302ec0615c6a3d2b381ed32537511

DATABASE_URL=postgres://postgres:postgres@localhost:5433/django-server
DATABASE_SSL=False

# local
SECRET_KEY="django-insecure-6qv7k*ip96oif8e!db#^bvfgl9dos6&hu4p+7$mvh9rza*036i"
DEBUG=True
DEBUG_TEMPLATES=True
USE_SSL=False

ALLOWED_HOSTS='[
    "localhost",
    "127.0.0.1",
    "0.0.0.0"
]'

CORS_ALLOWED_ORIGINS='[
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://0.0.0.0:8080"
]'

JWT_METHOD="HS256"

# local
SECRET_JWT_KEY="..."
IC_NETWORK_URL="http://localhost:8000"
CANISTER_MOTOKO_ID="..."

# production (IC Canisters or DigitalOcean Apps)
#SECRET_JWT_KEY="..."
#IC_NETWORK_URL="https://ic0.app"
#CANISTER_MOTOKO_ID="..."

# See README section `django-server` identity
IC_IDENTITY_PEM_ENCODED=...

```

## Migration

We trigger a migration to create our database tables:

```bash
python src/manage.py makemigrations
python src/manage.py migrate
```



## Start the Django server

Use one of the following options:

### Django's runserver from command line

```bash
 make run-with-runserver
```

### Production mode

To run with [uvicorn behind gunicorn](https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/uvicorn/), as we do in production:

```bash
make run-with-gunicorn-local
```

### Wing IDE

With django's runserver:

- Set `src/manage.py` as the main entry point

- Click on run, edit the launch configuration, and set the environment to use port 8001, because dfx local network already uses port 8000

  ```bash
  Run Arguments: runserver 0.0.0.0:8001
  ```

With uvicorn webserver:

- To debug in Wing Pro, make `src/run_uvicorn.py` the **main entry point** (Right Click > ...), and debug as usual

  - Verify the `Debug/Execute` tab in `Project Properties` from the `Project` menu:

    - Main Entry Point: `full path to run_uvicorn.py`

    - Debug Child Processes: `Always Debug Child Processes`

    \*(without this, Wing Pro will not stop at breakpoints)

### Note:

We run the django-server on port 8001, because port 8000 is already in use by the local IC network.

When configured to use the IC mainnet for internet identity:

- the url http://0.0.0.0:8001 works.
- the url http://localhost:8001 does NOT work.



## Testing

To test the health end-point of the running Django server:

```bash
make smoketest
```



To verify all static checks, that everything starts up properly and that the health endpoint works:

```bash
make all-test
```

