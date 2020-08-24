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

# run deps (like db and redis)
deps-up:
	$(call header,"Starting deps")
	docker-compose up db redis

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

# rebuild the collab_backend_web container
rebuild-collab-backend-web:
	docker-compose build collab_backend_web