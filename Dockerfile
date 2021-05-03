FROM python:3.8-slim

RUN apt-get update
RUN apt-get install -y libpq-dev build-essential libgraphviz-dev graphviz
RUN apt-get install -y sqlite3 libsqlite3-dev
#RUN apt-get install -y default-libmysqlclient-dev  default-mysql-client

#WORKDIR /tmp
#RUN curl -sL https://deb.nodesource.com/setup_14.x -o nodesource_setup.sh
#RUN bash nodesource_setup.sh
#RUN apt-get install nodejs
#RUN npm install -g contentful-cli

ARG APP_ENV='local'
ENV APP_ENV=${APP_ENV}
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY . /app
WORKDIR /app

RUN mkdir var
RUN touch var/app.log
RUN python -m pip install -U pip
RUN pip install pipreqs
RUN set -ex && \
    pip install -r chillapi/requirements.txt && \
    pip install -r server-requirements.txt

#CMD gunicorn --log-level=debug --bind=0.0.0.0:8000 app:server
