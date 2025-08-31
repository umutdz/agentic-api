build:
	docker compose build
up:
	docker compose up -d
down:
	docker compose down
stop:
	docker compose stop
restart:
	docker compose restart
pre-check:
	pre-commit uninstall && \
	pre-commit install && \
	pre-commit autoupdate && \
	pre-commit install --hook-type commit-msg -f
test:
	pytest -v
