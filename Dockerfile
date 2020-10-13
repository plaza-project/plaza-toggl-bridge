FROM python:3-alpine

ADD requirements.txt /app/requirements.txt

RUN apk add --no-cache git \
  && pip install -r /app/requirements.txt \
  && apk del git

ADD . /app
RUN pip install -e /app

# Bridge database (for user registrations)
VOLUME /root/.local/share/plaza/bridges/toggl/db.sqlite

CMD programaker-toggl-service
