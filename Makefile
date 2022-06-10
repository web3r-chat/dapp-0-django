SHELL := /bin/bash

GIT_BRANCH_NAME ?= $(shell git branch --show-current)

DJANGO_SERVER_PORT ?= 8001
DJANGO_SERVER_URL ?= http://localhost:$(DJANGO_SERVER_PORT)

.PHONY: all-test
all-test: \
	all-static-check \
	kill-gunicorn-daemon \
	docker-services-down \
	docker-services-up \
	docker-services-db-drop \
	docker-services-db-create \
	run-with-gunicorn-local \
	smoketest \
	docker-services-down \
	kill-gunicorn-daemon

.PHONY: all-down
all-down: \
	kill-gunicorn-daemon \
	docker-compose-down \
	docker-services-down
	
.PHONY: all-static
all-static: \
	python-format python-lint python-type-check
	
.PHONY: all-static-check
all-static-check: \
	python-format-check python-lint python-type-check


#######################################################################	
# Supportive services, like a local postgresql container
.PHONY: docker-clean-all
docker-clean-all:
	docker container stop $(docker container ls -q)
	docker system prune --all
	docker image prune --all
	docker volume prune

.PHONY: docker-services-up
docker-services-up:
	@echo "-------------------------------------------------"
	@echo "Starting docker-services (postgresql)"
	@cd docker-services && \
		docker-compose --env-file .env-db up -d
	@sleep 5
	@echo "--"
	@docker ps -a

.PHONY: docker-services-logs
docker-services-logs:
	@cd docker-services && \
		docker-compose --env-file .env-db logs --follow

.PHONY: docker-services-down
docker-services-down:
	@echo "-------------------------------------------------"
	@echo "Bringing down docker-services (postgresql)"
	@cd docker-services && \
		docker-compose --env-file .env-db down

.PHONY: docker-services-db-create
docker-services-db-create:
	@echo "--"
	@echo "Create the django-server database"
	@docker exec -i docker-services_django-server-db_1 psql \
		--host=localhost --port=5432 --username=postgres --dbname=postgres --command \
		"CREATE DATABASE \"django-server\" \
			WITH \
			OWNER = postgres \
			ENCODING = 'UTF8' \
			LC_COLLATE = 'en_US.utf8' \
			LC_CTYPE = 'en_US.utf8' \
			TABLESPACE = pg_default \
			CONNECTION LIMIT = -1;"
			
.PHONY: docker-services-db-drop
docker-services-db-drop:
	@echo "--"
	@echo "Drop the django-server database"
	@docker exec -i docker-services_django-server-db_1 psql \
		--host=localhost --port=5432 --username=postgres --dbname=postgres --command \
		"DROP DATABASE IF EXISTS \"django-server\";"
		
.PHONY: docker-ps
docker-ps:
	@docker ps -a

#######################################################################	
.PHONY: doctl-auth-init
doctl-auth-init:
	./scripts/doctl_auth_init.sh

.PHONY: doctl-create-deployment
doctl-create-deployment:
	@$(eval ID_BOT ?= $(shell doctl apps list --output json | jp "[?spec.name=='dapp-0-django-$(GIT_BRANCH_NAME)'].id" | jp [0]))
	
	@echo "-------------------------------------------------"
	@echo "Create deployment for dapp-0-django-$(GIT_BRANCH_NAME)..."
	doctl apps create-deployment $(ID_BOT) --wait --verbose

.PHONY: doctl-logs-dapp-0-django-main
doctl-logs-dapp-0-django-main:
	@$(eval ID ?= $(shell doctl apps list --output json | jp "[?spec.name=='dapp-0-django-main'].id" | jp [0]))
	doctl apps logs $(ID) --follow

.PHONY: doctl-logs-dapp-0-django-branch
doctl-logs-dapp-0-django-branch:
	@$(eval ID ?= $(shell doctl apps list --output json | jp "[?spec.name=='dapp-0-django-$(GIT_BRANCH_NAME)'].id" | jp [0]))
	doctl apps logs $(ID) --follow

.PHONY: install-doctl
install-doctl:
	sudo snap install doctl
	sudo snap connect doctl:dot-docker
	
.PHONY: install-jp
install-jp:
	sudo apt-get update && sudo apt-get install jp
	
.PHONY: install-python-dev
install-python-dev:
	pip install --upgrade pip
	pip install -r requirements-dev.txt

.PHONY: install-python-prod
install-python-prod:
	pip install --upgrade pip
	pip install -r requirements.txt

PYTHON_DIRS ?= scripts src 

.PHONY: python-format
python-format:
	@echo "---"
	@echo "python-format"
	python -m black $(PYTHON_DIRS)

.PHONY: python-format-check
python-format-check:
	@echo "---"
	@echo "python-format-check"
	python -m black --check $(PYTHON_DIRS)

.PHONY: python-lint
python-lint:
	@echo "---"
	@echo "python-lint"
	python -m pylint --jobs=1 --rcfile=.pylintrc --load-plugins pylint_django --django-settings-module=project.settings $(PYTHON_DIRS)

.PHONY: python-type-check
python-type-check:
	@echo "---"
	@echo "python-type-check"
	python -m mypy --config-file .mypy.ini --show-column-numbers --strict $(PYTHON_DIRS)


#######################################################################
.PHONY: smoketest
smoketest:
	@export DJANGO_SERVER_URL=$(DJANGO_SERVER_URL) ; \
	python -m scripts.smoketest

#######################################################################
.PHONY: django-security-check
django-security-check:
	python src/manage.py check --deploy --fail-level WARNING
	

.PHONY: collectstatic
collectstatic:
	python src/manage.py collectstatic --clear --noinput
	
.PHONY: migrate
migrate:
	python src/manage.py migrate
	
#######################################################################
# During Digital Ocean build steps:
# - Check that the deployment is secure
#
# During Digital Ocean Deploy steps:
# - Always automatically run the database migrations
# - Start it up with gunicorn & avicorn workers
#
# - Collectstatic (is done automatic for static items...)

##########################
# This runs post-build !
.PHONY: digital-ocean-dapp-0-django-main-build
digital-ocean-dapp-0-django-main-build: django-security-check

# This runs the server
.PHONY: digital-ocean-dapp-0-django-main-run
digital-ocean-dapp-0-django-main-run: migrate run-with-gunicorn-digital-ocean

##########################
# static site 
# NOT USING THIS 
# (-) I stripped the static_site of the digital-ocean yaml
# (-) The static files are served by django server itself, using Whitenoise
#
#.PHONY: digital-ocean-dapp-0-django-main-static-build
#digital-ocean-dapp-0-django-main-static-build: collectstatic


######################################################################
#
# https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/uvicorn/
# https://www.uvicorn.org/#running-with-gunicorn
.PHONY: run-with-gunicorn-digital-ocean
run-with-gunicorn-digital-ocean:
	cd src && \
		gunicorn \
		--worker-tmp-dir /dev/shm \
		--workers 4 \
		--worker-class uvicorn.workers.UvicornWorker \
		project.asgi:application 		

# Runs the default django development server
.PHONY: run-with-runserver
run-with-runserver:
	@$(MAKE) --no-print-directory kill-gunicorn-daemon
	python src/manage.py runserver $(DJANGO_SERVER_PORT)
		
# This mimics closely how it is run in production on Digital Ocean
.PHONY: run-with-gunicorn-local
run-with-gunicorn-local:
	@echo "---"
	@echo "Collecting static files"
	@$(MAKE) --no-print-directory collectstatic
	@echo "---"
	@echo "Applying migrations"
	@$(MAKE) --no-print-directory migrate
	@echo "---"
	@echo "Running dapp-0-django with gunicorn daemon"
	@cd src && \
		gunicorn --bind localhost:$(DJANGO_SERVER_PORT) \
		--worker-tmp-dir /dev/shm \
		--workers 4 \
		--worker-class uvicorn.workers.UvicornWorker \
		project.asgi:application 	\
		--daemon
	@sleep 2
	@pgrep --list-name gunicorn
	@echo "To kill gunicorn server, use:"
	@echo " make kill-gunicorn-daemon"
	@echo " "
		
.PHONY: kill-gunicorn-daemon
kill-gunicorn-daemon:
	@echo "---"
	@echo "killing all gunicorn daemons"
	@if pgrep gunicorn; then pkill gunicorn; fi


#######################################################################
.PHONY: versions
versions:
	@echo "pip    version  : $(shell pip --version)"
	@echo "python version  : $(shell python --version)"
	@echo "black  version  : $(shell black --version)"
	@echo "pylint version  : $(shell pylint --version)"
	@echo "mypy   version  : $(shell mypy --version)"
	@echo "Ensure conda works properly"
	@conda info
	@which pip
	@which python
