from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from setup import DB_DRIVER, DB_DATABASE, DB_PWD, DB_SERVER, DB_UID


class Database:
    def __init__(self):
        connection_string = (
            f"DRIVER={DB_DRIVER};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_UID};"
            f"PWD={DB_PWD};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "MultipleActiveResultSets=True;"
        )

        self.engine = create_async_engine(
            f"mssql+aioodbc:///?odbc_connect={connection_string}",
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_pre_ping=True,
        )
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def get_session(self):
        return self.SessionLocal()
