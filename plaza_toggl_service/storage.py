import re
import os
from xdg import XDG_DATA_HOME

import sqlalchemy

from . import models

DB_PATH_ENV = 'PLAZA_TOGGL_BRIDGE_DB_PATH'

if os.getenv(DB_PATH_ENV, None) is None:
    _DATA_DIRECTORY = os.path.join(XDG_DATA_HOME, "plaza", "bridges", "toggl")
    CONNECTION_STRING = "sqlite:///{}".format(os.path.join(_DATA_DIRECTORY, 'db.sqlite3'))
else:
    CONNECTION_STRING = os.getenv(DB_PATH_ENV)


class EngineContext:
    def __init__(self, engine):
        self.engine = engine
        self.connection = None

    def __enter__(self):
        self.connection = self.engine.connect()
        return self.connection

    def __exit__(self, exc_type, exc_value, tb):
        self.connection.close()

class StorageEngine:
    def __init__(self, engine):
        self.engine = engine

    def _connect_db(self):
        return EngineContext(self.engine)

    def _get_or_add_toggl_user(self, conn, toggl_user):
        user_id = toggl_user["user_id"]
        token = toggl_user["token"]
        username = toggl_user["username"]

        check = conn.execute(
            sqlalchemy.select([models.TogglUserRegistration.c.id])
            .where(models.TogglUserRegistration.c.toggl_token == token)
        ).fetchone()

        if check is not None:
            return check.id

        insert = models.TogglUserRegistration.insert().values(toggl_token=token,
                                                              toggl_user_id=user_id,
                                                              toggl_user_name=username)
        result = conn.execute(insert)
        return result.inserted_primary_key[0]


    def _get_or_add_plaza_user(self, conn, plaza_user):
        check = conn.execute(
            sqlalchemy.select([models.PlazaUsers.c.id])
            .where(models.PlazaUsers.c.plaza_user_id == plaza_user)
        ).fetchone()

        if check is not None:
            return check.id

        insert = models.PlazaUsers.insert().values(plaza_user_id=plaza_user)
        result = conn.execute(insert)
        return result.inserted_primary_key[0]

    def register_user(self, toggl_user, plaza_user):
        with self._connect_db() as conn:
            toggl_id = self._get_or_add_toggl_user(conn, toggl_user)
            plaza_id = self._get_or_add_plaza_user(conn, plaza_user)

            check = conn.execute(
                sqlalchemy.select([models.PlazaUsersInToggl.c.plaza_id])
                .where(
                    sqlalchemy.and_(
                        models.PlazaUsersInToggl.c.plaza_id == plaza_id,
                        models.PlazaUsersInToggl.c.toggl_id == toggl_id))
            ).fetchone()

            if check is not None:
                return

            insert = models.PlazaUsersInToggl.insert().values(plaza_id=plaza_id,
                                                              toggl_id=toggl_id)
            conn.execute(insert)

    def get_toggl_users_from_plaza_id(self, plaza_user):
        with self._connect_db() as conn:
            plaza_id = self._get_or_add_plaza_user(conn, plaza_user)

            join = sqlalchemy.join(models.TogglUserRegistration, models.PlazaUsersInToggl,
                                   models.TogglUserRegistration.c.id
                                   == models.PlazaUsersInToggl.c.toggl_id)
            results = conn.execute(
                sqlalchemy.select([
                    models.TogglUserRegistration.c.toggl_user_id,
                    models.TogglUserRegistration.c.toggl_token,
                    models.TogglUserRegistration.c.toggl_user_name,
                ])
                .select_from(join)
                .where(models.PlazaUsersInToggl.c.plaza_id == plaza_id)
            ).fetchall()
            return [
                dict(zip(["user_id", "token", "user_name"], row))
                for row in results
            ]

    def get_toggl_user_from_id(self, toggl_user_id):
        with self._connect_db() as conn:
            result = conn.execute(
                sqlalchemy.select([
                    models.TogglUserRegistration.c.toggl_user_id,
                    models.TogglUserRegistration.c.toggl_token,
                    models.TogglUserRegistration.c.toggl_user_name,
                ])
                .where(models.TogglUserRegistration.c.toggl_user_id == toggl_user_id)
            ).fetchone()
            return dict(zip(["user_id", "token", "user_name"], result))



def get_engine():
    # Create path to SQLite file, if its needed.
    if CONNECTION_STRING.startswith('sqlite'):
        db_file = re.sub("sqlite.*:///", "", CONNECTION_STRING)
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

    engine = sqlalchemy.create_engine(CONNECTION_STRING, echo=True)
    metadata = models.metadata
    metadata.create_all(engine)

    return StorageEngine(engine)
