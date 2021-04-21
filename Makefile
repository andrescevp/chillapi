VENV_NAME?=venv
VENV_ACTIVATE=. ${VENV_NAME}/bin/activate
PYTHON=${VENV_NAME}/bin/python
DOCKER=docker exec -ti chillapi-api
NTDOCKER=docker exec -it chillapi-api
CURRENT_GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
DB_REVISION_DESCRIPTION='autogenerated'
DB_URL='postgresql+psycopg2://root:root@postgres/codebook'
ALEMBIC_CONFIG=postgres.alembic.ini
virtualenv:
	${DOCKER} virtualenv venv
run:
	${DOCKER} sh -c "${VENV_ACTIVATE} && gunicorn --bind 0.0.0.0:8000 app:app"
run_dev:
	${DOCKER} sh -c "${VENV_ACTIVATE} && python -m app"
test_settime:
	${DOCKER} sh -c "${VENV_ACTIVATE} && python -m unittest tests.settime.api tests.settime.app.config"
test_runtime:
	${DOCKER} sh -c "${VENV_ACTIVATE} && python -m unittest tests.runtime.api_test"
profile_graph:
	${DOCKER} sh -c "${VENV_ACTIVATE} && gprof2dot -f pstats $(FILE) | dot -Tpng -o $(FILE).png"
pip_install:
	${DOCKER} sh -c "${VENV_ACTIVATE} && pip install ${LIBS}"
pip_uninstall:
	${DOCKER} sh -c "${VENV_ACTIVATE} && pip uninstall ${LIBS}"
pip_install_requirements:
	${DOCKER} sh -c "${VENV_ACTIVATE} && pip install -r requirements.txt"
pip_freeze_requirements:
	${DOCKER} sh -c "${VENV_ACTIVATE} && pip freeze > requirements.txt && chown -Rf 1000:1000 requirements.txt"
docker_exec_n:
	${NTDOCKER} ${CMD}
docker_pyexec:
	${DOCKER} sh -c "${VENV_ACTIVATE} && $(CMD)"
docker_exec:
	${DOCKER} ${CMD}
docker_fix_permissions:
	${DOCKER} chown -Rf 1000:1000 .
db_schema_upgrade:
	${DOCKER} sh -c "${VENV_ACTIVATE} && alembic -c $(ALEMBIC_CONFIG) upgrade head && chown -Rf 1000:1000 ."
db_schema_downgrade:
	${DOCKER} sh -c "${VENV_ACTIVATE} && alembic -c $(ALEMBIC_CONFIG) downgrade $(OPTS)"
db_schema_downgrade_last:
	${DOCKER} sh -c "${VENV_ACTIVATE} && alembic -c $(ALEMBIC_CONFIG) downgrade -1"
db_schema_new_revision:
	${DOCKER} sh -c "${VENV_ACTIVATE} && alembic -c $(ALEMBIC_CONFIG) revision -m '${CURRENT_GIT_BRANCH}/${DB_REVISION_DESCRIPTION}' && chown -Rf 1000:1000 ."
db_schema_docs:
	${DOCKER} sh -c "${VENV_ACTIVATE} && eralchemy -i ${DB_URL} -o db_schema_migrations/schema.jpg  && chown -Rf 1000:1000 ."
api_definition_validate:
	${DOCKER} sh -c "${VENV_ACTIVATE} && pykwalify -d api.yaml -s api.schema.yaml  && chown -Rf 1000:1000 ."
