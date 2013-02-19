from contextlib import contextmanager

from sqlalchemy import create_engine


engine = create_engine("sqlite:///terminal.db", echo=True)


@contextmanager
def txn(rw=False):
    connection = engine.connect()
    trans = connection.begin()

    try:
        yield connection

        if rw:
            trans.commit()
        else:
            trans.rollback()
    except:
        trans.rollback()
        raise
