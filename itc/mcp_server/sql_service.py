import pandas as pd
from sqlalchemy import text


class SQLService:
    def __init__(self, database):
        self.database = database

    async def execute(self, sql: str) -> dict | bool:
        self._validate_query(sql)

        try:
            async with self.database.get_session() as session:
                result = await session.execute(text(sql))

                if result.returns_rows:
                    rows = result.fetchall()
                    df = pd.DataFrame(rows, columns=result.keys())
                    return df.to_dict(orient="records")
                else:
                    await session.commit()
                    return True

        except Exception as e:
            return False
