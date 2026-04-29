import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, date
import uuid
import re
import sqlparse

BASE_URL = "https://itcshop.vn/"


def dataframe_to_json(df: pd.DataFrame):

    if df is None or df.empty:
        return []

    df = df.copy()

    if df.columns.duplicated().any():
        counts = {}
        new_cols = []

        for col in df.columns:
            if col in counts:
                counts[col] += 1
                new_cols.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                new_cols.append(col)

        df.columns = new_cols

    df = df.astype(object)

    def convert_value(v):

        if v is None:
            return None

        if pd.isna(v):
            return None

        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(v, (datetime, date)):
            return v.isoformat()

        if isinstance(v, Decimal):
            return float(v)

        if isinstance(v, (np.integer,)):
            return int(v)

        if isinstance(v, (np.floating,)):
            return float(v)

        if isinstance(v, uuid.UUID):
            return str(v)

        return v

    df = df.apply(lambda col: col.map(convert_value))

    for col in df.columns:
        if col.lower() in ["cover", "path"]:
            df[col] = df[col].apply(
                lambda v: (
                    BASE_URL + v.lstrip("/")
                    if isinstance(v, str) and v and not v.startswith("http")
                    else v
                )
            )

    return df.to_dict(orient="records")


def sanitize_sql(text: str) -> str:
    try:
        text = re.sub(r"```[\s\S]*?\n", "", text)
        text = text.replace("```", "")

        match = re.search(r"\bSELECT\b[\s\S]*", text, re.IGNORECASE)
        if not match:
            raise ValueError("No SELECT found")

        text = match.group(0)

        statements = sqlparse.parse(text)

        for stmt in statements:
            if stmt.get_type() == "SELECT":
                sql = str(stmt).strip()

                sql = re.sub(r"--.*", "", sql)
                sql = re.sub(r"/\*[\s\S]*?\*/", "", sql)
                sql = re.sub(r"\s+", " ", sql)

                return sql.strip()

        raise ValueError("No valid SELECT statement")

    except Exception as e:
        raise ValueError(f"SQL sanitize error: {str(e)}")
