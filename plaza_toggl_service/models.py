from sqlalchemy import Column, Integer, String, MetaData, Column, ForeignKey, UniqueConstraint, Table

metadata = MetaData()

TogglUserRegistration = Table(
    'TOGGL_USER_REGISTRATION', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('toggl_token', String(256), unique=True),
    Column('toggl_user_id', String(256)),
    Column('toggl_user_name', String(256)))

PlazaUsers = Table(
    'PLAZA_USERS', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('plaza_user_id', String(36), unique=True))

PlazaUsersInToggl = Table(
    'PLAZA_USERS_IN_TOGGL', metadata,
    Column('plaza_id', Integer, ForeignKey('PLAZA_USERS.id'), primary_key=True),
    Column('toggl_id', Integer, ForeignKey('TOGGL_USER_REGISTRATION.id'), primary_key=True),
    __table_args__=(UniqueConstraint('plaza_id', 'toggl_id')))
