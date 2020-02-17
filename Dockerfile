FROM python:3-alpine

# Note that git is not uninstalled later, as it's needed for the
#  installation of the requirements.
#
# PsycoPG is the driver for PostgreSQL installations
#  (used through SqlAlchemy.)
RUN apk add --no-cache git py3-psycopg2

ADD . /app
RUN pip install -r /app/requirements.docker.txt && pip install -e /app

# Bridge database (for user registrations)
VOLUME /root/.local/share/plaza/bridges/toggl/db.sqlite

CMD plaza-toggl-service
