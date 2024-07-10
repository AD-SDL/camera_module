.DEFAULT_GOAL := init

.PHONY += init paths checks test clean

init: # Do the initial configuration of the project
	@test -e .env || cp example.env .env

.env: init

checks: # Runs all the pre-commit checks
	@pre-commit install
	@pre-commit run --all-files || { echo "Checking fixes\n" ; pre-commit run --all-files; }

test: init .env # Runs all the tests
	@docker compose --profile wei up --build -d
	@docker compose --profile wei exec camera_module pytest -p no:cacheprovider camera_module
	@docker compose --profile wei down

clean:
	@rm .env
