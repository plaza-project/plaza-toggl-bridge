import os
import sqlite3
from xdg import XDG_DATA_HOME

DB_PATH_ENV = 'PLAZA_TOGGL_BRIDGE_DB_PATH'
if os.getenv(DB_PATH_ENV, None) is None:
    DATA_DIRECTORY = os.path.join(XDG_DATA_HOME, "plaza", "bridges", "toggl")
    DEFAULT_PATH = os.path.join(DATA_DIRECTORY, 'db.sqlite3')
else:
    DEFAULT_PATH = os.getenv(DB_PATH_ENV)
    DATA_DIRECTORY = os.path.dirname(DEFAULT_PATH)


class DBContext:
    def __init__(self, db, close_on_exit=True):
        self.db = db
        self.close_on_exit = close_on_exit

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, tb):
        if self.close_on_exit:
            self.db.close()


class SqliteStorage:
    def __init__(self, path, multithread=True):
        self.path = path
        self.db = None
        self.multithread = multithread
        self._create_db_if_not_exists()

    def _open_db(self):
        if not self.multithread:
            if self.db is None:
                self.db = sqlite3.connect(self.path)
                self.db.execute("PRAGMA foreign_keys = ON;")
            db = self.db
        else:
            db = sqlite3.connect(self.path)
            db.execute("PRAGMA foreign_keys = ON;")

        return DBContext(db, close_on_exit=not self.multithread)

    def _create_db_if_not_exists(self):
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        with self._open_db() as db:
            c = db.cursor()
            c.execute(
                """
            CREATE TABLE IF NOT EXISTS TOGGL_USER_REGISTRATION (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                toggl_token VARCHAR(256) UNIQUE,
                toggl_user_id VARCHAR(256),
                toggl_user_name VARCHAR(256)
            );
            """
            )

            c.execute(
                """
            CREATE TABLE IF NOT EXISTS PLAZA_USERS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plaza_user_id VARCHAR(36) UNIQUE
            );
            """
            )

            c.execute(
                """
            CREATE TABLE IF NOT EXISTS PLAZA_USERS_IN_TOGGL (
                plaza_id INTEGER,
                toggl_id INTEGER,
                UNIQUE(plaza_id, toggl_id),
                FOREIGN KEY(plaza_id) REFERENCES PLAZA_USERS(id),
                FOREIGN KEY(toggl_id) REFERENCES TOGGL_USER_REGISTRATION(id)
            );
            """
            )
            db.commit()
            c.close()

    def is_toggl_user_registered(self, user_id):
        with self._open_db() as db:
            c = db.cursor()
            c.execute(
                """
            SELECT count(1)
            FROM TOGGL_USER_REGISTRATION
            WHERE toggl_user_id=?
            ;
            """,
                (user_id,),
            )
            result = c.fetchone()[0]

            c.close()

            return result > 0

    def get_plaza_user_from_toggl(self, user_id):
        ## Warning: Untested!
        with self._open_db() as db:
            c = db.cursor()
            c.execute(
                """
            SELECT plaza_user_id
            FROM PLAZA_USERS as p
            JOIN PLAZA_USERS_IN_TOGGL as plaza_in_toggl
            ON plaza_in_toggl.plaza_id = p.id
            JOIN TOGGL_USER_REGISTRATION as m
            ON plaza_in_toggl.toggl_id = m.id
            WHERE m.toggl_user_id=?
            ;
            """,
                (user_id,),
            )
            results = c.fetchall()

            c.close()
            assert 0 <= len(results) <= 1
            if len(results) == 0:
                raise Exception("User (toggl:{}) not found".format(user_id))
            return results[0][0]

    def _get_or_add_toggl_user(self, cursor, toggl_user):

        user_id = toggl_user["user_id"]
        token = toggl_user["token"]
        username = toggl_user["username"]

        cursor.execute(
            """
        SELECT id
        FROM TOGGL_USER_REGISTRATION
        WHERE toggl_token=?
        ;
        """,
            (token,),
        )

        results = cursor.fetchall()
        if len(results) == 0:  # New user
            cursor.execute(
                """
            INSERT INTO TOGGL_USER_REGISTRATION (
                toggl_token,
                toggl_user_id,
                toggl_user_name
            ) VALUES(?, ?, ?);
            """,
                (token, user_id, username),
            )
            return cursor.lastrowid
        elif len(results) == 1:  # Existing user
            return results[0][0]
        else:  # This shouldn't happen
            raise Exception(
                "Integrity error, query by UNIQUE returned multiple values: {}".format(
                    cursor.rowcount
                )
            )

    def _get_or_add_plaza_user(self, cursor, plaza_user):
        cursor.execute(
            """
        SELECT id
        FROM PLAZA_USERS
        WHERE plaza_user_id=?
        ;
        """,
            (plaza_user,),
        )

        results = cursor.fetchall()
        if len(results) == 0:  # New user
            cursor.execute(
                """
            INSERT INTO PLAZA_USERS (plaza_user_id) VALUES(?);
            """,
                (plaza_user,),
            )
            return cursor.lastrowid
        elif len(results) == 1:  # Existing user
            return results[0][0]
        else:  # This shouldn't happen
            raise Exception(
                "Integrity error, query by UNIQUE returned multiple values: {}".format(
                    cursor.rowcount
                )
            )

    def register_user(self, toggl_user, plaza_user):
        with self._open_db() as db:
            c = db.cursor()
            toggl_id = self._get_or_add_toggl_user(c, toggl_user)
            plaza_id = self._get_or_add_plaza_user(c, plaza_user)
            c.execute(
                """
                INSERT OR REPLACE INTO
                PLAZA_USERS_IN_TOGGL (plaza_id, toggl_id)
                VALUES (?, ?)
                """,
                (plaza_id, toggl_id),
            )
            c.close()
            db.commit()

    def get_toggl_users_from_plaza_id(self, plaza_user):
        with self._open_db() as db:
            c = db.cursor()
            plaza_id = self._get_or_add_plaza_user(c, plaza_user)
            c.execute(
                """
            SELECT toggl_u.toggl_user_id,
                   toggl_u.toggl_token,
                   toggl_u.toggl_user_name
            FROM TOGGL_USER_REGISTRATION toggl_u
            JOIN PLAZA_USERS_IN_TOGGL plaza_in_toggl
            ON toggl_u.id=plaza_in_toggl.toggl_id
            WHERE plaza_in_toggl.plaza_id=?
            ;
            """,
                (plaza_id,),
            )
            results = c.fetchall()
            c.close()
            return [
                dict(zip(["user_id", "token", "user_name"], row))
                for row in results
            ]

    def get_toggl_user_from_id(self, toggl_user_id):
        with self._open_db() as db:
            c = db.cursor()
            c.execute(
                """
            SELECT toggl_user_id,
                   toggl_token,
                   toggl_user_name
            FROM TOGGL_USER_REGISTRATION
            WHERE toggl_user_id=?
            ;
            """,
                (toggl_user_id,),
            )
            results = c.fetchall()
            c.close()
            return dict(zip(["user_id", "token", "user_name"], results[0]))


def get_default():
    return SqliteStorage(DEFAULT_PATH)
