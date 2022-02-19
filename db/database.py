import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def _after_init_db():
    pass

def global_init_sqlite(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Required path to your DB.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Connecting to db by {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine, autoflush=True)

    # from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)

    _after_init_db()


def create_session() -> Session:
    global __factory
    return __factory()
