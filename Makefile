.DEFAULT_GOAL := init

.PHONY += init paths checks test clean

init: # Do the initial configuration of the project
	@test -e .env || cp example.env .env
ifeq ($(shell uname),Darwin)
	@sed -i '' 's|^PROJECT_PATH=.*|PROJECT_PATH=$(shell pwd | sed 's/\//\\\//g')|' .env
else
	@sed -i 's/^PROJECT_PATH=.*/PROJECT_PATH=$(shell pwd | sed 's/\//\\\//g')/' .env
endif

.env: init

checks: # Runs all the pre-commit checks
	@pre-commit install
	@pre-commit run --all-files || { echo "Checking fixes\n" ; pre-commit run --all-files; }

test: init .env # Runs all the tests
	@docker compose -f tests/wei.compose.yaml --env-file .env up --build -d
	@docker compose -f tests/wei.compose.yaml --env-file .env exec camera_module pytest -p no:cacheprovider camera_module
	@docker compose -f tests/wei.compose.yaml --env-file .env down

clean:
	@rm .env
