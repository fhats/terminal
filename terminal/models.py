"""Contains definitions of database objects used throughout the application.

Advisories contains service advisories of different types. Each advisory has a
type, which can be 'info', 'warning', or 'alert' depending on the severity of
the advisory. Advisories also have message fields, which can be used to
describe the advisory.

Versions contains the version identifier for each service in each environment
it is running in. Version rows contain the name of the service, the environment
the service is running in, and a version identifier. Note that multiple rows
should exist for each environment a service is running in. For example, if
I have a service 'foo' running in both production and stage, I would have the
following Versions rows:

ID  Name  Env         Version
1   foo   production  12345-master
2   foo   stage       12346-dev

Versions is intended for storage only while the application is running. It
should be emptied on shutdown and startup.
"""
from sqlalchemy import Column, Table
from sqlalchemy import Enum, Integer, String
from sqlalchemy import MetaData


ADVISORY_TYPES = ['info', 'warning', 'alert']

metadata = MetaData()

advisories = Table('advisories', metadata,
    Column('id', Integer, primary_key=True),
    Column('type', Enum(*ADVISORY_TYPES), index=True),
    Column('message', String)
)

versions = Table('versions', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, index=True),
    Column('env', String),
    Column('version', String)
)
