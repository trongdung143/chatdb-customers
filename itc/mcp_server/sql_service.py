import asyncio

import pandas as pd
from sqlalchemy import text

_CONN_ERROR_CODES = {"08S01", "08001", "08003", "08007", "HYT00"}
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0


def _is_connection_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(code in msg for code in _CONN_ERROR_CODES)


class SQLService:
    def __init__(self, database):
        self.database = database

    async def execute(self, sql: str, params: dict | None = None) -> dict | bool:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                async with self.database.get_session() as session:
                    result = await session.execute(text(sql), params or {})

                    if result.returns_rows:
                        rows = result.fetchall()
                        df = pd.DataFrame(rows, columns=result.keys())
                        return df.to_dict(orient="records")

                    await session.commit()
                    return {"success": True, "rowcount": result.rowcount}

            except Exception as e:
                last_exc = e
                if _is_connection_error(e) and attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_DELAY * (attempt + 1))
                    continue
                return {"success": False, "error": str(e), "rowcount": 0}

        return {"success": False, "error": str(last_exc), "rowcount": 0}
