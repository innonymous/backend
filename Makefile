###--START--############################################################################################################

api:
	gunicorn --config ./src/innonymous/gunicorn.conf.py innonymous.presenters.api.application:application

server:
	docker compose up -d

########################################################################################################################


###--TEST--#############################################################################################################

test:
	pytest --force-testdox --showlocals --cov=innonymous --tb=native ./src/tests/

########################################################################################################################


###--LINT--#############################################################################################################

format:
	black ./src/ && ruff --fix ./src/innonymous/

lint:
	black --check ./src/ && ruff ./src/innonymous && mypy --install-types --non-interactive ./src/innonymous/

########################################################################################################################

###--DOCKER--###########################################################################################################

build:
	docker build -t smthngslv/innonymous-backend:latest .

push:
	docker push smthngslv/innonymous-backend:latest

pull:
	docker pull smthngslv/innonymous-backend:latest

prune:
	docker system prune -f

########################################################################################################################
