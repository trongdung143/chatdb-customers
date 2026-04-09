import pandas as pd
from sqlalchemy import text
from conn_db import Database


class SQLService:
    def __init__(self, database: Database):
        self.database = database

    def _validate_query(self, sql: str):
        if not sql.strip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

    async def execute(self, sql: str) -> pd.DataFrame | str:
        self._validate_query(sql)

        try:
            async with self.database.get_session() as session:
                result = await session.execute(text(sql))
                rows = result.fetchall()
                df = pd.DataFrame(rows, columns=result.keys())
                return df

        except Exception as e:
            raise RuntimeError(str(e))
