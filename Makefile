# Optional Environment Parameters:
#	CONFIG: additional config to pass in
#		Applies to `start`, `shell`, `run`, etc.
#	CMD: Django command to run
#		Applies to `run`.
#	INSTALL_DIR: path to the local install/virtualenv folder.
#		Default: installed
#		Applies to all targets.
#	TEST: path to a test folder, file, or module.
#		Applies to `test`, `unit`, `integration`.
#		Should be given in PyTest notation, see https://pytest.org/latest/usage.html#specifying-tests-selecting-tests
#		Example usage: TEST=test_views.py make test
#					   TEST=test_views.py::ExampleTestCase make test
#					   TEST=test_views.py::ExampleTestCase::specifc_test make test
#					   TEST=permissions/test_plaid_item.py make test
#   PACKAGE: desired python package to install
# 	    Applies to 'install_package'
# 		EXAMPLE: PACKAGE=flake8 make install_package

# INSTALL_DIR  ?= $(shell git rev-parse --show-toplevel)/installed
SOURCE_DIRS  := collab collab_app tests

_FULL_CONFIG := $(CONFIG)

# pretty print
define header
	@tput setaf 6
	@echo "* $1"
	@tput sgr0
endef

# Build/install the app
install:
	$(call header,"Installing")
	poetry install

# run all containers, including django server
up:
	$(call header,"Starting every service")
	docker-compose up

# run deps (like db, redis, etc..)
deps-up:
	$(call header,"Starting deps")
	docker-compose up db redis collab_backend_worker

# run db only
db-up:
	$(call header,"Starting db")
	docker-compose up db

# Start the development server
start:
	$(call header,"Starting development server")
	docker-compose run --rm --service-ports collab_backend_web python manage.py runserver 0.0.0.0:8000

# Start the development ssl server
start_ssl:
	$(call header,"Starting development ssl server")
	docker-compose run --rm --service-ports collab_backend_web python manage.py runsslserver 0.0.0.0:8000

# Start the Django shell
shell:
	$(call header,"Starting shell")
	docker-compose run --rm collab_backend_web python manage.py shell_plus --ipython

# Start the Django dbshell
dbshell:
	$(call header,"Starting dbshell")
	docker-compose run --rm collab_backend_web python manage.py dbshell

# Run any Django command
run:
	$(call header,"Running command: $(CMD)")
	docker-compose run --rm collab_backend_web python manage.py $(CMD)

# Migrate database
migrate:
	$(call header,"Running migrate")
	docker-compose run --rm collab_backend_web python manage.py migrate

# Create new migrations
migrations:
	$(call header,"Running makemigrations")
	docker-compose run --rm collab_backend_web python manage.py makemigrations

# Create new data migration
datamigration:
	$(call header,"Running data-migration")
	docker-compose run --rm collab_backend_web python manage.py makemigrations --empty collab_app

# Run unit tests (all or by file)
test: unit
unit: unit_test
unit_test: lint unit_nolint
unit_nolint:
	$(call header,"Running unit tests")
	docker-compose run --rm collab_backend_web pytest --ds=tests.settings -s tests/$(TEST)

test-no-sugar: unit-no-sugar
unit-no-sugar: unit-test-no-sugar
unit-test-no-sugar: lint unit-no-sugar-nolint
unit-no-sugar-nolint:
	$(call header,"Running unit tests")
	docker-compose run --rm collab_backend_web python manage.py test --settings=tests.settings

# Removes build files in working directory
clean_working_directory:
	$(call header,"Cleaning working directory")
	@rm -rf ./build ./dist ./collab-backend.egg-info
	@find . -type f -name '*.pyc' -exec rm -rf {} \;

# Full clean
clean: clean_working_directory
	$(call header,"Cleaning all")

# Lint the whole project
lint: clean_working_directory
	$(call header,"Linting code")
	docker-compose run --rm collab_backend_web flake8

# show the path to the virtualenv created by poetry
show-virtualenv-path:
	poetry show -v 2> /dev/null | head -1

# get env vars for staging environment (using heroku)
pull-staging-env-vars:
	$(call header,"Saving env vars to .env.staging")
	heroku config -s -a api-staging-collabsauce > .env.staging
	echo 'SENTRY_RELEASE=$(shell git rev-parse --short HEAD)' >> .env.staging

# get env vars for staging environment (using heroku)
pull-production-env-vars:
	$(call header,"Saving env vars to .env.production")
	heroku config -s -a api-production-collabsauce > .env.production
	echo 'SENTRY_RELEASE=$(shell git rev-parse --short HEAD)' >> .env.production

# rebuild the collab_backend_web container
rebuild-collab-backend-web:
	docker-compose -f ${YML_FILE} build collab_backend_web

# rebuild the collab_backend_worker container
rebuild-collab-backend-worker:
	docker-compose -f ${YML_FILE} build collab_backend_worker

rebuild-image: rebuild-collab-backend-web rebuild-collab-backend-worker

# rebuild the web and worker image
rebuild: YML_FILE=docker-compose.yml
rebuild: rebuild-image

# rebuild the web and worker image for staging
rebuild-staging: YML_FILE=docker-compose.staging.yml
rebuild-staging: pull-staging-env-vars
rebuild-staging: rebuild-image

run-staging-web:
	docker-compose -f docker-compose.staging.yml up -d collab_backend_web

run-staging-worker:
	docker-compose -f docker-compose.staging.yml up -d collab_backend_worker

# rebuild the web and worker image for production
rebuild-production: YML_FILE=docker-compose.production.yml
rebuild-production: pull-production-env-vars
rebuild-production: rebuild-image

run-production-web:
	docker-compose -f docker-compose.production.yml up -d collab_backend_web

run-production-worker:
	docker-compose -f docker-compose.production.yml up -d collab_backend_worker
