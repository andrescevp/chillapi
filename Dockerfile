FROM python:3.8-slim

ARG DASH_DEBUG_MODE=False
ENV DASH_DEBUG_MODE=$DASH_DEBUG_MODE

RUN apt-get update
RUN apt-get install -y libpq-dev build-essential
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

RUN set -ex && \
    pip install -r requirements.txt

#CMD gunicorn --log-level=debug --bind=0.0.0.0:8000 app:server
