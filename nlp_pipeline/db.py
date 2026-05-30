from contextlib import contextmanager

from celery.utils.log import get_task_logger
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nlp_pipeline.constants import GCPPOSTGRES
from nlp_pipeline.settings import POSTGRES_DATABASE_PASSWORD, SQLALCHEMY_DATABASE_URL, ENV

logger = get_task_logger(__name__)

config = getattr(GCPPOSTGRES, ENV.name).value
connection_string = config["connection_string"]
database = config["db"]


def getconn():
    try:
        connector = Connector()
        conn = connector.connect(
            connection_string,
            "pg8000",
            user="postgres",
            password=POSTGRES_DATABASE_PASSWORD,
            db=database,
        )
        return conn
    except Exception as e:
        if "403" in str(e) or "NOT_AUTHORIZED" in str(e):
            logger.error(
                f"GCP Cloud SQL authorization failed. Ensure the service account has "
                f"'cloudsql.instances.get' and 'cloudsql.instances.connect' permissions "
                f"on resource: {connection_string}. Error: {e}"
            )
        raise


try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, creator=getconn)
    Session = sessionmaker(bind=engine)
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


with session_scope() as session:
    try:
        if POSTGRES_DATABASE_PASSWORD:
            connection = session.connection()
            logger.info("Successfully connected to db.")
        else:
            logger.warning("No password for db provided, skipping connection check.")
    except Exception as e:
        if "403" in str(e) or "NOT_AUTHORIZED" in str(e):
            logger.warning(
                f"Failed to connect to db: missing Cloud SQL permissions. "
                f"Grant 'cloudsql.instances.get' and 'cloudsql.instances.connect' "
                f"to your service account on instance: {connection_string}. "
                f"Original error: {e}"
            )
        else:
            logger.warning(f"Failed to connect to db: {e}")
