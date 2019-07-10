FROM python:3-alpine

# Note that git is not uninstalled later, as it's needed for the
#  installation of the requirements.
RUN apk add --no-cache git

ADD . /app
RUN pip install -r /app/requirements.txt && pip install -e /app

# Bridge database (for user registrations)
VOLUME /root/.local/share/plaza/bridges/toggl/db.sqlite

CMD plaza-toggl-service
