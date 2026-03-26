from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
import psycopg2

from utils.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, ENV_FILE


def load_env() -> None:
    if ENV_FILE.exists():
        from dotenv import load_dotenv

        load_dotenv(ENV_FILE)


@contextmanager
def get_connection():
    load_env()
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        yield conn
    finally:
        conn.close()


def query_to_dataframe(query: str) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

